"""Custom exceptions for the application."""


class ValutaTradeError(Exception):
    """Base exception for all application errors."""
    pass


class InsufficientFundsError(ValutaTradeError):
    """Raised when there are insufficient funds for an operation."""
    
    def __init__(self, available: float, required: float, currency_code: str):
        self.available = available
        self.required = required
        self.currency_code = currency_code
        super().__init__(
            f"Недостаточно средств: доступно {available} {currency_code}, требуется {required} {currency_code}"
        )


class CurrencyNotFoundError(ValutaTradeError):
    """Raised when currency is not found."""
    
    def __init__(self, code: str):
        self.code = code
        super().__init__(f"Неизвестная валюта '{code}'")


class UserNotFoundError(ValutaTradeError):
    """Raised when user is not found."""
    
    def __init__(self, username: str = None, user_id: int = None):
        self.username = username
        self.user_id = user_id
        if username:
            super().__init__(f"Пользователь '{username}' не найден")
        else:
            super().__init__(f"Пользователь с ID {user_id} не найден")


class AuthenticationError(ValutaTradeError):
    """Raised when authentication fails."""
    pass


class ApiRequestError(ValutaTradeError):
    """Raised when external API request fails."""
    
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"Ошибка при обращении к внешнему API: {reason}")
