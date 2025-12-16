"""Domain exceptions with user-friendly messages."""


class DomainError(Exception):
    """Base domain error."""


class AuthenticationError(DomainError):
    """Raised when user must login or credentials are invalid."""


class InsufficientFundsError(DomainError):
    """Raised when wallet has not enough funds."""

    def __init__(self, code: str, available: float, required: float) -> None:
        super().__init__(
            f"Недостаточно средств: доступно {available:.4f} {code}, "
            f"требуется {required:.4f} {code}"
        )


class CurrencyNotFoundError(DomainError):
    """Raised when currency code is not supported."""

    def __init__(self, code: str) -> None:
        super().__init__(f"Неизвестная валюта '{code}'")


class ApiRequestError(DomainError):
    """Raised when external API (or rate source) is unavailable."""

    def __init__(self, reason: str) -> None:
        super().__init__(f"Ошибка при обращении к внешнему API: {reason}")


class ConfigurationError(DomainError):
    """Raised when configuration cannot be loaded/validated."""


class DatabaseError(DomainError):
    """Raised when JSON storage cannot be read/written."""
