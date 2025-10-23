#!/usr/bin/env python3
"""Простой тест интерактивного режима"""

import os
import subprocess
import sys

def test_interactive():
    print("ТЕСТ ИНТЕРАКТИВНОГО РЕЖИМА")
    print("=" * 40)
    
    # Очищаем данные
    if os.path.exists("data/users.json"):
        os.remove("data/users.json")
    if os.path.exists("data/portfolios.json"):
        os.remove("data/portfolios.json")
    
    # Команды для тестирования
    commands = [
        "register --username test --password test123",
        "login --username test --password test123", 
        "whoami",
        "get_rate --from USD --to BTC",
        "buy --currency USD --amount 100",
        "show_portfolio",
        "logout",
        "exit"
    ]
    
    # Запускаем интерактивный режим
    process = subprocess.Popen(
        [sys.executable, "main.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    try:
        output_lines = []
        
        for cmd in commands:
            process.stdin.write(cmd + '\n')
            process.stdin.flush()
            
            # Читаем вывод до следующего промпта
            while True:
                line = process.stdout.readline()
                if not line:
                    break
                output_lines.append(line.strip())
                if 'valutatrade' in line and '>' in line:
                    break
        
        # Завершаем процесс
        process.stdin.write('exit\n')
        process.stdin.flush()
        process.wait()
        
        # Анализируем вывод
        output = '\n'.join(output_lines)
        success_count = 0
        
        if "УСПЕХ: Пользователь 'test' зарегистрирован" in output:
            print("✅ Регистрация работает")
            success_count += 1
        else:
            print("❌ Регистрация не работает")
        
        if "УСПЕХ: Вы вошли как 'test'" in output:
            print("✅ Вход работает") 
            success_count += 1
        else:
            print("❌ Вход не работает")
        
        if "КУРС USD -> BTC:" in output:
            print("✅ Получение курса работает")
            success_count += 1
        else:
            print("❌ Получение курса не работает")
        
        if "Покупка выполнена" in output:
            print("✅ Покупка работает")
            success_count += 1
        else:
            print("❌ Покупка не работает")
        
        if "ПОРТФЕЛЬ" in output:
            print("✅ Портфель работает")
            success_count += 1
        else:
            print("❌ Портфель не работает")
        
        print(f"\nРЕЗУЛЬТАТ: {success_count}/5 тестов пройдено")
        
    except Exception as e:
        print(f"ОШИБКА ТЕСТИРОВАНИЯ: {e}")
    finally:
        process.terminate()

if __name__ == "__main__":
    test_interactive()
