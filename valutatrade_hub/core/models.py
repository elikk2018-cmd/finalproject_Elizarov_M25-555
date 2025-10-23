"""Data models for users, wallets, and portfolios."""
from datetime import datetime
from typing import Dict
from .exceptions import InsufficientFundsError
from .utils import hash_password, generate_salt, get_current_datetime, ExchangeRates


class User:
    """User model representing a system user."""
    
    def __init__(self, user_id: int, username: str, hashed_password: str, 
                 salt: str, registration_date: str = None):
        self._user_id = user_id
        self._username = username
        self._hashed_password = hashed_password
        self._salt = salt
        self._registration_date = registration_date or get_current_datetime()
    
    @property
    def user_id(self) -> int:
        return self._user_id
    
    @property
    def username(self) -> str:
        return self._username
    
    @username.setter
    def username(self, value: str):
        if not value or len(value.strip()) == 0:
            raise ValueError("Имя пользователя не может быть пустым")
        self._username = value
    
    @property
    def hashed_password(self) -> str:
        return self._hashed_password
    
    @property
    def salt(self) -> str:
        return self._salt
    
    @property
    def registration_date(self) -> str:
        return self._registration_date
    
    def get_user_info(self) -> dict:
        """Get user information (without password)."""
        return {
            "user_id": self._user_id,
            "username": self._username,
            "registration_date": self._registration_date
        }
    
    def change_password(self, new_password: str):
        """Change user password with new hashing."""
        if len(new_password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов")
        
        new_salt = generate_salt()
        new_hashed_password = hash_password(new_password, new_salt)
        
        self._hashed_password = new_hashed_password
        self._salt = new_salt
    
    def verify_password(self, password: str) -> bool:
        """Verify if provided password matches stored hash."""
        test_hash = hash_password(password, self._salt)
        return test_hash == self._hashed_password
    
    def to_dict(self) -> dict:
        """Convert user to dictionary for JSON storage."""
        return {
            "user_id": self._user_id,
            "username": self._username,
            "hashed_password": self._hashed_password,
            "salt": self._salt,
            "registration_date": self._registration_date
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        """Create User instance from dictionary."""
        return cls(
            user_id=data["user_id"],
            username=data["username"],
            hashed_password=data["hashed_password"],
            salt=data["salt"],
            registration_date=data["registration_date"]
        )


class Wallet:
    """Wallet model for managing a single currency balance."""
    
    def __init__(self, currency_code: str, balance: float = 0.0):
        self.currency_code = currency_code.upper()
        self._balance = float(balance)
    
    @property
    def balance(self) -> float:
        return self._balance
    
    @balance.setter
    def balance(self, value: float):
        if not isinstance(value, (int, float)):
            raise TypeError("Баланс должен быть числом")
        if value < 0:
            raise ValueError("Баланс не может быть отрицательным")
        self._balance = float(value)
    
    def deposit(self, amount: float):
        """Deposit funds into wallet."""
        if amount <= 0:
            raise ValueError("Сумма пополнения должна быть положительной")
        self.balance += amount
    
    def withdraw(self, amount: float):
        """Withdraw funds from wallet."""
        if amount <= 0:
            raise ValueError("Сумма снятия должна быть положительной")
        if amount > self._balance:
            raise InsufficientFundsError(
                available=self._balance,
                required=amount,
                currency_code=self.currency_code
            )
        self.balance -= amount
    
    def get_balance_info(self) -> dict:
        """Get wallet balance information."""
        return {
            "currency_code": self.currency_code,
            "balance": self._balance
        }
    
    def to_dict(self) -> dict:
        """Convert wallet to dictionary for JSON storage."""
        return {
            "currency_code": self.currency_code,
            "balance": self._balance
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Wallet':
        """Create Wallet instance from dictionary."""
        return cls(
            currency_code=data["currency_code"],
            balance=data["balance"]
        )


class Portfolio:
    """Portfolio model for managing all user wallets."""
    
    def __init__(self, user_id: int, wallets: Dict[str, Wallet] = None):
        self._user_id = user_id
        self._wallets = wallets or {}
    
    @property
    def user_id(self) -> int:
        return self._user_id
    
    @property
    def wallets(self) -> Dict[str, Wallet]:
        return self._wallets.copy()  # Return copy to prevent external modification
    
    def add_currency(self, currency_code: str) -> Wallet:
        """Add new currency wallet to portfolio."""
        currency_code = currency_code.upper()
        if currency_code in self._wallets:
            raise ValueError(f"Валюта '{currency_code}' уже есть в портфеле")
        
        wallet = Wallet(currency_code)
        self._wallets[currency_code] = wallet
        return wallet
    
    def get_wallet(self, currency_code: str) -> Wallet:
        """Get wallet by currency code."""
        currency_code = currency_code.upper()
        if currency_code not in self._wallets:
            raise ValueError(f"Кошелек для валюты '{currency_code}' не найден")
        return self._wallets[currency_code]
    
    def get_total_value(self, base_currency: str = 'USD') -> float:
        """Calculate total portfolio value in base currency."""
        total_value = 0.0
        
        for currency_code, wallet in self._wallets.items():
            if currency_code == base_currency:
                total_value += wallet.balance
            else:
                try:
                    rate = ExchangeRates.get_rate(currency_code, base_currency)
                    total_value += wallet.balance * rate
                except Exception:
                    # If rate not available, skip this currency
                    continue
        
        return total_value
    
    def to_dict(self) -> dict:
        """Convert portfolio to dictionary for JSON storage."""
        wallets_dict = {}
        for currency_code, wallet in self._wallets.items():
            wallets_dict[currency_code] = wallet.to_dict()
        
        return {
            "user_id": self._user_id,
            "wallets": wallets_dict
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Portfolio':
        """Create Portfolio instance from dictionary."""
        wallets = {}
        for currency_code, wallet_data in data["wallets"].items():
            wallets[currency_code] = Wallet.from_dict(wallet_data)
        
        return cls(
            user_id=data["user_id"],
            wallets=wallets
        )
