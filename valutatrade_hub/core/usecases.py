"""Enhanced business logic with comprehensive logging and error handling."""
from ..decorators import log_action, require_authentication, validate_currency
from ..infra.database import db
from .currencies import CurrencyRegistry, get_currency
from .exceptions import (
    AuthenticationError,
    CurrencyNotFoundError,
    DatabaseError,
    InsufficientFundsError,
    UserNotFoundError,
    ValidationError,
)
from .models import Portfolio, User, Wallet
from .utils import generate_salt, hash_password, validate_password, validate_username


class UserManager:
    """Enhanced UserManager with comprehensive logging and validation."""

    def __init__(self):
        self.users_file = "users"

    @log_action(operation="USER_REGISTRATION", verbose=True)
    def register_user(self, username: str, password: str) -> User:
        """Register a new user with enhanced validation and logging."""
        # Validate inputs
        if not validate_username(username):
            raise ValidationError("username", username, "must be at least 3 characters and contain no spaces")

        if not validate_password(password):
            raise ValidationError("password", "***", "must be at least 4 characters")

        # Check if username already exists
        existing_user = db.find_entity("users", "username", username)
        if existing_user:
            raise ValidationError("username", username, "already exists")

        # Create new user in transaction
        try:
            with db.transaction() as transaction:
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
                transaction.add_operation({
                    'type': 'update',
                    'entity': 'users',
                    'key': 'user_id',
                    'value': user_id,
                    'data': user.to_dict()
                })

                # Create empty portfolio for user
                portfolio = Portfolio(user_id)
                transaction.add_operation({
                    'type': 'update',
                    'entity': 'portfolios',
                    'key': 'user_id',
                    'value': user_id,
                    'data': portfolio.to_dict()
                })

                transaction.commit()

            return user

        except Exception as e:
            raise DatabaseError("user_registration", "users", str(e))

    @log_action(operation="USER_LOGIN")
    def authenticate_user(self, username: str, password: str) -> User:
        """Authenticate user with enhanced error handling and logging."""
        user_data = db.find_entity("users", "username", username)
        if not user_data:
            raise UserNotFoundError(username=username)

        user = User.from_dict(user_data)
        if not user.verify_password(password):
            raise AuthenticationError("Неверный пароль")

        return user

    @log_action(operation="GET_USER_BY_ID")
    def get_user_by_id(self, user_id: int) -> User:
        """Get user by ID with logging."""
        user_data = db.find_entity("users", "user_id", user_id)
        if not user_data:
            raise UserNotFoundError(user_id=user_id)

        return User.from_dict(user_data)


class PortfolioManager:
    """Enhanced PortfolioManager with currency validation and transaction support."""

    def __init__(self):
        self.portfolios_file = "portfolios"

    @require_authentication
    def get_user_portfolio(self, user_id: int) -> Portfolio:
        """Get user's portfolio with authentication check."""
        portfolio_data = db.find_entity("portfolios", "user_id", user_id)
        if not portfolio_data:
            # Create empty portfolio if not exists
            portfolio = Portfolio(user_id)
            db.update_entity("portfolios", "user_id", user_id, portfolio.to_dict())
            return portfolio

        return Portfolio.from_dict(portfolio_data)

    def _save_user_portfolio(self, portfolio: Portfolio):
        """Save user portfolio with transaction support."""
        db.update_entity("portfolios", "user_id", portfolio.user_id, portfolio.to_dict())

    @log_action(operation="ADD_CURRENCY_TO_PORTFOLIO")
    @require_authentication
    @validate_currency('currency_code')
    def add_currency_to_portfolio(self, user_id: int, currency_code: str) -> Wallet:
        """Add currency to user's portfolio with comprehensive validation."""
        # Validate currency exists (handled by decorator)
        currency = get_currency(currency_code)

        portfolio = self.get_user_portfolio(user_id)
        wallet = portfolio.add_currency(currency_code)
        self._save_user_portfolio(portfolio)

        return wallet

    @log_action(operation="DEPOSIT_TO_WALLET", verbose=True)
    @require_authentication
    @validate_currency('currency_code')
    def deposit_to_wallet(self, user_id: int, currency_code: str, amount: float):
        """Deposit funds to user's wallet with validation and logging."""
        if amount <= 0:
            raise ValidationError("amount", amount, "must be positive")

        portfolio = self.get_user_portfolio(user_id)

        # Create wallet if it doesn't exist
        if currency_code not in portfolio.wallets:
            portfolio.add_currency(currency_code)

        wallet = portfolio.get_wallet(currency_code)
        wallet.deposit(amount)
        self._save_user_portfolio(portfolio)

    @log_action(operation="WITHDRAW_FROM_WALLET", verbose=True)
    @require_authentication
    @validate_currency('currency_code')
    def withdraw_from_wallet(self, user_id: int, currency_code: str, amount: float):
        """Withdraw funds from user's wallet with comprehensive error handling."""
        if amount <= 0:
            raise ValidationError("amount", amount, "must be positive")

        portfolio = self.get_user_portfolio(user_id)

        try:
            wallet = portfolio.get_wallet(currency_code)
        except ValueError:
            raise ValidationError("currency_code", currency_code, "wallet not found")

        # Check balance before withdrawal
        if wallet.balance < amount:
            raise InsufficientFundsError(
                available=wallet.balance,
                required=amount,
                currency_code=currency_code,
                operation="withdrawal"
            )

        wallet.withdraw(amount)
        self._save_user_portfolio(portfolio)


class RateManager:
    """Enhanced RateManager with comprehensive error handling."""

    def __init__(self):
        self.rates_file = "rates"

    @log_action(operation="GET_EXCHANGE_RATE")
    @validate_currency('from_currency')
    @validate_currency('to_currency')
    def get_exchange_rate(self, from_currency: str, to_currency: str) -> float:
        """Get exchange rate between two currencies with validation."""
        from .utils import ExchangeRates

        try:
            rate = ExchangeRates.get_rate(from_currency, to_currency)
            return rate
        except CurrencyNotFoundError:
            # Fallback to basic rate calculation for known currencies
            if from_currency == to_currency:
                return 1.0
            raise

    @log_action(operation="GET_CURRENCY_INFO")
    @validate_currency('currency_code')
    def get_currency_info(self, currency_code: str) -> str:
        """Get currency display information."""
        currency = get_currency(currency_code)
        return currency.get_display_info()

    def get_supported_currencies(self) -> dict:
        """Get all supported currencies."""
        return CurrencyRegistry.get_all_currencies()


# Global instances for easy access
user_manager = UserManager()
portfolio_manager = PortfolioManager()
rate_manager = RateManager()
