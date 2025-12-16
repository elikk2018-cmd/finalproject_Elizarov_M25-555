"""Usecases: register/login/buy/sell/show-portfolio/get-rate.

Rules:
- CLI does not contain business logic; it calls these usecases.
- Storage is JSON files via DatabaseManager.
- Rates are taken from data/rates.json with TTL.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from valutatrade_hub.core.currencies import get_currency
from valutatrade_hub.core.exceptions import ApiRequestError, AuthenticationError
from valutatrade_hub.core.models import Portfolio, User, Wallet
from valutatrade_hub.core.session import session_manager
from valutatrade_hub.core.utils import normalize_currency_code, parse_positive_decimal
from valutatrade_hub.decorators import log_action, require_auth
from valutatrade_hub.infra.database import db
from valutatrade_hub.infra.settings import settings


class UsersUsecase:
    """User registration and login."""

    @log_action("REGISTER")
    def register(self, username: str, password: str) -> User:
        """Register a new user and create an empty portfolio."""
        users: list[dict[str, Any]] = db.read_list("users")

        if any(u.get("username") == username for u in users):
            raise ValueError(f"Имя пользователя '{username}' уже занято")

        next_id = max((u.get("user_id", 0) for u in users), default=0) + 1
        user = User.create_new(user_id=next_id, username=username, password=password)

        users.append(asdict(user.to_dump()))
        db.write_list("users", users)

        portfolios = db.read_list("portfolios")
        portfolios.append({"user_id": user.user_id, "wallets": {}})
        db.write_list("portfolios", portfolios)

        return user

    @log_action("LOGIN")
    def login(self, username: str, password: str) -> None:
        """Login and set in-memory session."""
        users: list[dict[str, Any]] = db.read_list("users")
        raw = next((u for u in users if u.get("username") == username), None)
        if raw is None:
            raise AuthenticationError(f"Пользователь '{username}' не найден")

        user = User(
            user_id=int(raw["user_id"]),
            username=str(raw["username"]),
            hashed_password=str(raw["hashed_password"]),
            salt=str(raw["salt"]),
            registration_date=datetime.fromisoformat(str(raw["registration_date"])),
        )

        if not user.verify_password(password):
            raise AuthenticationError("Неверный пароль")

        session_manager.login(user_id=user.user_id, username=user.username)


class PortfolioUsecase:
    """Trading and portfolio operations."""

    def _load_portfolio(self, user_id: int) -> Portfolio:
        portfolios = db.read_list("portfolios")
        raw = next((p for p in portfolios if p.get("user_id") == user_id), None)
        if raw is None:
            return Portfolio(user_id=user_id, wallets={})

        wallets: dict[str, Wallet] = {}
        raw_wallets = raw.get("wallets") or {}
        for code, w in raw_wallets.items():
            wallets[code] = Wallet(
                currency_code=code, balance=Decimal(str(w.get("balance", 0)))
            )
        return Portfolio(user_id=user_id, wallets=wallets)

    def _save_portfolio(self, portfolio: Portfolio) -> None:
        portfolios = db.read_list("portfolios")
        for i, p in enumerate(portfolios):
            if p.get("user_id") == portfolio.user_id:
                portfolios[i] = portfolio.to_json_payload()
                db.write_list("portfolios", portfolios)
                return
        portfolios.append(portfolio.to_json_payload())
        db.write_list("portfolios", portfolios)

    @require_auth
    @log_action("BUY", verbose=True)
    def buy(
        self, currency_code: str, amount: Decimal, base: str = "USD"
    ) -> dict[str, Any]:
        """Buy currency: increases wallet balance by amount."""
        code = normalize_currency_code(currency_code)
        base_code = normalize_currency_code(base)

        get_currency(code)
        get_currency(base_code)

        amt = parse_positive_decimal(amount)

        user = session_manager.current_user
        if user is None:
            raise AuthenticationError("Сначала выполните login")

        portfolio = self._load_portfolio(user.user_id)
        wallet = portfolio.get_wallet(code)

        old_balance = wallet.balance
        wallet.deposit(amt)

        rate, updated_at = RatesUsecase().get_rate(code, base_code)
        estimated_cost = float(amt) * rate

        self._save_portfolio(portfolio)

        return {
            "currency": code,
            "amount": float(amt),
            "old_balance": float(old_balance),
            "new_balance": float(wallet.balance),
            "rate": rate,
            "base": base_code,
            "updated_at": updated_at,
            "estimated_cost": estimated_cost,
        }

    @require_auth
    @log_action("SELL", verbose=True)
    def sell(
        self, currency_code: str, amount: Decimal, base: str = "USD"
    ) -> dict[str, Any]:
        """Sell currency: decreases wallet balance by amount (requires funds)."""
        code = normalize_currency_code(currency_code)
        base_code = normalize_currency_code(base)

        get_currency(code)
        get_currency(base_code)

        amt = parse_positive_decimal(amount)

        user = session_manager.current_user
        if user is None:
            raise AuthenticationError("Сначала выполните login")

        portfolio = self._load_portfolio(user.user_id)
        wallet = portfolio.get_wallet(code)

        old_balance = wallet.balance
        wallet.withdraw(amt)

        rate, updated_at = RatesUsecase().get_rate(code, base_code)
        estimated_proceeds = float(amt) * rate

        self._save_portfolio(portfolio)

        return {
            "currency": code,
            "amount": float(amt),
            "old_balance": float(old_balance),
            "new_balance": float(wallet.balance),
            "rate": rate,
            "base": base_code,
            "updated_at": updated_at,
            "estimated_proceeds": estimated_proceeds,
        }

    @require_auth
    def show_portfolio(self, base: str = "USD") -> tuple[Portfolio, dict[str, float], float]:
        """Return portfolio + per-wallet value in base + total."""
        base_code = normalize_currency_code(base)
        get_currency(base_code)

        user = session_manager.current_user
        if user is None:
            raise AuthenticationError("Сначала выполните login")

        portfolio = self._load_portfolio(user.user_id)

        rates = RatesUsecase()
        values: dict[str, float] = {}
        total = 0.0

        for code, wallet in portfolio.wallets.items():
            if code == base_code:
                value = float(wallet.balance)
            else:
                rate, _ = rates.get_rate(code, base_code)
                value = float(wallet.balance) * rate
            values[code] = value
            total += value

        return portfolio, values, total


class RatesUsecase:
    """Rates access with TTL based on settings."""

    def _pair_key(self, from_code: str, to_code: str) -> str:
        return f"{from_code}_{to_code}"

    def _is_fresh(self, last_refresh_iso: str) -> bool:
        ttl = int(settings.get("ratesttlseconds", 300))
        last = datetime.fromisoformat(last_refresh_iso)
        return (datetime.now() - last) <= timedelta(seconds=ttl)

    def get_rate(self, from_code: str, to_code: str) -> tuple[float, str]:
        """Get rate from cache rates.json; fails if missing/expired."""
        frm = normalize_currency_code(from_code)
        to = normalize_currency_code(to_code)

        get_currency(frm)
        get_currency(to)

        data = db.read_obj("rates", default={})

        last_refresh = data.get("last_refresh")
        if not last_refresh:
            raise ApiRequestError("Кеш курсов пуст. Выполните update-rates")

        if not self._is_fresh(str(last_refresh)):
            raise ApiRequestError("Кеш курсов устарел. Выполните update-rates")

        pair = self._pair_key(frm, to)
        rec = data.get(pair)
        if rec is None:
            raise ApiRequestError(f"Курс {frm}→{to} недоступен. Выполните update-rates")

        return float(rec["rate"]), str(rec["updated_at"])
