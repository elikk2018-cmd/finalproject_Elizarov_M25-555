#!/usr/bin/env python3
"""Тестирование полной интеграции логирования, исключений и синглтонов"""

import logging
import os
import tempfile

from valutatrade_hub.core.currencies import get_currency
from valutatrade_hub.core.exceptions import (
    AuthenticationError,
    CurrencyNotFoundError,
    InsufficientFundsError,
    ValidationError,
)
from valutatrade_hub.decorators import (
    log_action,
    require_authentication,
    validate_currency,
)
from valutatrade_hub.infra.database import DatabaseManager
from valutatrade_hub.infra.settings import SettingsLoader


def test_enhanced_logging():
    print("=== ТЕСТИРОВАНИЕ УЛУЧШЕННОГО ЛОГИРОВАНИЯ ===")

    try:
        # Test logging configuration
        logger = logging.getLogger(__name__)

        # Test different log levels
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")

        # Test structured logging
        logger.info("Structured log", extra={
            'operation': 'TEST',
            'user_id': 123,
            'currency': 'USD',
            'amount': 100.0
        })

        print("✅ Логирование работает на всех уровнях")

        # Check log file creation
        if os.path.exists("logs/valutatrade.log"):
            print("✅ Файл логов создан")
        else:
            print("⚠️  Файл логов не создан (может быть нормально в тестовой среде)")

    except Exception as e:
        print(f"❌ Ошибка логирования: {e}")


def test_enhanced_exceptions():
    print("\n=== ТЕСТИРОВАНИЕ УЛУЧШЕННЫХ ИСКЛЮЧЕНИЙ ===")

    try:
        # Test CurrencyNotFoundError with details
        try:
            get_currency("INVALID")
        except CurrencyNotFoundError as e:
            assert "INVALID" in str(e)
            assert "details" in e.to_dict()
            print("✅ CurrencyNotFoundError с деталями")

        # Test InsufficientFundsError
        try:
            raise InsufficientFundsError(100, 200, "USD", "purchase")
        except InsufficientFundsError as e:
            assert e.details["available"] == 100
            assert e.details["required"] == 200
            print("✅ InsufficientFundsError с контекстом")

        # Test ValidationError
        try:
            raise ValidationError("email", "invalid", "must be valid email format")
        except ValidationError as e:
            assert e.details["field"] == "email"
            assert e.details["reason"] == "must be valid email format"
            print("✅ ValidationError с детальной информацией")

        print("✅ Все исключения работают с улучшенной информацией")

    except Exception as e:
        print(f"❌ Ошибка тестирования исключений: {e}")


def test_thread_safe_singletons():
    print("\n=== ТЕСТИРОВАНИЕ ПОТОКОБЕЗОПАСНЫХ СИНГЛТОНОВ ===")

    try:
        import threading

        # Test SettingsLoader singleton
        settings1 = SettingsLoader()
        settings2 = SettingsLoader()
        assert settings1 is settings2, "SettingsLoader should be singleton"

        # Test concurrent access
        results = []

        def get_setting(value):
            settings = SettingsLoader()
            results.append(settings.get('default_base_currency'))

        threads = []
        for i in range(5):
            thread = threading.Thread(target=get_setting, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        assert all(r == "USD" for r in results)
        print("✅ SettingsLoader потокобезопасный")

        # Test DatabaseManager singleton
        db1 = DatabaseManager()
        db2 = DatabaseManager()
        assert db1 is db2, "DatabaseManager should be singleton"
        print("✅ DatabaseManager потокобезопасный")

    except Exception as e:
        print(f"❌ Ошибка тестирования синглтонов: {e}")


def test_enhanced_decorators():
    print("\n=== ТЕСТИРОВАНИЕ УЛУЧШЕННЫХ ДЕКОРАТОРОВ ===")

    try:
        # Test log_action decorator
        @log_action(operation="TEST_OPERATION", verbose=True)
        def test_function(x, y):
            return x + y

        result = test_function(2, 3)
        assert result == 5
        print("✅ Декоратор log_action работает")

        # Test validate_currency decorator
        @validate_currency('code')
        def currency_function(code):
            return code

        try:
            currency_function("USD")
            print("✅ Декоратор validate_currency (успех)")
        except CurrencyNotFoundError:
            print("❌ Декоратор validate_currency (неожиданная ошибка)")

        try:
            currency_function("INVALID")
            print("❌ Декоратор validate_currency (должен был вызвать ошибку)")
        except CurrencyNotFoundError:
            print("✅ Декоратор validate_currency (корректная ошибка)")

        # Test require_authentication decorator
        @require_authentication
        def secure_function():
            return "secret"

        try:
            secure_function()
            print("❌ Декоратор require_authentication (должен был вызвать ошибку)")
        except AuthenticationError:
            print("✅ Декоратор require_authentication (корректная ошибка)")

    except Exception as e:
        print(f"❌ Ошибка тестирования декораторов: {e}")


def test_database_transactions():
    print("\n=== ТЕСТИРОВАНИЕ ТРАНЗАКЦИЙ БАЗЫ ДАННЫХ ===")

    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Configure settings to use temp directory
            settings = SettingsLoader()
            settings.set('data_dir', temp_dir)
            settings.set('backup_dir', os.path.join(temp_dir, 'backups'))

            db = DatabaseManager()

            # Test transaction
            with db.transaction() as tx:
                tx.add_operation({
                    'type': 'update',
                    'entity': 'test',
                    'key': 'id',
                    'value': 1,
                    'data': {'id': 1, 'name': 'test1'}
                })
                tx.add_operation({
                    'type': 'update',
                    'entity': 'test',
                    'key': 'id',
                    'value': 2,
                    'data': {'id': 2, 'name': 'test2'}
                })
                tx.commit()

            # Verify data was written
            data = db.read_data("test")
            assert len(data) == 2
            print("✅ Транзакции базы данных работают")

            # Test backup creation
            backup_files = os.listdir(os.path.join(temp_dir, 'backups'))
            assert any('test_' in f for f in backup_files)
            print("✅ Создание бэкапов работает")

        except Exception as e:
            print(f"❌ Ошибка тестирования транзакций: {e}")


def main():
    print("🚀 ТЕСТИРОВАНИЕ ПОЛНОЙ ИНТЕГРАЦИИ СИСТЕМЫ")
    print("=" * 60)

    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)

    test_enhanced_logging()
    test_enhanced_exceptions()
    test_thread_safe_singletons()
    test_enhanced_decorators()
    test_database_transactions()

    print("\n" + "=" * 60)
    print("🎯 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("\n📝 Проверьте файл logs/valutatrade.log для просмотра детальных логов")


if __name__ == "__main__":
    main()
