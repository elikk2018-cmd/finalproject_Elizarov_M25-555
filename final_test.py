#!/usr/bin/env python3
"""Финальное тестирование всех функций ValutaTrade Hub"""

import os
import subprocess
import sys


def cleanup():
    """Очистка тестовых данных"""
    if os.path.exists("data/users.json"):
        os.remove("data/users.json")
    if os.path.exists("data/portfolios.json"):
        os.remove("data/portfolios.json")
    print("✅ Тестовые данные очищены")


def test_single_commands():
    """Тестирование одиночных команд"""
    print("\n=== ТЕСТИРОВАНИЕ ОДИНОЧНЫХ КОМАНД ===")
    
    # 1. Регистрация
    print("\n1. Регистрация пользователя")
    result = subprocess.run(
        [sys.executable, "main.py", "register", "--username", "demo", "--password", "demo123"],
        capture_output=True, text=True
    )
    if "УСПЕХ" in result.stdout:
        print("   ✅ Регистрация работает")
    else:
        print("   ❌ Регистрация не работает")
        print(f"   Вывод: {result.stdout}")
    
    # 2. Получение курса
    print("\n2. Получение курса валют")
    result = subprocess.run(
        [sys.executable, "main.py", "get-rate", "--from", "USD", "--to", "EUR"],
        capture_output=True, text=True
    )
    if "КУРС" in result.stdout:
        print("   ✅ Получение курса работает")
    else:
        print("   ❌ Получение курса не работает")
    
    # 3. Вход (сессия не сохранится)
    print("\n3. Вход в систему (сессия не сохраняется между вызовами)")
    result = subprocess.run(
        [sys.executable, "main.py", "login", "--username", "demo", "--password", "demo123"],
        capture_output=True, text=True
    )
    if "УСПЕХ" in result.stdout:
        print("   ✅ Вход работает (но сессия теряется)")
    else:
        print("   ❌ Вход не работает")


def test_interactive_flow():
    """Тестирование полного потока в интерактивном режиме"""
    print("\n=== ТЕСТИРОВАНИЕ ИНТЕРАКТИВНОГО РЕЖИМА ===")
    
    commands = [
        "register --username trader --password trade123",
        "login --username trader --password trade123",
        "whoami",
        "get_rate --from USD --to BTC",
        "buy --currency USD --amount 1500",
        "buy --currency BTC --amount 0.05", 
        "buy --currency EUR --amount 800",
        "show_portfolio",
        "sell --currency BTC --amount 0.01",
        "show_portfolio --base EUR",
        "logout",
        "exit"
    ]
    
    process = subprocess.Popen(
        [sys.executable, "main.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    try:
        success_steps = 0
        total_steps = len(commands)
        
        for i, cmd in enumerate(commands, 1):
            print(f"\n{i}/{total_steps}. {cmd}")
            process.stdin.write(cmd + '\n')
            process.stdin.flush()
            
            # Читаем вывод
            output = []
            while True:
                line = process.stdout.readline()
                if not line:
                    break
                if 'valutatrade' in line and '>' in line:
                    break
                if line.strip():
                    output.append(line.strip())
            
            # Проверяем успешность
            output_text = '\n'.join(output)
            if any(success in output_text for success in ['УСПЕХ', 'ПОРТФЕЛЬ', 'ТЕКУЩИЙ', 'КУРС']):
                success_steps += 1
                print("   ✅ Успех")
            else:
                print("   ❌ Проблема")
            
            # Выводим релевантные строки
            for line in output:
                if any(keyword in line for keyword in ['УСПЕХ', 'ОШИБКА', 'ПОРТФЕЛЬ', 'КУРС', 'ТЕКУЩИЙ']):
                    print(f"      {line}")
        
        print(f"\n📊 Результат: {success_steps}/{total_steps} шагов выполнено успешно")
        
    except Exception as e:
        print(f"Ошибка тестирования: {e}")
    finally:
        process.terminate()


def check_data_files():
    """Проверка целостности данных"""
    print("\n=== ПРОВЕРКА ФАЙЛОВ ДАННЫХ ===")
    
    try:
        import json
        
        if os.path.exists("data/users.json"):
            with open("data/users.json", "r") as f:
                users = json.load(f)
            print(f"✅ users.json: {len(users)} пользователь(ей)")
            for user in users:
                print(f"   - {user['username']} (id: {user['user_id']})")
        
        if os.path.exists("data/portfolios.json"):
            with open("data/portfolios.json", "r") as f:
                portfolios = json.load(f)
            print(f"✅ portfolios.json: {len(portfolios)} портфель(ей)")
            for portfolio in portfolios:
                print(f"   - Пользователь {portfolio['user_id']}: {len(portfolio['wallets'])} кошельков")
        
    except Exception as e:
        print(f"❌ Ошибка проверки данных: {e}")


def main():
    """Основная функция тестирования"""
    print("🚀 ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ VALUTATRADE HUB")
    print("=" * 50)
    
    # Очищаем данные
    cleanup()
    
    # Запускаем тесты
    test_single_commands()
    test_interactive_flow() 
    check_data_files()
    
    print("\n" + "=" * 50)
    print("🎯 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("\n💡 Рекомендации по использованию:")
    print("   • Для интерактивной работы: python main.py")
    print("   • Для одиночных команд: python main.py <команда>")
    print("   • Сессия сохраняется только в интерактивном режиме")


if __name__ == "__main__":
    main()
