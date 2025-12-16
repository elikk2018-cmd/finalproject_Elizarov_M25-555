"""Utility helpers (validation + parsing)."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation


def normalize_currency_code(code: str) -> str:
    """Validate and normalize currency code.

    Rules:
    - Non-empty string
    - Uppercase
    - Length 2..5
    - No spaces

    Args:
        code: Raw currency code from user input.

    Returns:
        Normalized uppercase currency code.

    Raises:
        ValueError: If code is invalid.
    """
    if not isinstance(code, str) or not code.strip():
        raise ValueError("currency_code должен быть непустой строкой")

    norm = code.strip().upper()
    if " " in norm or not (2 <= len(norm) <= 5):
        raise ValueError("currency_code должен быть 2–5 символов, без пробелов, UPPER")
    return norm


def parse_positive_decimal(value: str | int | float | Decimal) -> Decimal:
    """Parse amount as positive Decimal.

    Args:
        value: Input value (string/number).

    Returns:
        Decimal amount > 0.

    Raises:
        ValueError: If cannot parse or non-positive.
    """
    try:
        amount = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, TypeError) as e:
        raise ValueError("'amount' должен быть положительным числом") from e

    if amount <= 0:
        raise ValueError("'amount' должен быть положительным числом")
    return amount
