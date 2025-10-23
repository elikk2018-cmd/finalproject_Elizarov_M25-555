"""Interactive CLI mode for ValutaTrade Hub."""
import cmd
import shlex

from prettytable import PrettyTable

from ..core.exceptions import ValutaTradeError
from ..core.session import session_manager
from ..core.usecases import portfolio_manager, user_manager
from ..core.utils import ExchangeRates, format_currency_amount


class ValutaTradeCLI(cmd.Cmd):
    """Interactive command line interface for ValutaTrade Hub."""

    prompt = 'valutatrade> '
    intro = '''
==================================================
      ValutaTrade Hub - Currency Trading Wallet
==================================================

Добро пожаловать! Используйте команды для управления вашим портфелем.
Для справки введите "help" или "?".
Для выхода введите "exit" или "quit".
'''

    def __init__(self):
        super().__init__()
        self.user_manager = user_manager
        self.portfolio_manager = portfolio_manager

    def do_register(self, arg):
        """Регистрация нового пользователя: register --username NAME --password PASS"""
        try:
            args = self._parse_args(arg)
            username = args.get('--username')
            password = args.get('--password')

            if not username or not password:
                print("Использование: register --username NAME --password PASS")
                return

            user = self.user_manager.register_user(username, password)
            print(f"УСПЕХ: Пользователь '{user.username}' зарегистрирован (id={user.user_id}).")
            print(f"       Войдите: login --username {username} --password ****")

        except ValutaTradeError as e:
            print(f"ОШИБКА: {e}")
        except Exception as e:
            print(f"НЕОЖИДАННАЯ ОШИБКА: {e}")

    def do_login(self, arg):
        """Вход в систему: login --username NAME --password PASS"""
        try:
            args = self._parse_args(arg)
            username = args.get('--username')
            password = args.get('--password')

            if not username or not password:
                print("Использование: login --username NAME --password PASS")
                return

            user = self.user_manager.authenticate_user(username, password)
            session_manager.login(user)
            self.prompt = f'valutatrade({username})> '
            print(f"УСПЕХ: Вы вошли как '{user.username}'")

        except ValutaTradeError as e:
            print(f"ОШИБКА: {e}")
        except Exception as e:
            print(f"НЕОЖИДАННАЯ ОШИБКА: {e}")

    def do_logout(self, arg):
        """Выход из системы: logout"""
        if session_manager.is_authenticated:
            username = session_manager.current_user.username
            session_manager.logout()
            self.prompt = 'valutatrade> '
            print(f"УСПЕХ: Вы вышли из системы. До свидания, {username}!")
        else:
            print("ИНФО: Вы не вошли в систему")

    def do_whoami(self, arg):
        """Показать текущего пользователя: whoami"""
        if session_manager.is_authenticated:
            user = session_manager.current_user
            info = user.get_user_info()
            print(f"ТЕКУЩИЙ ПОЛЬЗОВАТЕЛЬ: {info['username']} (id: {info['user_id']})")
            print(f"ДАТА РЕГИСТРАЦИИ: {info['registration_date']}")
        else:
            print("ИНФО: Вы не вошли в систему")

    def do_show_portfolio(self, arg):
        """Показать портфель: show_portfolio [--base CURRENCY]"""
        try:
            user = session_manager.require_auth()
            args = self._parse_args(arg)
            base_currency = args.get('--base', 'USD')

            portfolio = self.portfolio_manager.get_user_portfolio(user.user_id)

            if not portfolio.wallets:
                print("ВАШ ПОРТФЕЛЬ ПУСТ. Используйте 'buy' для добавления валют.")
                return

            # Create table
            table = PrettyTable()
            table.field_names = ["Валюта", "Баланс", f"Стоимость ({base_currency})", "Доля (%)"]

            total_value = portfolio.get_total_value(base_currency)

            for currency_code, wallet in portfolio.wallets.items():
                balance = wallet.balance

                if currency_code == base_currency:
                    value = balance
                else:
                    try:
                        rate = ExchangeRates.get_rate(currency_code, base_currency)
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

            print(f"ПОРТФЕЛЬ пользователя '{user.username}' (база: {base_currency}):")
            print(table)
            print(f"ИТОГО: {total_value:,.2f} {base_currency}")

        except ValutaTradeError as e:
            print(f"ОШИБКА: {e}")
        except Exception as e:
            print(f"НЕОЖИДАННАЯ ОШИБКА: {e}")

    def do_buy(self, arg):
        """Купить валюту: buy --currency CODE --amount AMOUNT"""
        try:
            user = session_manager.require_auth()
            args = self._parse_args(arg)
            currency_code = args.get('--currency')
            amount = args.get('--amount')

            if not currency_code or not amount:
                print("Использование: buy --currency CODE --amount AMOUNT")
                return

            amount = float(amount)
            currency_code = currency_code.upper()

            if amount <= 0:
                print("ОШИБКА: 'amount' должен быть положительным числом")
                return

            # Add currency to portfolio if it doesn't exist
            if currency_code not in self.portfolio_manager.get_user_portfolio(user.user_id).wallets:
                self.portfolio_manager.add_currency_to_portfolio(user.user_id, currency_code)

            # Deposit the currency
            self.portfolio_manager.deposit_to_wallet(user.user_id, currency_code, amount)

            # Calculate estimated cost in USD
            try:
                rate = ExchangeRates.get_rate(currency_code, 'USD')
                cost = amount * rate
            except ValutaTradeError:
                cost = 0

            portfolio = self.portfolio_manager.get_user_portfolio(user.user_id)
            new_balance = portfolio.get_wallet(currency_code).balance

            print(f"УСПЕХ: Покупка выполнена: {format_currency_amount(amount, currency_code)}")
            if cost > 0:
                print(f"       Оценочная стоимость покупки: {cost:,.2f} USD")
            print("       Изменения в портфеле:")
            print(f"       - {currency_code}: стало {format_currency_amount(new_balance, currency_code)}")

        except ValutaTradeError as e:
            print(f"ОШИБКА: {e}")
        except Exception as e:
            print(f"НЕОЖИДАННАЯ ОШИБКА: {e}")

    def do_sell(self, arg):
        """Продать валюту: sell --currency CODE --amount AMOUNT"""
        try:
            user = session_manager.require_auth()
            args = self._parse_args(arg)
            currency_code = args.get('--currency')
            amount = args.get('--amount')

            if not currency_code or not amount:
                print("Использование: sell --currency CODE --amount AMOUNT")
                return

            amount = float(amount)
            currency_code = currency_code.upper()

            if amount <= 0:
                print("ОШИБКА: 'amount' должен быть положительным числом")
                return

            # Withdraw the currency
            self.portfolio_manager.withdraw_from_wallet(user.user_id, currency_code, amount)

            # Calculate estimated revenue in USD
            try:
                rate = ExchangeRates.get_rate(currency_code, 'USD')
                revenue = amount * rate
            except ValutaTradeError:
                revenue = 0

            portfolio = self.portfolio_manager.get_user_portfolio(user.user_id)
            new_balance = portfolio.get_wallet(currency_code).balance

            print(f"УСПЕХ: Продажа выполнена: {format_currency_amount(amount, currency_code)}")
            if revenue > 0:
                print(f"       Оценочная выручка: {revenue:,.2f} USD")
            print("       Изменения в портфеле:")
            print(f"       - {currency_code}: стало {format_currency_amount(new_balance, currency_code)}")

        except ValutaTradeError as e:
            print(f"ОШИБКА: {e}")
        except Exception as e:
            print(f"НЕОЖИДАННАЯ ОШИБКА: {e}")

    def do_get_rate(self, arg):
        """Получить курс валюты: get_rate --from CODE --to CODE"""
        try:
            args = self._parse_args(arg)
            from_currency = args.get('--from')
            to_currency = args.get('--to')

            if not from_currency or not to_currency:
                print("Использование: get_rate --from CODE --to CODE")
                return

            from_currency = from_currency.upper()
            to_currency = to_currency.upper()

            rate = ExchangeRates.get_rate(from_currency, to_currency)
            reverse_rate = ExchangeRates.get_rate(to_currency, from_currency)

            print(f"КУРС {from_currency} -> {to_currency}: {rate:.6f}")
            print(f"       Обратный курс {to_currency} -> {from_currency}: {reverse_rate:.6f}")

        except ValutaTradeError as e:
            print(f"ОШИБКА: {e}")
            print("       Попробуйте обновить курсы позже или проверьте коды валют.")
        except Exception as e:
            print(f"НЕОЖИДАННАЯ ОШИБКА: {e}")

    def do_exit(self, arg):
        """Выход из приложения: exit"""
        print("До свидания!")
        return True

    def do_quit(self, arg):
        """Выход из приложения: quit"""
        return self.do_exit(arg)

    def _parse_args(self, arg_string):
        """Parse command line arguments."""
        args = {}
        parts = shlex.split(arg_string)

        i = 0
        while i < len(parts):
            if parts[i].startswith('--'):
                key = parts[i]
                if i + 1 < len(parts) and not parts[i + 1].startswith('--'):
                    args[key] = parts[i + 1]
                    i += 2
                else:
                    args[key] = True
                    i += 1
            else:
                i += 1

        return args


def run_interactive():
    """Run interactive CLI mode."""
    cli = ValutaTradeCLI()
    cli.cmdloop()
