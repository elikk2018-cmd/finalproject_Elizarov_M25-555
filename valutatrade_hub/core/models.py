"""Domain models: User, Wallet, Portfolio."""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from valutatrade_hub.core.exceptions import InsufficientFundsError
from valutatrade_hub.core.utils import normalize_currency_code, parse_positive_decimal


@dataclass(frozen=True)
class UserDump:
    """Serializable representation of a User (for users.json)."""

    user_id: int
    username: str
    hashed_password: str
    salt: str
    registration_date: str


class User:
    """User entity with private fields and salted SHA-256 password hash."""

    def __init__(
        self,
        user_id: int,
        username: str,
        hashed_password: str,
        salt: str,
        registration_date: datetime,
    ) -> None:
        self._user_id = int(user_id)
        self.username = username
        self._hashed_password = hashed_password
        self._salt = salt
        self._registration_date = registration_date

    @classmethod
    def create_new(cls, user_id: int, username: str, password: str) -> User:
        """Create a new user with generated salt and hashed password."""
        if not password or len(password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов")

        salt = secrets.token_urlsafe(8)
        hashed = cls._hash_password(password=password, salt=salt)

        return cls(
            user_id=user_id,
            username=username,
            hashed_password=hashed,
            salt=salt,
            registration_date=datetime.now(),
        )

    @staticmethod
    def _hash_password(password: str, salt: str) -> str:
        """One-way pseudo-hash: sha256(password + salt)."""
        return hashlib.sha256((password + salt).encode("utf-8")).hexdigest()

    @property
    def user_id(self) -> int:
        """Unique user id."""
        return self._user_id

    @property
    def username(self) -> str:
        """Username."""
        return self._username

    @username.setter
    def username(self, value: str) -> None:
        """Set username with validation."""
        if not value or not value.strip():
            raise ValueError("Имя не может быть пустым")
        self._username = value.strip()

    def get_user_info(self) -> dict[str, Any]:
        """Return user info without password."""
        return {
            "user_id": self._user_id,
            "username": self._username,
            "registration_date": self._registration_date.isoformat(),
        }

    def verify_password(self, password: str) -> bool:
        """Verify password against stored hash."""
        return self._hash_password(password=password, salt=self._salt) == self._hashed_password

    def change_password(self, new_password: str) -> None:
        """Change password and update hash."""
        if not new_password or len(new_password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов")
        self._hashed_password = self._hash_password(password=new_password, salt=self._salt)

    def to_dump(self) -> UserDump:
        """Serialize for JSON storage."""
        return UserDump(
            user_id=self._user_id,
            username=self._username,
            hashed_password=self._hashed_password,
            salt=self._salt,
            registration_date=self._registration_date.isoformat(),
        )


class Wallet:
    """Wallet for a single currency."""

    def __init__(self, currency_code: str, balance: Decimal = Decimal("0")) -> None:
        self.currency_code = normalize_currency_code(currency_code)
        self.balance = balance

    @property
    def balance(self) -> Decimal:
        """Current balance."""
        return self._balance

    @balance.setter
    def balance(self, value: Decimal) -> None:
        """Set balance with validation (no negative)."""
        if not isinstance(value, Decimal):
            raise ValueError("balance должен быть Decimal")
        if value < 0:
            raise ValueError("balance не может быть отрицательным")
        self._balance = value

    def deposit(self, amount: Decimal) -> None:
        """Deposit amount (must be positive)."""
        amt = parse_positive_decimal(amount)
        self._balance += amt

    def withdraw(self, amount: Decimal) -> None:
        """Withdraw amount if enough funds (must be positive)."""
        amt = parse_positive_decimal(amount)
        if self._balance < amt:
            raise InsufficientFundsError(
                code=self.currency_code,
                available=float(self._balance),
                required=float(amt),
            )
        self._balance -= amt

    def get_balance_info(self) -> dict[str, Any]:
        """Return wallet info."""
        return {"currency_code": self.currency_code, "balance": float(self._balance)}


class Portfolio:
    """Portfolio with wallets of a single user."""

    def __init__(self, user_id: int, wallets: dict[str, Wallet] | None = None) -> None:
        self._user_id = int(user_id)
        self._wallets: dict[str, Wallet] = wallets or {}

    @property
    def user_id(self) -> int:
        """User id (read-only)."""
        return self._user_id

    @property
    def wallets(self) -> dict[str, Wallet]:
        """Copy of wallets mapping."""
        return self._wallets.copy()

    def add_currency(self, currency_code: str) -> Wallet:
        """Add wallet for currency if missing and return it."""
        code = normalize_currency_code(currency_code)
        if code not in self._wallets:
            self._wallets[code] = Wallet(code)
        return self._wallets[code]

    def get_wallet(self, currency_code: str) -> Wallet:
        """Get wallet for currency (auto-create if missing)."""
        return self.add_currency(currency_code)

    def to_json_payload(self) -> dict[str, Any]:
        """Serialize portfolio for portfolios.json."""
        return {
            "user_id": self._user_id,
            "wallets": {c: {"balance": float(w.balance)} for c, w in self._wallets.items()},
        }
