"""Utility functions and helpers with currency integration."""
import hashlib
import secrets
import string
from datetime import datetime

from .currencies import get_currency
from .exceptions import CurrencyNotFoundError


def generate_salt(length: int = 16) -> str:
    """Generate a random salt for password hashing."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def hash_password(password: str, salt: str) -> str:
    """Hash password with salt using SHA-256."""
    return hashlib.sha256((password + salt).encode()).hexdigest()


def validate_username(username: str) -> bool:
    """Validate username format."""
    return bool(username and len(username.strip()) >= 3 and ' ' not in username)


def validate_password(password: str) -> bool:
    """Validate password meets minimum requirements."""
    return bool(password and len(password) >= 4)


def validate_currency_code(currency_code: str) -> bool:
    """Validate currency code format using currency registry."""
    try:
        get_currency(currency_code)
        return True
    except CurrencyNotFoundError:
        return False


def get_current_datetime() -> str:
    """Get current datetime in ISO format."""
    return datetime.now().isoformat()


def format_currency_amount(amount: float, currency_code: str) -> str:
    """Format currency amount for display."""
    try:
        currency = get_currency(currency_code)
        # Different formatting for crypto vs fiat
        if hasattr(currency, 'algorithm'):  # Crypto
            return f"{amount:.8f} {currency_code}"
        else:  # Fiat
            return f"{amount:.2f} {currency_code}"
    except CurrencyNotFoundError:
        return f"{amount:.2f} {currency_code}"


class ExchangeRates:
    """Temporary exchange rates stub with currency validation."""

    _rates = {
        # Fiat to USD
        "EUR_USD": 1.0786,
        "GBP_USD": 1.2591,
        "RUB_USD": 0.01016,
        "JPY_USD": 0.0067,
        "CNY_USD": 0.1389,
        "USD_USD": 1.0,

        # Crypto to USD
        "BTC_USD": 59337.21,
        "ETH_USD": 3720.00,
        "SOL_USD": 145.12,
        "ADA_USD": 0.45,
        "DOT_USD": 8.20,

        # Cross rates (calculated)
        "EUR_BTC": 0.00001817,
        "BTC_EUR": 55027.42,
    }

    @classmethod
    def get_rate(cls, from_currency: str, to_currency: str) -> float:
        """Get exchange rate between two currencies with validation."""
        # Validate currencies
        get_currency(from_currency)
        get_currency(to_currency)

        if from_currency == to_currency:
            return 1.0

        pair = f"{from_currency}_{to_currency}"
        if pair in cls._rates:
            return cls._rates[pair]

        # Try reverse rate
        reverse_pair = f"{to_currency}_{from_currency}"
        if reverse_pair in cls._rates:
            return 1.0 / cls._rates[reverse_pair]

        # Calculate through USD if possible
        if from_currency != "USD" and to_currency != "USD":
            try:
                rate_to_usd = cls.get_rate(from_currency, "USD")
                rate_from_usd = cls.get_rate("USD", to_currency)
                return rate_to_usd * rate_from_usd
            except CurrencyNotFoundError:
                pass

        raise CurrencyNotFoundError(f"Курс для пары {from_currency}/{to_currency} не найден")

    @classmethod
    def add_rate(cls, from_currency: str, to_currency: str, rate: float):
        """Add or update exchange rate."""
        pair = f"{from_currency}_{to_currency}"
        cls._rates[pair] = float(rate)
