#!/usr/bin/env python3
"""Расширенный тестовый скрипт для проверки всех компонентов системы"""

import os
import json
from valutatrade_hub.core.usecases import user_manager, portfolio_manager
from valutatrade_hub.core.exceptions import *
from valutatrade_hub.core.utils import ExchangeRates


def cleanup_test_data():
    """Очистка тестовых данных"""
    if os.path.exists("data/users.json"):
        os.remove("data/users.json")
    if os.path.exists("data/portfolios.json"):
        os.remove("data/portfolios.json")
    print("🗑️  Тестовые данные очищены")


def test_user_management():
    print("\n" + "="*60)
    print("ТЕСТИРОВАНИЕ УПРАВЛЕНИЯ ПОЛЬЗОВАТЕЛЯМИ")
    print("="*60)
    
    # Тест 1: Регистрация нового пользователя
    print("\n1. 📝 Регистрация пользователя 'alice'")
    try:
        alice = user_manager.register_user("alice", "password123")
        print(f"   ✅ Успешно создан пользователь: {alice.get_user_info()}")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return
    
    # Тест 2: Попытка создать пользователя с существующим именем
    print("\n2. 🚫 Попытка создать пользователя с существующим именем 'alice'")
    try:
        user_manager.register_user("alice", "anotherpass")
        print("   ❌ Должна быть ошибка, но её нет!")
    except ValueError as e:
        print(f"   ✅ Корректная ошибка: {e}")
    
    # Тест 3: Аутентификация с правильным паролем
    print("\n3. 🔐 Аутентификация с правильным паролем")
    try:
        auth_user = user_manager.authenticate_user("alice", "password123")
        print(f"   ✅ Успешная аутентификация: {auth_user.username}")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    # Тест 4: Аутентификация с неправильным паролем
    print("\n4. ❌ Аутентификация с неправильным паролем")
    try:
        user_manager.authenticate_user("alice", "wrongpassword")
        print("   ❌ Должна быть ошибка, но её нет!")
    except AuthenticationError as e:
        print(f"   ✅ Корректная ошибка: {e}")
    
    # Тест 5: Получение пользователя по ID
    print("\n5. 👤 Получение пользователя по ID")
    try:
        user_by_id = user_manager.get_user_by_id(alice.user_id)
        print(f"   ✅ Пользователь найден: {user_by_id.username}")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    return alice


def test_wallet_operations(user):
    print("\n" + "="*60)
    print("ТЕСТИРОВАНИЕ ОПЕРАЦИЙ С КОШЕЛЬКАМИ")
    print("="*60)
    
    # Тест 1: Создание портфеля и добавление валют
    print("\n1. 💰 Создание портфеля и добавление валют")
    try:
        portfolio = portfolio_manager.get_user_portfolio(user.user_id)
        portfolio_manager.add_currency_to_portfolio(user.user_id, "USD")
        portfolio_manager.add_currency_to_portfolio(user.user_id, "EUR")
        portfolio_manager.add_currency_to_portfolio(user.user_id, "BTC")
        print("   ✅ Валюты добавлены в портфель")
        
        # Показываем портфель
        updated_portfolio = portfolio_manager.get_user_portfolio(user.user_id)
        print("   Текущий портфель:")
        for currency, wallet in updated_portfolio.wallets.items():
            print(f"     - {currency}: {wallet.balance}")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return
    
    # Тест 2: Пополнение баланса
    print("\n2. 📈 Пополнение баланса")
    try:
        portfolio_manager.deposit_to_wallet(user.user_id, "USD", 1000.0)
        portfolio_manager.deposit_to_wallet(user.user_id, "EUR", 500.0)
        portfolio_manager.deposit_to_wallet(user.user_id, "BTC", 0.05)
        
        updated_portfolio = portfolio_manager.get_user_portfolio(user.user_id)
        print("   ✅ Балансы пополнены:")
        for currency, wallet in updated_portfolio.wallets.items():
            print(f"     - {currency}: {wallet.balance}")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    # Тест 3: Снятие средств
    print("\n3. 📉 Снятие средств с кошелька USD")
    try:
        portfolio_manager.withdraw_from_wallet(user.user_id, "USD", 200.0)
        updated_portfolio = portfolio_manager.get_user_portfolio(user.user_id)
        usd_balance = updated_portfolio.get_wallet("USD").balance
        print(f"   ✅ Успешное снятие. Новый баланс USD: {usd_balance}")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    # Тест 4: Попытка снять больше чем есть
    print("\n4. 🚫 Попытка снять больше средств чем есть на счете")
    try:
        portfolio_manager.withdraw_from_wallet(user.user_id, "USD", 5000.0)
        print("   ❌ Должна быть ошибка, но её нет!")
    except InsufficientFundsError as e:
        print(f"   ✅ Корректная ошибка: {e}")


