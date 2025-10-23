#!/usr/bin/env python3
"""
ValutaTrade Hub - Main entry point
Currency trading simulation platform
"""
import sys

from valutatrade_hub.cli.interactive import run_interactive
from valutatrade_hub.cli.interface import CLI


def main():
    """Основная функция приложения."""
    if len(sys.argv) == 1:
        # No arguments provided, start interactive mode
        run_interactive()
    elif len(sys.argv) == 2 and sys.argv[1] in ['-i', '--interactive']:
        # Explicit interactive mode
        run_interactive()
    else:
        # Arguments provided, use single-command CLI
        cli = CLI()
        cli.run()


if __name__ == "__main__":
    main()
