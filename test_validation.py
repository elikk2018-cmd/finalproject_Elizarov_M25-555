#!/usr/bin/env python3
"""Тестирование валидации данных"""

from valutatrade_hub.core.utils import (
    validate_currency_code,
    validate_password,
    validate_username,
)


def test_validation():
    print("🧪 ТЕСТИРОВАНИЕ ВАЛИДАЦИИ ДАННЫХ")
    print("="*40)

    # Тесты имен пользователей
    test_cases = [
        ("alice", True, "Корректное имя"),
        ("bob123", True, "Имя с цифрами"),
        ("test_user", True, "Имя с подчеркиванием"),
        ("ab", False, "Слишком короткое"),
        ("", False, "Пустая строка"),
        ("  ", False, "Только пробелы"),
        ("verylongusername123", True, "Длинное имя"),
    ]

    print("\n👤 Валидация имен пользователей:")
    for username, expected, description in test_cases:
        result = validate_username(username)
        status = "✅" if result == expected else "❌"
        print(f"   {status} '{username}' ({description}): {result} (ожидалось: {expected})")

    # Тесты паролей
    password_cases = [
        ("1234", True, "Минимальная длина"),
        ("password", True, "Нормальный пароль"),
        ("123", False, "Слишком короткий"),
        ("", False, "Пустой пароль"),
    ]

    print("\n🔐 Валидация паролей:")
    for password, expected, description in password_cases:
        result = validate_password(password)
        status = "✅" if result == expected else "❌"
        print(f"   {status} '{password}' ({description}): {result} (ожидалось: {expected})")

    # Тесты кодов валют
    currency_cases = [
        ("USD", True, "Корректный код"),
        ("EUR", True, "Корректный код"),
        ("BTC", True, "Криптовалюта"),
        ("U", False, "Слишком короткий"),
        ("USDDD", False, "Слишком длинный"),
        ("U1", False, "С цифрами"),
        ("", False, "Пустая строка"),
    ]

    print("\n💱 Валидация кодов валют:")
    for currency, expected, description in currency_cases:
        result = validate_currency_code(currency)
        status = "✅" if result == expected else "❌"
        print(f"   {status} '{currency}' ({description}): {result} (ожидалось: {expected})")

if __name__ == "__main__":
    test_validation()
