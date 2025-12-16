"""Currency hierarchy and registry (factory by code)."""

from __future__ import annotations

from abc import ABC, abstractmethod

from valutatrade_hub.core.exceptions import CurrencyNotFoundError
from valutatrade_hub.core.utils import normalize_currency_code


class Currency(ABC):
    """Abstract base currency.

    Public attributes:
        name: Human-readable name (e.g. "US Dollar").
        code: Code/ticker (e.g. "USD", "BTC").
    """

    def __init__(self, name: str, code: str) -> None:
        if not name or not isinstance(name, str):
            raise ValueError("name должен быть непустой строкой")
        self.name = name
        self.code = normalize_currency_code(code)

    @abstractmethod
    def get_display_info(self) -> str:
        """Return display string for UI/logs."""


class FiatCurrency(Currency):
    """Fiat currency."""

    def __init__(self, name: str, code: str, issuing_country: str) -> None:
        super().__init__(name=name, code=code)
        if not issuing_country or not isinstance(issuing_country, str):
            raise ValueError("issuing_country должен быть непустой строкой")
        self.issuing_country = issuing_country

    def get_display_info(self) -> str:
        return f"[FIAT] {self.code} — {self.name} (Issuing: {self.issuing_country})"


class CryptoCurrency(Currency):
    """Crypto currency."""

    def __init__(self, name: str, code: str, algorithm: str, market_cap: float) -> None:
        super().__init__(name=name, code=code)
        if not algorithm or not isinstance(algorithm, str):
            raise ValueError("algorithm должен быть непустой строкой")
        self.algorithm = algorithm
        self.market_cap = float(market_cap)

    def get_display_info(self) -> str:
        return (
            f"[CRYPTO] {self.code} — {self.name} "
            f"(Algo: {self.algorithm}, MCAP: {self.market_cap:.2e})"
        )


_CURRENCIES: dict[str, Currency] = {
    "USD": FiatCurrency("US Dollar", "USD", "United States"),
    "EUR": FiatCurrency("Euro", "EUR", "Eurozone"),
    "RUB": FiatCurrency("Russian Ruble", "RUB", "Russia"),
    "BTC": CryptoCurrency("Bitcoin", "BTC", "SHA-256", 1.12e12),
    "ETH": CryptoCurrency("Ethereum", "ETH", "Ethash", 4.2e11),
}


def get_currency(code: str) -> Currency:
    """Get Currency object by code.

    Args:
        code: Currency code (any case, trimmed).

    Returns:
        Currency instance from registry.

    Raises:
        CurrencyNotFoundError: If code is unknown.
    """
    key = normalize_currency_code(code)
    cur = _CURRENCIES.get(key)
    if cur is None:
        raise CurrencyNotFoundError(key)
    return cur
