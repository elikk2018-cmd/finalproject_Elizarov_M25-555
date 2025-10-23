"""Comprehensive exception hierarchy for ValutaTrade Hub."""
from typing import Any


class ValutaTradeError(Exception):
    """Base exception for all application errors."""

    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self):
        if self.details:
            return f"{self.message} (Details: {self.details})"
        return self.message

    def to_dict(self):
        """Convert exception to dictionary for logging/API responses."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details
        }


class InsufficientFundsError(ValutaTradeError):
    """Raised when there are insufficient funds for an operation."""

    def __init__(self, available: float, required: float, currency_code: str, operation: str = None):
        details = {
            "available": available,
            "required": required,
            "currency_code": currency_code,
            "operation": operation
        }
        super().__init__(
            f"Недостаточно средств: доступно {available} {currency_code}, требуется {required} {currency_code}",
            details
        )


class CurrencyNotFoundError(ValutaTradeError):
    """Raised when currency is not found."""

    def __init__(self, code: str, available_currencies: list = None):
        details = {
            "requested_currency": code,
            "available_currencies": available_currencies or []
        }
        super().__init__(f"Неизвестная валюта '{code}'", details)


class UserNotFoundError(ValutaTradeError):
    """Raised when user is not found."""

    def __init__(self, username: str = None, user_id: int = None):
        details = {}
        if username:
            details["username"] = username
            message = f"Пользователь '{username}' не найден"
        elif user_id:
            details["user_id"] = user_id
            message = f"Пользователь с ID {user_id} не найден"
        else:
            message = "Пользователь не найден"

        super().__init__(message, details)


class AuthenticationError(ValutaTradeError):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Ошибка аутентификации", details: dict = None):
        super().__init__(message, details or {})


class AuthorizationError(ValutaTradeError):
    """Raised when user is not authorized for an operation."""

    def __init__(self, operation: str, user_id: int = None):
        details = {
            "operation": operation,
            "user_id": user_id
        }
        super().__init__(f"Недостаточно прав для выполнения операции: {operation}", details)


class ValidationError(ValutaTradeError):
    """Raised when input validation fails."""

    def __init__(self, field: str, value: Any, reason: str):
        details = {
            "field": field,
            "value": value,
            "reason": reason
        }
        super().__init__(f"Ошибка валидации поля '{field}': {reason}", details)


class ApiRequestError(ValutaTradeError):
    """Raised when external API request fails."""

    def __init__(self, url: str, status_code: int = None, reason: str = None):
        details = {
            "url": url,
            "status_code": status_code,
            "reason": reason
        }
        message = f"Ошибка при обращении к внешнему API: {reason or 'Unknown error'}"
        if status_code:
            message += f" (Status: {status_code})"
        super().__init__(message, details)


class ConfigurationError(ValutaTradeError):
    """Raised when there is a configuration error."""

    def __init__(self, key: str = None, value: Any = None, reason: str = None):
        details = {
            "config_key": key,
            "config_value": value,
            "reason": reason
        }
        message = "Ошибка конфигурации"
        if key:
            message += f" ключа '{key}'"
        if reason:
            message += f": {reason}"
        super().__init__(message, details)


class DatabaseError(ValutaTradeError):
    """Raised when there is a database error."""

    def __init__(self, operation: str, entity: str = None, details: str = None):
        error_details = {
            "operation": operation,
            "entity": entity,
            "system_details": details
        }
        message = f"Ошибка базы данных при операции: {operation}"
        if entity:
            message += f" (сущность: {entity})"
        super().__init__(message, error_details)


class BusinessLogicError(ValutaTradeError):
    """Raised when business logic constraints are violated."""

    def __init__(self, constraint: str, details: dict = None):
        super().__init__(
            f"Нарушение бизнес-логики: {constraint}",
            details or {}
        )


# Convenience functions for common error scenarios
def raise_currency_validation_error(currency_code: str, available_currencies: list = None):
    """Convenience function to raise CurrencyNotFoundError."""
    raise CurrencyNotFoundError(currency_code, available_currencies)


def raise_insufficient_funds(available: float, required: float, currency_code: str, operation: str = None):
    """Convenience function to raise InsufficientFundsError."""
    raise InsufficientFundsError(available, required, currency_code, operation)


def raise_validation_error(field: str, value: Any, reason: str):
    """Convenience function to raise ValidationError."""
    raise ValidationError(field, value, reason)
