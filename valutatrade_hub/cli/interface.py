"""Enhanced CLI interface with new features."""
import argparse
import sys

from prettytable import PrettyTable

from ..core.currencies import CurrencyRegistry, get_currency
from ..core.exceptions import (
    CurrencyNotFoundError,
    InsufficientFundsError,
    ValutaTradeError,
)
from ..core.session import session_manager
from ..core.usecases import portfolio_manager, rate_manager, user_manager
from ..core.utils import ExchangeRates, format_currency_amount


class CLI:
    """Enhanced Command Line Interface for ValutaTrade Hub."""

    def __init__(self):
        self.parser = self._create_parser()

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser with all commands."""
        parser = argparse.ArgumentParser(
            description="ValutaTrade Hub - Currency Trading Wallet",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Примеры использования:
  register --username alice --password 1234
  login --username alice --password 1234
  show-portfolio
  buy --currency BTC --amount 0.1
  sell --currency BTC --amount 0.05
  get-rate --from USD --to BTC
  list-currencies
            """
        )

        subparsers = parser.add_subparsers(dest='command', help='Команды')

        # register command
        register_parser = subparsers.add_parser('register', help='Регистрация нового пользователя')
        register_parser.add_argument('--username', required=True, help='Имя пользователя')
        register_parser.add_argument('--password', required=True, help='Пароль')

        # login command
        login_parser = subparsers.add_parser('login', help='Вход в систему')
        login_parser.add_argument('--username', required=True, help='Имя пользователя')
        login_parser.add_argument('--password', required=True, help='Пароль')

        # logout command
        subparsers.add_parser('logout', help='Выход из системы')

        # show-portfolio command
        portfolio_parser = subparsers.add_parser('show-portfolio', help='Показать портфель')
        portfolio_parser.add_argument('--base', default='USD', help='Базовая валюта для расчета (по умолчанию USD)')

        # buy command
        buy_parser = subparsers.add_parser('buy', help='Купить валюту')
        buy_parser.add_argument('--currency', required=True, help='Код покупаемой валюты (например, BTC)')
        buy_parser.add_argument('--amount', type=float, required=True, help='Количество покупаемой валюты')

        # sell command
        sell_parser = subparsers.add_parser('sell', help='Продать валюту')
        sell_parser.add_argument('--currency', required=True, help='Код продаваемой валюты')
        sell_parser.add_argument('--amount', type=float, required=True, help='Количество продаваемой валюты')

        # get-rate command
        rate_parser = subparsers.add_parser('get-rate', help='Получить курс валюты')
        rate_parser.add_argument('--from', required=True, dest='from_currency', help='Исходная валюта')
        rate_parser.add_argument('--to', required=True, dest='to_currency', help='Целевая валюта')

        # whoami command
        subparsers.add_parser('whoami', help='Показать текущего пользователя')

        # list-currencies command
        subparsers.add_parser('list-currencies', help='Показать все доступные валюты')

        # currency-info command
        currency_parser = subparsers.add_parser('currency-info', help='Информация о валюте')
        currency_parser.add_argument('--currency', required=True, help='Код валюты')

        return parser

    def run(self, args=None):
        """Run CLI with provided arguments."""
        if args is None:
            args = sys.argv[1:]

        if not args:
            self.parser.print_help()
            return

        parsed_args = self.parser.parse_args(args)

        try:
            if parsed_args.command == 'register':
                self.handle_register(parsed_args)
            elif parsed_args.command == 'login':
                self.handle_login(parsed_args)
            elif parsed_args.command == 'logout':
                self.handle_logout()
            elif parsed_args.command == 'show-portfolio':
                self.handle_show_portfolio(parsed_args)
            elif parsed_args.command == 'buy':
                self.handle_buy(parsed_args)
            elif parsed_args.command == 'sell':
                self.handle_sell(parsed_args)
            elif parsed_args.command == 'get-rate':
                self.handle_get_rate(parsed_args)
            elif parsed_args.command == 'whoami':
                self.handle_whoami()
            elif parsed_args.command == 'list-currencies':
                self.handle_list_currencies()
            elif parsed_args.command == 'currency-info':
                self.handle_currency_info(parsed_args)
            else:
                self.parser.print_help()
        except ValutaTradeError as e:
            print(f"ОШИБКА: {e}")
        except Exception as e:
            print(f"НЕОЖИДАННАЯ ОШИБКА: {e}")

    def handle_register(self, args):
        """Handle user registration."""
        user = user_manager.register_user(args.username, args.password)
        print(f"УСПЕХ: Пользователь '{user.username}' зарегистрирован (id={user.user_id}).")
        print("   Войдите: login --username {} --password ****".format(args.username))

    def handle_login(self, args):
        """Handle user login."""
        user = user_manager.authenticate_user(args.username, args.password)
        session_manager.login(user)
        print(f"УСПЕХ: Вы вошли как '{user.username}'")

    def handle_logout(self):
        """Handle user logout."""
        if session_manager.is_authenticated:
            username = session_manager.current_user.username
            session_manager.logout()
            print(f"УСПЕХ: Вы вышли из системы. До свидания, {username}!")
        else:
            print("ИНФО: Вы не вошли в систему")

    def handle_whoami(self):
        """Show current user info."""
        if session_manager.is_authenticated:
            user = session_manager.current_user
            info = user.get_user_info()
            print(f"ТЕКУЩИЙ ПОЛЬЗОВАТЕЛЬ: {info['username']} (id: {info['user_id']})")
            print(f"ДАТА РЕГИСТРАЦИИ: {info['registration_date']}")
        else:
            print("ИНФО: Вы не вошли в систему")

    def handle_show_portfolio(self, args):
        """Show user portfolio."""
        user = session_manager.require_auth()
        portfolio = portfolio_manager.get_user_portfolio(user.user_id)

        if not portfolio.wallets:
            print("ВАШ ПОРТФЕЛЬ ПУСТ. Используйте 'buy' для добавления валют.")
            return

        # Create table
        table = PrettyTable()
        table.field_names = ["Валюта", "Баланс", f"Стоимость ({args.base})", "Доля (%)"]

        total_value = portfolio.get_total_value(args.base)

        for currency_code, wallet in portfolio.wallets.items():
            balance = wallet.balance

            if currency_code == args.base:
                value = balance
            else:
                try:
                    rate = ExchangeRates.get_rate(currency_code, args.base)
                    value = balance * rate
                except ValutaTradeError:
                    value = 0

            percentage = (value / total_value * 100) if total_value > 0 else 0

            table.add_row([
                currency_code,
                format_currency_amount(balance, currency_code),
                f"{value:.2f}",
                f"{percentage:.1f}%"
            ])

        print(f"ПОРТФЕЛЬ пользователя '{user.username}' (база: {args.base}):")
        print(table)
        print(f"ИТОГО: {total_value:,.2f} {args.base}")

    def handle_buy(self, args):
        """Handle currency purchase."""
        user = session_manager.require_auth()

        if args.amount <= 0:
            raise ValueError("'amount' должен быть положительным числом")

        currency_code = args.currency.upper()

        # Validate currency
        try:
            currency_info = rate_manager.get_currency_info(currency_code)
            print(f"Информация о валюте: {currency_info}")
        except CurrencyNotFoundError as e:
            print(f"ОШИБКА: {e}")
            print("   Используйте 'list-currencies' для просмотра доступных валют.")
            return

        # Add currency to portfolio if it doesn't exist
        if currency_code not in portfolio_manager.get_user_portfolio(user.user_id).wallets:
            portfolio_manager.add_currency_to_portfolio(user.user_id, currency_code)

        # Deposit the currency
        portfolio_manager.deposit_to_wallet(user.user_id, currency_code, args.amount)

        # Calculate estimated cost in USD
        try:
            rate = ExchangeRates.get_rate(currency_code, 'USD')
            cost = args.amount * rate
        except ValutaTradeError:
            cost = 0

        portfolio = portfolio_manager.get_user_portfolio(user.user_id)
        new_balance = portfolio.get_wallet(currency_code).balance

        print(f"УСПЕХ: Покупка выполнена: {format_currency_amount(args.amount, currency_code)}")
        if cost > 0:
            print(f"   Оценочная стоимость покупки: {cost:,.2f} USD")
        print("   Изменения в портфеле:")
        print(f"   - {currency_code}: стало {format_currency_amount(new_balance, currency_code)}")

    def handle_sell(self, args):
        """Handle currency sale."""
        user = session_manager.require_auth()

        if args.amount <= 0:
            raise ValueError("'amount' должен быть положительным числом")

        currency_code = args.currency.upper()

        # Validate currency exists
        try:
            get_currency(currency_code)
        except CurrencyNotFoundError as e:
            print(f"ОШИБКА: {e}")
            return

        try:
            # Withdraw the currency
            portfolio_manager.withdraw_from_wallet(user.user_id, currency_code, args.amount)

            # Calculate estimated revenue in USD
            try:
                rate = ExchangeRates.get_rate(currency_code, 'USD')
                revenue = args.amount * rate
            except ValutaTradeError:
                revenue = 0

            portfolio = portfolio_manager.get_user_portfolio(user.user_id)
            new_balance = portfolio.get_wallet(currency_code).balance

            print(f"УСПЕХ: Продажа выполнена: {format_currency_amount(args.amount, currency_code)}")
            if revenue > 0:
                print(f"   Оценочная выручка: {revenue:,.2f} USD")
            print("   Изменения в портфеле:")
            print(f"   - {currency_code}: стало {format_currency_amount(new_balance, currency_code)}")

        except InsufficientFundsError as e:
            print(f"ОШИБКА: {e}")

    def handle_get_rate(self, args):
        """Handle exchange rate lookup."""
        from_currency = args.from_currency.upper()
        to_currency = args.to_currency.upper()

        try:
            # Validate currencies
            from_curr = get_currency(from_currency)
            to_curr = get_currency(to_currency)

            rate = rate_manager.get_exchange_rate(from_currency, to_currency)
            reverse_rate = rate_manager.get_exchange_rate(to_currency, from_currency)

            print(f"КУРС {from_currency} -> {to_currency}: {rate:.6f}")
            print(f"   Обратный курс {to_currency} -> {from_currency}: {reverse_rate:.6f}")
            print(f"   {from_curr.get_display_info()}")
            print(f"   {to_curr.get_display_info()}")

        except CurrencyNotFoundError as e:
            print(f"ОШИБКА: {e}")
            print("   Используйте 'list-currencies' для просмотра доступных валют.")
        except ValutaTradeError as e:
            print(f"ОШИБКА: {e}")

    def handle_list_currencies(self):
        """Handle list currencies command."""
        currencies = CurrencyRegistry.get_all_currencies()

        fiat_table = PrettyTable()
        fiat_table.field_names = ["Код", "Название", "Страна эмитент"]

        crypto_table = PrettyTable()
        crypto_table.field_names = ["Код", "Название", "Алгоритм", "Капитализация"]

        for code, currency in currencies.items():
            if hasattr(currency, 'issuing_country'):
                # Fiat currency
                fiat_table.add_row([code, currency.name, currency.issuing_country])
            else:
                # Crypto currency
                mcap_str = f"{currency.market_cap:.2e}" if currency.market_cap > 0 else "N/A"
                crypto_table.add_row([code, currency.name, currency.algorithm, mcap_str])

        print("ФИАТНЫЕ ВАЛЮТЫ:")
        print(fiat_table)
        print("\nКРИПТОВАЛЮТЫ:")
        print(crypto_table)
        print(f"\nВсего доступно валют: {len(currencies)}")

    def handle_currency_info(self, args):
        """Handle currency info command."""
        currency_code = args.currency.upper()

        try:
            currency = get_currency(currency_code)
            print(f"ИНФОРМАЦИЯ О ВАЛЮТЕ {currency_code}:")
            print(f"  {currency.get_display_info()}")

            # Show current rates to major currencies
            print("\nТЕКУЩИЕ КУРСЫ:")
            major_currencies = ['USD', 'EUR', 'BTC']
            for major in major_currencies:
                if major != currency_code:
                    try:
                        rate = rate_manager.get_exchange_rate(currency_code, major)
                        print(f"  {currency_code} -> {major}: {rate:.6f}")
                    except ValutaTradeError:
                        continue

        except CurrencyNotFoundError as e:
            print(f"ОШИБКА: {e}")
            print("   Используйте 'list-currencies' для просмотра доступных валют.")


def main():
    """CLI entry point."""
    cli = CLI()
    cli.run()


if __name__ == "__main__":
    main()
