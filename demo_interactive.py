#!/usr/bin/env python3
"""Демонстрационный сценарий для интерактивного режима"""

import os
import subprocess
import sys
import time


def run_interactive_commands(commands):
    """Run commands in interactive mode using subprocess with input."""

    # Clean previous data
    if os.path.exists("data/users.json"):
        os.remove("data/users.json")
    if os.path.exists("data/portfolios.json"):
        os.remove("data/portfolios.json")

    print("ЗАПУСК ИНТЕРАКТИВНОЙ ДЕМОНСТРАЦИИ")
    print("=" * 50)

    # Start interactive process
    process = subprocess.Popen(
        [sys.executable, "main.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )

    try:
        for command in commands:
            print(f"\n>>> {command}")
            process.stdin.write(command + '\n')
            process.stdin.flush()

            # Read output
            output = []
            while True:
                line = process.stdout.readline()
                if not line:
                    break
                if 'valutatrade' in line and '>' in line:
                    break  # Stop at next prompt
                output.append(line.strip())

            # Print output
            for line in output:
                if line and '==================================================' not in line:
                    print(f"   {line}")

            time.sleep(0.5)

        # Exit
        process.stdin.write('exit\n')
        process.stdin.flush()

    finally:
        process.terminate()
        process.wait()


def main():
    """Run interactive demo."""
    commands = [
        "register --username alice --password 1234",
        "login --username alice --password 1234",
        "whoami",
        "get_rate --from USD --to BTC",
        "get_rate --from USD --to EUR",
        "buy --currency USD --amount 1000",
        "buy --currency BTC --amount 0.1",
        "buy --currency EUR --amount 500",
        "show_portfolio",
        "show_portfolio --base EUR",
        "sell --currency BTC --amount 0.02",
        "show_portfolio",
        "logout",
        "exit"
    ]

    run_interactive_commands(commands)

    print("\n" + "=" * 50)
    print("ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА!")
    print("\nДля интерактивного режима используйте:")
    print("   python main.py")
    print("   python main.py --interactive")


if __name__ == "__main__":
    main()
