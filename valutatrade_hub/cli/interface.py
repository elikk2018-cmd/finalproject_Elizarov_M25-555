"""CLI interface (argparse commands).

Command entrypoint is `valutatrade_hub.cli.interface:main`.
It is called from main.py for Poetry script `project`.
"""

from __future__ import annotations

import argparse
import sys
from decimal import Decimal

from prettytable import PrettyTable

from valutatrade_hub.core.exceptions import DomainError
from valutatrade_hub.core.usecases import PortfolioUsecase, RatesUsecase, UsersUsecase
from valutatrade_hub.core.utils import normalize_currency_code, parse_positive_decimal
from valutatrade_hub.logging_config import setup_logging
from valutatrade_hub.parser_service.updater import RatesUpdater


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="project", description="ValutaTrade Hub CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_reg = sub.add_parser("register", help="Register a new user")
    p_reg.add_argument("--username", required=True)
    p_reg.add_argument("--password", required=True)

    p_login = sub.add_parser("login", help="Login")
    p_login.add_argument("--username", required=True)
    p_login.add_argument("--password", required=True)

    p_buy = sub.add_parser("buy", help="Buy currency")
    p_buy.add_argument("--currency", required=True)
    p_buy.add_argument("--amount", required=True)

    p_sell = sub.add_parser("sell", help="Sell currency")
    p_sell.add_argument("--currency", required=True)
    p_sell.add_argument("--amount", required=True)

    p_port = sub.add_parser("show-portfolio", help="Show portfolio")
    p_port.add_argument("--base", default="USD")

    p_rate = sub.add_parser("get-rate", help="Get rate from cache (TTL enforced)")
    p_rate.add_argument("--from", dest="from_code", required=True)
    p_rate.add_argument("--to", dest="to_code", required=True)

    sub.add_parser("update-rates", help="Fetch and update rates cache")
    sub.add_parser("show-rates", help="Show all cached rates")

    return parser


def main(argv: list[str] | None = None) -> None:
    """CLI main."""
    setup_logging()

    parser = _build_parser()
    args = parser.parse_args(argv)

    users = UsersUsecase()
    portfolio_uc = PortfolioUsecase()
    rates_uc = RatesUsecase()

    try:
        match args.command:
            case "register":
                user = users.register(username=args.username, password=args.password)
                print(f"OK: registered user_id={user.user_id}, username={user.username}")

            case "login":
                users.login(username=args.username, password=args.password)
                print("OK: logged in")

            case "buy":
                code = normalize_currency_code(args.currency)
                amt: Decimal = parse_positive_decimal(args.amount)
                result = portfolio_uc.buy(currency_code=code, amount=amt)
                print(
                    f"OK: bought {result['amount']} {result['currency']} "
                    f"(new balance {result['new_balance']})"
                )

            case "sell":
                code = normalize_currency_code(args.currency)
                amt = parse_positive_decimal(args.amount)
                result = portfolio_uc.sell(currency_code=code, amount=amt)
                print(
                    f"OK: sold {result['amount']} {result['currency']} "
                    f"(new balance {result['new_balance']})"
                )

            case "show-portfolio":
                base = normalize_currency_code(args.base)
                portfolio, values, total = portfolio_uc.show_portfolio(base=base)

                t = PrettyTable()
                t.field_names = ["Currency", "Balance", f"Value in {base}"]
                for code, wallet in portfolio.wallets.items():
                    t.add_row([code, float(wallet.balance), round(values.get(code, 0.0), 6)])
                t.add_row(["TOTAL", "", round(total, 6)])
                print(t)

            case "get-rate":
                frm = normalize_currency_code(args.from_code)
                to = normalize_currency_code(args.to_code)
                rate, updated_at = rates_uc.get_rate(frm, to)
                print(f"{frm}->{to} = {rate} (updated_at={updated_at})")

            case "update-rates":
                RatesUpdater().update()
                print("OK: rates updated")

            case "show-rates":
                data = RatesUpdater().read_cache()
                t = PrettyTable()
                t.field_names = ["Pair", "Rate", "Updated at"]
                for key, rec in sorted(data.items()):
                    if key in {"source", "last_refresh"}:
                        continue
                    t.add_row([key, rec.get("rate"), rec.get("updated_at")])
                print(t)
                if "last_refresh" in data:
                    print(f"last_refresh={data['last_refresh']} source={data.get('source')}")

            case _:
                parser.print_help()
                sys.exit(2)

    except DomainError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
