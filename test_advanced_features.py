#!/usr/bin/env python3
"""Тестирование расширенных функций модели данных"""

import tempfile

from valutatrade_hub.core.currencies import (
    CryptoCurrency,
    CurrencyRegistry,
    FiatCurrency,
    get_currency,
)
from valutatrade_hub.core.exceptions import CurrencyNotFoundError
from valutatrade_hub.decorators import log_action
from valutatrade_hub.infra.database import DatabaseManager
from valutatrade_hub.infra.settings import SettingsLoader


def test_currency_hierarchy():
    print("=== ТЕСТИРОВАНИЕ ИЕРАРХИИ ВАЛЮТ ===")

    try:
        # Test FiatCurrency
        usd = get_currency("USD")
        assert isinstance(usd, FiatCurrency)
        assert usd.name == "US Dollar"
        assert usd.issuing_country == "United States"
        print(f"✅ USD: {usd.get_display_info()}")

        # Test CryptoCurrency
        btc = get_currency("BTC")
        assert isinstance(btc, CryptoCurrency)
        assert btc.name == "Bitcoin"
        assert btc.algorithm == "SHA-256"
        print(f"✅ BTC: {btc.get_display_info()}")

        # Test unknown currency
        try:
            get_currency("UNKNOWN")
            assert False, "Should raise CurrencyNotFoundError"
        except CurrencyNotFoundError:
            print("✅ Корректная ошибка для неизвестной валюты")

        # Test currency registry
        all_currencies = CurrencyRegistry.get_all_currencies()
        assert "USD" in all_currencies
        assert "BTC" in all_currencies
        print(f"✅ Реестр валют содержит {len(all_currencies)} валют")

    except Exception as e:
        print(f"❌ Ошибка: {e}")


def test_singleton_pattern():
    print("\n=== ТЕСТИРОВАНИЕ SINGLETON ПАТТЕРНА ===")

    try:
        # Test SettingsLoader singleton
        settings1 = SettingsLoader()
        settings2 = SettingsLoader()
        assert settings1 is settings2, "SettingsLoader should be singleton"

        data_dir = settings1.get('data_dir')
        assert data_dir == "data"
        print(f"✅ SettingsLoader singleton: data_dir = {data_dir}")

        # Test DatabaseManager singleton
        db1 = DatabaseManager()
        db2 = DatabaseManager()
        assert db1 is db2, "DatabaseManager should be singleton"
        print("✅ DatabaseManager singleton работает")

    except Exception as e:
        print(f"❌ Ошибка: {e}")


def test_database_operations():
    print("\n=== ТЕСТИРОВАНИЕ ОПЕРАЦИЙ БАЗЫ ДАННЫХ ===")

    # Use temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Configure settings to use temp directory
            settings = SettingsLoader()
            settings.set('data_dir', temp_dir)

            db = DatabaseManager()

            # Test write and read
            test_data = [{"id": 1, "name": "test"}, {"id": 2, "name": "test2"}]
            db.write_data("test", test_data)

            read_data = db.read_data("test")
            assert read_data == test_data
            print("✅ Запись и чтение данных работают")

            # Test update entity
            db.update_entity("test", "id", 1, {"id": 1, "name": "updated"})
            updated = db.find_entity("test", "id", 1)
            assert updated["name"] == "updated"
            print("✅ Обновление сущности работает")

            # Test find entity
            found = db.find_entity("test", "id", 2)
            assert found["name"] == "test2"
            print("✅ Поиск сущности работает")

        except Exception as e:
            print(f"❌ Ошибка: {e}")


def test_logging_decorator():
    print("\n=== ТЕСТИРОВАНИЕ ДЕКОРАТОРА ЛОГИРОВАНИЯ ===")

    try:
        # Create a test function with decorator
        @log_action(verbose=True)
        def test_function(x, y):
            return x + y

        # Test successful execution
        result = test_function(2, 3)
        assert result == 5
        print("✅ Декоратор логирования (успешное выполнение)")

        # Test error logging
        @log_action()
        def failing_function():
            raise ValueError("Test error")

        try:
            failing_function()
        except ValueError:
            pass  # Expected

        print("✅ Декоратор логирования (ошибки)")

    except Exception as e:
        print(f"❌ Ошибка: {e}")


def main():
    print("🚀 ТЕСТИРОВАНИЕ РАСШИРЕННЫХ ВОЗМОЖНОСТЕЙ")
    print("=" * 50)

    test_currency_hierarchy()
    test_singleton_pattern()
    test_database_operations()
    test_logging_decorator()

    print("\n" + "=" * 50)
    print("🎯 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")


if __name__ == "__main__":
    main()
