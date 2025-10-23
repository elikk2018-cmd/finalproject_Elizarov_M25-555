#!/usr/bin/env python3
"""Демонстрационный сценарий использования CLI"""

import os
import subprocess
import sys
import time


def run_demo_command(command, description):
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
    
    time.sleep(1)  # Pause for readability
    return result.returncode == 0


def main():
    """Run CLI demo."""
    print("ДЕМОНСТРАЦИЯ CLI VALUTATRADE HUB")
    print("=" * 60)
    
    # Clean previous data
    if os.path.exists("data/users.json"):
        os.remove("data/users.json")
    if os.path.exists("data/portfolios.json"):
        os.remove("data/portfolios.json")
    
    print("\nСценарий: Полный цикл работы пользователя")
    print("=" * 60)
    
    # 1. Register
    run_demo_command(["register", "--username", "alice", "--password", "1234"], 
                    "Регистрация нового пользователя 'alice'")
    
    # 2. Login
    run_demo_command(["login", "--username", "alice", "--password", "1234"], 
                    "Вход пользователя 'alice' в систему")
    
    # 3. Check whoami
    run_demo_command(["whoami"], "Проверка текущего пользователя")
    
    # 4. Get exchange rates
    run_demo_command(["get-rate", "--from", "USD", "--to", "BTC"], "Получение курса USD/BTC")
    run_demo_command(["get-rate", "--from", "USD", "--to", "EUR"], "Получение курса USD/EUR")
    
    # 5. Buy currencies
    run_demo_command(["buy", "--currency", "USD", "--amount", "1000"], "Покупка 1000 USD")
    run_demo_command(["buy", "--currency", "BTC", "--amount", "0.1"], "Покупка 0.1 BTC")
    run_demo_command(["buy", "--currency", "EUR", "--amount", "500"], "Покупка 500 EUR")
    
    # 6. Show portfolio
    run_demo_command(["show-portfolio"], "Просмотр портфеля")
    run_demo_command(["show-portfolio", "--base", "EUR"], "Просмотр портфеля в EUR")
    
    # 7. Sell some currency
    run_demo_command(["sell", "--currency", "BTC", "--amount", "0.02"], "Продажа 0.02 BTC")
    
    # 8. Show updated portfolio
    run_demo_command(["show-portfolio"], "Просмотр обновленного портфеля")
    
    # 9. Logout
    run_demo_command(["logout"], "Выход из системы")
    
    print("\n" + "=" * 60)
    print("ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА!")
    print("\nДля продолжения работы используйте команды:")
    print("   python main.py --help")


if __name__ == "__main__":
    main()
