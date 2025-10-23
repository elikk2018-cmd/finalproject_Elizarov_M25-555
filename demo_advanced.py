#!/usr/bin/env python3
"""Демонстрация расширенных возможностей"""

import os
import subprocess
import sys


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
    
    return result.returncode == 0


def main():
    """Run advanced features demo."""
    print("🚀 ДЕМОНСТРАЦИЯ РАСШИРЕННЫХ ВОЗМОЖНОСТЕЙ")
    print("=" * 60)
    
    # Clean previous data
    if os.path.exists("data/users.json"):
        os.remove("data/users.json")
    if os.path.exists("data/portfolios.json"):
        os.remove("data/portfolios.json")
    
    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)
    
    print("\n1. Работа с системой валют")
    print("=" * 40)
    
    run_command(["list-currencies"], "Список всех доступных валют")
    run_command(["currency-info", "--currency", "USD"], "Информация о USD")
    run_command(["currency-info", "--currency", "BTC"], "Информация о BTC")
    run_command(["currency-info", "--currency", "EUR"], "Информация о EUR")
    
    print("\n2. Получение курсов с валидацией валют")
    print("=" * 40)
    
    run_command(["get-rate", "--from", "USD", "--to", "BTC"], "Курс USD/BTC")
    run_command(["get-rate", "--from", "EUR", "--to", "BTC"], "Курс EUR/BTC")
    run_command(["get-rate", "--from", "BTC", "--to", "ETH"], "Курс BTC/ETH")
    
    print("\n3. Работа с пользователем (с логированием)")
    print("=" * 40)
    
    run_command(["register", "--username", "advanced", "--password", "adv123"], "Регистрация")
    run_command(["login", "--username", "advanced", "--password", "adv123"], "Вход")
    run_command(["whoami"], "Информация о пользователе")
    
    print("\n4. Операции с валютами (с проверкой валют)")
    print("=" * 40)
    
    run_command(["buy", "--currency", "USD", "--amount", "2000"], "Покупка USD")
    run_command(["buy", "--currency", "BTC", "--amount", "0.05"], "Покупка BTC")
    run_command(["buy", "--currency", "ETH", "--amount", "0.5"], "Покупка ETH")
    run_command(["show-portfolio"], "Портфель в USD")
    run_command(["show-portfolio", "--base", "BTC"], "Портфель в BTC")
    
    print("\n5. Проверка обработки ошибок")
    print("=" * 40)
    
    run_command(["get-rate", "--from", "USD", "--to", "XYZ"], "Неизвестная валюта")
    run_command(["buy", "--currency", "XYZ", "--amount", "100"], "Покупка неизвестной валюты")
    run_command(["sell", "--currency", "BTC", "--amount", "1"], "Продажа больше чем есть")
    
    print("\n6. Завершение работы")
    print("=" * 40)
    
    run_command(["logout"], "Выход из системы")
    
    print("\n" + "=" * 60)
    print("🎉 ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА!")
    print("\n📝 Логи операций сохранены в logs/valutatrade.log")
    print("💡 Проверьте файл логов для просмотра записанных операций")


if __name__ == "__main__":
    main()
