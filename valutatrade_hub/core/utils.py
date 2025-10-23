"""Utility functions and helpers."""
import hashlib
import secrets
import string
from datetime import datetime


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
    """Validate currency code format."""
    return bool(currency_code and currency_code.isalpha() and 2 <= len(currency_code) <= 5)


def get_current_datetime() -> str:
    """Get current datetime in ISO format."""
    return datetime.now().isoformat()


def format_currency_amount(amount: float, currency_code: str) -> str:
    """Format currency amount for display."""
    return f"{amount:.4f} {currency_code}"


class ExchangeRates:
    """Temporary exchange rates stub until Parser Service is implemented."""
    
    _rates = {
        "EUR_USD": 1.0786,
        "BTC_USD": 59337.21,
        "RUB_USD": 0.01016,
        "ETH_USD": 3720.00,
        "USD_USD": 1.0,
    }
    
    @classmethod
    def get_rate(cls, from_currency: str, to_currency: str) -> float:
        """Get exchange rate between two currencies."""
        if from_currency == to_currency:
            return 1.0
            
        pair = f"{from_currency}_{to_currency}"
        if pair in cls._rates:
            return cls._rates[pair]
            
        # Try reverse rate
        reverse_pair = f"{to_currency}_{from_currency}"
        if reverse_pair in cls._rates:
            return 1.0 / cls._rates[reverse_pair]
            
        raise CurrencyNotFoundError(f"{from_currency}/{to_currency}")
