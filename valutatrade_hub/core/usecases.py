"""Business logic use cases."""
import json
import os
from typing import Optional, List
from .models import User, Wallet, Portfolio
from .exceptions import UserNotFoundError, AuthenticationError, CurrencyNotFoundError
from .utils import validate_username, validate_password, validate_currency_code, hash_password, generate_salt


class UserManager:
    """Manager for user-related operations."""
    
    def __init__(self, users_file: str = "data/users.json"):
        self.users_file = users_file
        self._ensure_data_file()
    
    def _ensure_data_file(self):
        """Ensure data file and directory exist."""
        os.makedirs(os.path.dirname(self.users_file), exist_ok=True)
        if not os.path.exists(self.users_file):
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump([], f)
    
    def _load_users(self) -> List[dict]:
        """Load users from JSON file."""
        try:
            with open(self.users_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _save_users(self, users_data: List[dict]):
        """Save users to JSON file."""
        with open(self.users_file, 'w', encoding='utf-8') as f:
            json.dump(users_data, f, indent=2, ensure_ascii=False)
    
    def _get_next_user_id(self) -> int:
        """Get next available user ID."""
        users = self._load_users()
        if not users:
            return 1
        return max(user["user_id"] for user in users) + 1
    
    def register_user(self, username: str, password: str) -> User:
        """Register a new user."""
        if not validate_username(username):
            raise ValueError("Имя пользователя должно содержать не менее 3 символов и состоять из букв и цифр")
        
        if not validate_password(password):
            raise ValueError("Пароль должен быть не короче 4 символов")
        
        # Check if username already exists
        users = self._load_users()
        if any(user["username"] == username for user in users):
            raise ValueError(f"Имя пользователя '{username}' уже занято")
        
        # Create new user
        user_id = self._get_next_user_id()
        salt = generate_salt()
        hashed_password = hash_password(password, salt)
        
        user = User(
            user_id=user_id,
            username=username,
            hashed_password=hashed_password,
            salt=salt
        )
        
        # Save user
        users.append(user.to_dict())
        self._save_users(users)
        
        return user
    
    def authenticate_user(self, username: str, password: str) -> User:
        """Authenticate user and return User object if successful."""
        users = self._load_users()
        
        for user_data in users:
            if user_data["username"] == username:
                user = User.from_dict(user_data)
                if user.verify_password(password):
                    return user
                else:
                    raise AuthenticationError("Неверный пароль")
        
        raise UserNotFoundError(username=username)
    
    def get_user_by_id(self, user_id: int) -> User:
        """Get user by ID."""
        users = self._load_users()
        
        for user_data in users:
            if user_data["user_id"] == user_id:
                return User.from_dict(user_data)
        
        raise UserNotFoundError(user_id=user_id)


class PortfolioManager:
    """Manager for portfolio-related operations."""
    
    def __init__(self, portfolios_file: str = "data/portfolios.json"):
        self.portfolios_file = portfolios_file
        self._ensure_data_file()
    
    def _ensure_data_file(self):
        """Ensure data file and directory exist."""
        os.makedirs(os.path.dirname(self.portfolios_file), exist_ok=True)
        if not os.path.exists(self.portfolios_file):
            with open(self.portfolios_file, 'w', encoding='utf-8') as f:
                json.dump([], f)
    
    def _load_portfolios(self) -> List[dict]:
        """Load portfolios from JSON file."""
        try:
            with open(self.portfolios_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _save_portfolios(self, portfolios_data: List[dict]):
        """Save portfolios to JSON file."""
        with open(self.portfolios_file, 'w', encoding='utf-8') as f:
            json.dump(portfolios_data, f, indent=2, ensure_ascii=False)
    
    def get_user_portfolio(self, user_id: int) -> Portfolio:
        """Get user's portfolio."""
        portfolios = self._load_portfolios()
        
        for portfolio_data in portfolios:
            if portfolio_data["user_id"] == user_id:
                return Portfolio.from_dict(portfolio_data)
        
        # Create empty portfolio if not exists
        portfolio = Portfolio(user_id)
        self._save_user_portfolio(portfolio)
        return portfolio
    
    def _save_user_portfolio(self, portfolio: Portfolio):
        """Save user portfolio."""
        portfolios = self._load_portfolios()
        
        # Remove existing portfolio for this user
        portfolios = [p for p in portfolios if p["user_id"] != portfolio.user_id]
        
        # Add updated portfolio
        portfolios.append(portfolio.to_dict())
        self._save_portfolios(portfolios)
    
    def add_currency_to_portfolio(self, user_id: int, currency_code: str) -> Wallet:
        """Add currency to user's portfolio."""
        if not validate_currency_code(currency_code):
            raise ValueError("Некорректный код валюты")
        
        portfolio = self.get_user_portfolio(user_id)
        wallet = portfolio.add_currency(currency_code)
        self._save_user_portfolio(portfolio)
        return wallet
    
    def deposit_to_wallet(self, user_id: int, currency_code: str, amount: float):
        """Deposit funds to user's wallet."""
        if amount <= 0:
            raise ValueError("Сумма пополнения должна быть положительной")
        
        portfolio = self.get_user_portfolio(user_id)
        
        # Create wallet if it doesn't exist
        if currency_code not in portfolio.wallets:
            portfolio.add_currency(currency_code)
        
        wallet = portfolio.get_wallet(currency_code)
        wallet.deposit(amount)
        self._save_user_portfolio(portfolio)
    
    def withdraw_from_wallet(self, user_id: int, currency_code: str, amount: float):
        """Withdraw funds from user's wallet."""
        if amount <= 0:
            raise ValueError("Сумма снятия должна быть положительной")
        
        portfolio = self.get_user_portfolio(user_id)
        wallet = portfolio.get_wallet(currency_code)
        wallet.withdraw(amount)
        self._save_user_portfolio(portfolio)


# Global instances for easy access
user_manager = UserManager()
portfolio_manager = PortfolioManager()
