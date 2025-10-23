#!/usr/bin/env python3
"""Тестовый скрипт для проверки CLI интерфейса"""

import os
import subprocess
import sys


def run_command(command):
    """Run a CLI command and return result."""
    try:
        result = subprocess.run(
            [sys.executable, "main.py"] + command,
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"


def test_cli_commands():
    """Test all CLI commands."""
    print("🚀 ТЕСТИРОВАНИЕ CLI ИНТЕРФЕЙСА")
    print("=" * 50)

    # Cleanup test data
    if os.path.exists("data/users.json"):
        os.remove("data/users.json")
    if os.path.exists("data/portfolios.json"):
        os.remove("data/portfolios.json")

    # Test 1: Help command
    print("\n1. Testing help command...")
    returncode, stdout, stderr = run_command(["--help"])
    if returncode == 0 and "Команды" in stdout:
        print("   ✅ Help command works")
    else:
        print("   ❌ Help command failed")

    # Test 2: Register user
    print("\n2. Testing user registration...")
    returncode, stdout, stderr = run_command(["register", "--username", "testuser", "--password", "testpass"])
    if returncode == 0 and "зарегистрирован" in stdout:
        print("   ✅ User registration works")
    else:
        print("   ❌ User registration failed")
        print(f"      stdout: {stdout}")
        print(f"      stderr: {stderr}")

    # Test 3: Login
    print("\n3. Testing user login...")
    returncode, stdout, stderr = run_command(["login", "--username", "testuser", "--password", "testpass"])
    if returncode == 0 and "вошли" in stdout:
        print("   ✅ User login works")
    else:
        print("   ❌ User login failed")
        print(f"      stdout: {stdout}")
        print(f"      stderr: {stderr}")

    # Test 4: Whoami command
    print("\n4. Testing whoami command...")
    returncode, stdout, stderr = run_command(["whoami"])
    if returncode == 0 and "testuser" in stdout:
        print("   ✅ Whoami command works")
    else:
        print("   ❌ Whoami command failed")

    # Test 5: Get rate command
    print("\n5. Testing get-rate command...")
    returncode, stdout, stderr = run_command(["get-rate", "--from", "USD", "--to", "BTC"])
    if returncode == 0 and "Курс" in stdout:
        print("   ✅ Get-rate command works")
    else:
        print("   ❌ Get-rate command failed")

    # Test 6: Buy command
    print("\n6. Testing buy command...")
    returncode, stdout, stderr = run_command(["buy", "--currency", "BTC", "--amount", "0.1"])
    if returncode == 0 and "Покупка выполнена" in stdout:
        print("   ✅ Buy command works")
    else:
        print("   ❌ Buy command failed")
        print(f"      stdout: {stdout}")
        print(f"      stderr: {stderr}")

    # Test 7: Show portfolio command
    print("\n7. Testing show-portfolio command...")
    returncode, stdout, stderr = run_command(["show-portfolio"])
    if returncode == 0 and "Портфель" in stdout:
        print("   ✅ Show-portfolio command works")
    else:
        print("   ❌ Show-portfolio command failed")

    # Test 8: Logout command
    print("\n8. Testing logout command...")
    returncode, stdout, stderr = run_command(["logout"])
    if returncode == 0 and "вышли" in stdout:
        print("   ✅ Logout command works")
    else:
        print("   ❌ Logout command failed")

    print("\n" + "=" * 50)
    print("🎯 ТЕСТИРОВАНИЕ CLI ЗАВЕРШЕНО")


if __name__ == "__main__":
    test_cli_commands()
