#!/usr/bin/env python3
"""
ValutaTrade Hub - Main entry point
Currency trading simulation platform
"""
from valutatrade_hub.core.usecases import user_manager, portfolio_manager
from valutatrade_hub.core.exceptions import ValutaTradeError


def main():
    """Основная функция приложения"""
    print("=" * 50)
    print("      ValutaTrade Hub - Currency Trading Wallet")
    print("=" * 50)
    print("\nДобро пожаловать! Это платформа для симуляции торговли валютами.")
    
    # Демонстрация работы моделей
    demo_models()
    
    print("\nДля начала работы используйте команды:")
    print("  register --username <name> --password <pass>  - регистрация")
    print("  login --username <name> --password <pass>     - вход в систему")
    print("  --help                                        - справка по командам")
    print("\nПроект находится в разработке...")


def demo_models():
    """Демонстрация работы моделей данных."""
    print("\n--- Демонстрация моделей данных ---")
    
    try:
        # Тестируем регистрацию пользователя
        print("1. Регистрация пользователя...")
        user = user_manager.register_user("test_user", "test123")
        print(f"   ✅ Создан пользователь: {user.get_user_info()}")
        
        # Тестируем аутентификацию
        print("2. Аутентификация пользователя...")
        auth_user = user_manager.authenticate_user("test_user", "test123")
        print(f"   ✅ Пользователь аутентифицирован: {auth_user.username}")
        
        # Тестируем работу с портфелем
        print("3. Создание портфеля...")
        portfolio = portfolio_manager.get_user_portfolio(user.user_id)
        print(f"   ✅ Портфель создан для пользователя ID: {portfolio.user_id}")
        
        # Тестируем добавление валют
        print("4. Добавление валют в портфель...")
        portfolio_manager.add_currency_to_portfolio(user.user_id, "USD")
        portfolio_manager.add_currency_to_portfolio(user.user_id, "BTC")
        print("   ✅ Добавлены валюты: USD, BTC")
        
        # Тестируем пополнение баланса
        print("5. Пополнение баланса...")
        portfolio_manager.deposit_to_wallet(user.user_id, "USD", 1000.0)
        portfolio_manager.deposit_to_wallet(user.user_id, "BTC", 0.1)
        
        # Получаем обновленный портфель
        updated_portfolio = portfolio_manager.get_user_portfolio(user.user_id)
        total_value = updated_portfolio.get_total_value("USD")
        
        print("   ✅ Балансы пополнены:")
        for currency, wallet in updated_portfolio.wallets.items():
            print(f"      - {currency}: {wallet.balance}")
        print(f"   💰 Общая стоимость портфеля: {total_value:.2f} USD")
        
        print("\n🎉 Модели данных работают корректно!")
        
    except ValutaTradeError as e:
        print(f"   ❌ Ошибка: {e}")
    except Exception as e:
        print(f"   ❌ Неожиданная ошибка: {e}")


if __name__ == "__main__":
    main()
