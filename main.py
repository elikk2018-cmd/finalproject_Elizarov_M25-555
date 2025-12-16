"""Entry point for Poetry script `project`.

Poetry config uses:
[tool.poetry.scripts]
project = "main:main"
"""

from valutatrade_hub.cli.interface import main as cli_main


def main() -> None:
    """Run CLI application."""
    cli_main()


if __name__ == "__main__":
    main()