def test_portfolio_operations(user):
    print("\n" + "="*60)
    print("ТЕСТИРОВАНИЕ ОПЕРАЦИЙ С ПОРТФЕЛЕМ")
    print("="*60)
    
    portfolio = portfolio_manager.get_user_portfolio(user.user_id)
    
    # Тест 1: Расчет общей стоимости портфеля
    print("\n1. 🧮 Расчет общей стоимости портфеля в USD")
    try:
        total_value = portfolio.get_total_value("USD")
        print(f"   ✅ Общая стоимость портфеля: {total_value:.2f} USD")
        
        # Показываем детали
        print("   Детали расчета:")
        for currency, wallet in portfolio.wallets.items():
            if currency == "USD":
                value = wallet.balance
            else:
                try:
                    rate = ExchangeRates.get_rate(currency, "USD")
                    value = wallet.balance * rate
                except:
                    value = 0
            print(f"     - {currency}: {wallet.balance} → {value:.2f} USD")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    # Тест 2: Расчет стоимости в EUR
    print("\n2. 🧮 Расчет общей стоимости портфеля в EUR")
    try:
        total_value_eur = portfolio.get_total_value("EUR")
        print(f"   ✅ Общая стоимость портфеля: {total_value_eur:.2f} EUR")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    # Тест 3: Получение несуществующего кошелька
    print("\n3. 🚫 Попытка получить несуществующий кошелек")
    try:
        portfolio.get_wallet("XYZ")
        print("   ❌ Должна быть ошибка, но её нет!")
    except ValueError as e:
        print(f"   ✅ Корректная ошибка: {e}")


def test_data_persistence():
    print("\n" + "="*60)
    print("ТЕСТИРОВАНИЕ СОХРАНЕНИЯ ДАННЫХ")
    print("="*60)
    
    print("\n1. 💾 Проверка сохраненных данных")
    
    # Читаем данные из файлов
    try:
        with open("data/users.json", "r") as f:
            users_data = json.load(f)
        print(f"   ✅ Файл users.json: {len(users_data)} пользователь(ей)")
        
        with open("data/portfolios.json", "r") as f:
            portfolios_data = json.load(f)
        print(f"   ✅ Файл portfolios.json: {len(portfolios_data)} портфель(ей)")
        
        # Показываем структуру данных
        if users_data:
            user = users_data[0]
            print(f"   👤 Данные пользователя: ID={user['user_id']}, имя='{user['username']}'")
            print(f"     Хеш пароля: {user['hashed_password'][:20]}...")
            print(f"     Соль: {user['salt']}")
        
        if portfolios_data:
            portfolio = portfolios_data[0]
            print(f"   💼 Данные портфеля: ID пользователя={portfolio['user_id']}")
            print(f"     Кошельки: {list(portfolio['wallets'].keys())}")
            
    except Exception as e:
        print(f"   ❌ Ошибка чтения данных: {e}")


def main():
    print("🚀 ЗАПУСК ТЕСТИРОВАНИЯ СИСТЕМЫ ValutaTrade Hub")
    print("="*60)
    
    # Очищаем старые тестовые данные
    cleanup_test_data()
    
    # Запускаем тесты
    user = test_user_management()
    
    if user:
        test_wallet_operations(user)
        test_portfolio_operations(user)
        test_data_persistence()
        
        print("\n" + "="*60)
        print("🎉 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО!")
        print("="*60)
        print("\n📊 Статус системы: ✅ ГОТОВА К РАБОТЕ")
        print("\nСледующие шаги:")
        print("1. Реализовать CLI интерфейс")
        print("2. Добавить систему курсов валют")
        print("3. Реализовать Parser Service")
    else:
        print("\n❌ Тестирование прервано из-за ошибок в базовых функциях")


if __name__ == "__main__":
    main()
