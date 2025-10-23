#!/usr/bin/env python3
"""Демонстрация полной системы с логированием, исключениями и синглтонами"""

import os
import subprocess
import sys
import time


def run_command(command, description):
    """Run a command and show description."""
    print(f"\n--- {description} ---")
    print(f"   Команда: {' '.join(command)}")

    result = subprocess.run(
        [sys.executable, "main.py"] + command,
        capture_output=True,
        text=True
    )

    # Print output
    for line in result.stdout.split('\n'):
        if line.strip():
            print(f"   {line}")

    if result.stderr:
        print("   ОШИБКА:")
        for line in result.stderr.split('\n'):
            if line.strip():
                print(f"      {line}")

    time.sleep(0.5)
    return result.returncode == 0


def main():
    """Run complete system demo."""
    print("🚀 ДЕМОНСТРАЦИЯ ПОЛНОЙ СИСТЕМЫ VALUTATRADE HUB")
    print("=" * 60)

    # Clean previous data and ensure directories
    if os.path.exists("data/users.json"):
        os.remove("data/users.json")
    if os.path.exists("data/portfolios.json"):
        os.remove("data/portfolios.json")

    os.makedirs("data", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    os.makedirs("backups", exist_ok=True)

    print("\n1. Работа с улучшенными исключениями")
    print("=" * 40)

    run_command(["get-rate", "--from", "INVALID", "--to", "USD"], "Неизвестная валюта (детализированная ошибка)")
    run_command(["currency-info", "--currency", "UNKNOWN"], "Информация о неизвестной валюте")

    print("\n2. Регистрация и аутентификация (с логированием)")
    print("=" * 40)

    run_command(["register", "--username", "trader1", "--password", "pass123"], "Регистрация пользователя")
    run_command(["register", "--username", "trader1", "--password", "pass123"], "Повторная регистрация (ошибка)")
    run_command(["login", "--username", "trader1", "--password", "wrongpass"], "Неверный пароль")
    run_command(["login", "--username", "trader1", "--password", "pass123"], "Успешный вход")

    print("\n3. Операции с портфелем (с транзакциями)")
    print("=" * 40)

    run_command(["buy", "--currency", "USD", "--amount", "5000"], "Покупка USD")
    run_command(["buy", "--currency", "BTC", "--amount", "0.1"], "Покупка BTC")
    run_command(["buy", "--currency", "ETH", "--amount", "2.5"], "Покупка ETH")
    run_command(["show-portfolio"], "Портфель в USD")
    run_command(["show-portfolio", "--base", "BTC"], "Портфель в BTC")

    print("\n4. Тестирование обработки ошибок баланса")
    print("=" * 40)

    run_command(["sell", "--currency", "BTC", "--amount", "1.0"], "Продажа больше чем есть")
    run_command(["sell", "--currency", "BTC", "--amount", "0.05"], "Успешная продажа")
    run_command(["show-portfolio"], "Обновленный портфель")

    print("\n5. Работа с курсами валют (валидация)")
    print("=" * 40)

    run_command(["get-rate", "--from", "USD", "--to", "EUR"], "Курс USD/EUR")
    run_command(["get-rate", "--from", "BTC", "--to", "ETH"], "Курс BTC/ETH")
    run_command(["list-currencies"], "Список всех валют")

    print("\n6. Завершение работы")
    print("=" * 40)

    run_command(["logout"], "Выход из системы")
    run_command(["whoami"], "Проверка сессии")

    print("\n" + "=" * 60)
    print("🎉 ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА!")
    print("\n📊 СИСТЕМА ВКЛЮЧАЕТ:")
    print("   ✅ Улучшенное логирование с ротацией и форматами")
    print("   ✅ Детализированные исключения с контекстом")
    print("   ✅ Потокобезопасные синглтоны")
    print("   ✅ Транзакции базы данных с бэкапами")
    print("   ✅ Декораторы для валидации и аутентификации")
    print("   ✅ Комплексная обработка ошибок")
    print("\n📝 Логи сохранены в logs/valutatrade.log")
    print("💾 Бэкапы созданы в backups/")
    print("🗄️  Данные сохранены в data/")


if __name__ == "__main__":
    main()
