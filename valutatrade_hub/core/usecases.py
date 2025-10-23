"""Business logic use cases with enhanced features."""
from typing import Optional
from .models import User, Wallet, Portfolio
from .exceptions import UserNotFoundError, AuthenticationError, CurrencyNotFoundError, InsufficientFundsError
from .utils import validate_username, validate_password, hash_password, generate_salt
from .currencies import get_currency, CurrencyRegistry
from ..infra.database import db
from ..decorators import log_action


class UserManager:
    """Manager for user-related operations with logging."""
    
    def __init__(self):
        self.users_file = "users"
    
    @log_action(verbose=True)
    def register_user(self, username: str, password: str) -> User:
        """Register a new user with enhanced validation."""
        if not validate_username(username):
            raise ValueError("Имя пользователя должно содержать не менее 3 символов и состоять из букв и цифр")
        
        if not validate_password(password):
            raise ValueError("Пароль должен быть не короче 4 символов")
        
        # Check if username already exists
        existing_user = db.find_entity("users", "username", username)
        if existing_user:
            raise ValueError(f"Имя пользователя '{username}' уже занято")
        
        # Create new user
        users = db.read_data("users")
        user_id = max([user["user_id"] for user in users], default=0) + 1
        
        salt = generate_salt()
        hashed_password = hash_password(password, salt)
        
        user = User(
            user_id=user_id,
            username=username,
            hashed_password=hashed_password,
            salt=salt
        )
        
        # Save user
        db.update_entity("users", "user_id", user_id, user.to_dict())
        
        # Create empty portfolio for user
        portfolio = Portfolio(user_id)
        db.update_entity("portfolios", "user_id", user_id, portfolio.to_dict())
        
        return user
    
    @log_action()
    def authenticate_user(self, username: str, password: str) -> User:
        """Authenticate user with enhanced error handling."""
        user_data = db.find_entity("users", "username", username)
        if not user_data:
            raise UserNotFoundError(username=username)
        
        user = User.from_dict(user_data)
        if not user.verify_password(password):
            raise AuthenticationError("Неверный пароль")
        
        return user
    
    def get_user_by_id(self, user_id: int) -> User:
        """Get user by ID."""
        user_data = db.find_entity("users", "user_id", user_id)
        if not user_data:
            raise UserNotFoundError(user_id=user_id)
        
        return User.from_dict(user_data)


class PortfolioManager:
    """Manager for portfolio-related operations with currency validation."""
    
    def __init__(self):
        self.portfolios_file = "portfolios"
    
    def get_user_portfolio(self, user_id: int) -> Portfolio:
        """Get user's portfolio."""
        portfolio_data = db.find_entity("portfolios", "user_id", user_id)
        if not portfolio_data:
            # Create empty portfolio if not exists
            portfolio = Portfolio(user_id)
            db.update_entity("portfolios", "user_id", user_id, portfolio.to_dict())
            return portfolio
        
        return Portfolio.from_dict(portfolio_data)
    
    def _save_user_portfolio(self, portfolio: Portfolio):
        """Save user portfolio."""
        db.update_entity("portfolios", "user_id", portfolio.user_id, portfolio.to_dict())
    
    @log_action()
    def add_currency_to_portfolio(self, user_id: int, currency_code: str) -> Wallet:
        """Add currency to user's portfolio with currency validation."""
        # Validate currency exists
        currency = get_currency(currency_code)
        
        portfolio = self.get_user_portfolio(user_id)
        wallet = portfolio.add_currency(currency_code)
        self._save_user_portfolio(portfolio)
        
        print(f"Добавлена валюта: {currency.get_display_info()}")
        return wallet
    
    @log_action(verbose=True)
    def deposit_to_wallet(self, user_id: int, currency_code: str, amount: float):
        """Deposit funds to user's wallet with currency validation."""
        if amount <= 0:
            raise ValueError("Сумма пополнения должна быть положительной")
        
        # Validate currency exists
        get_currency(currency_code)
        
        portfolio = self.get_user_portfolio(user_id)
        
        # Create wallet if it doesn't exist
        if currency_code not in portfolio.wallets:
            portfolio.add_currency(currency_code)
        
        wallet = portfolio.get_wallet(currency_code)
        wallet.deposit(amount)
        self._save_user_portfolio(portfolio)
    
    @log_action(verbose=True)
    def withdraw_from_wallet(self, user_id: int, currency_code: str, amount: float):
        """Withdraw funds from user's wallet with enhanced error handling."""
        if amount <= 0:
            raise ValueError("Сумма снятия должна быть положительной")
        
        # Validate currency exists
        get_currency(currency_code)
        
        portfolio = self.get_user_portfolio(user_id)
        wallet = portfolio.get_wallet(currency_code)
        wallet.withdraw(amount)
        self._save_user_portfolio(portfolio)


class RateManager:
    """Manager for exchange rate operations."""
    
    def __init__(self):
        self.rates_file = "rates"
    
    @log_action()
    def get_exchange_rate(self, from_currency: str, to_currency: str) -> float:
        """Get exchange rate between two currencies with validation."""
        # Validate both currencies
        from_curr = get_currency(from_currency)
        to_curr = get_currency(to_currency)
        
        from .utils import ExchangeRates
        
        try:
            rate = ExchangeRates.get_rate(from_currency, to_currency)
            return rate
        except CurrencyNotFoundError:
            # Fallback to basic rate calculation for known currencies
            if from_currency == to_currency:
                return 1.0
            raise
    
    def get_currency_info(self, currency_code: str) -> str:
        """Get currency display information."""
        currency = get_currency(currency_code)
        return currency.get_display_info()


# Global instances for easy access
user_manager = UserManager()
portfolio_manager = PortfolioManager()
rate_manager = RateManager()
