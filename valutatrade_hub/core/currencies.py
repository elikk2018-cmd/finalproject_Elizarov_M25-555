"""Currency hierarchy with inheritance and polymorphism."""
from abc import ABC, abstractmethod

from ..core.exceptions import CurrencyNotFoundError


class Currency(ABC):
    """Abstract base class for all currencies."""

    def __init__(self, name: str, code: str):
        if not name or not isinstance(name, str):
            raise ValueError("Название валюты не может быть пустым")
        if not code or not code.isalpha() or not 2 <= len(code) <= 5:
            raise ValueError("Код валюты должен содержать 2-5 букв в верхнем регистре")

        self._name = name
        self._code = code.upper()

    @property
    def name(self) -> str:
        return self._name

    @property
    def code(self) -> str:
        return self._code

    @abstractmethod
    def get_display_info(self) -> str:
        """Return string representation for UI/logs."""
        pass

    def __str__(self) -> str:
        return self.get_display_info()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', code='{self.code}')"


class FiatCurrency(Currency):
    """Fiat currency representation."""

    def __init__(self, name: str, code: str, issuing_country: str):
        super().__init__(name, code)
        self._issuing_country = issuing_country

    @property
    def issuing_country(self) -> str:
        return self._issuing_country

    def get_display_info(self) -> str:
        return f"[FIAT] {self.code} — {self.name} (Issuing: {self.issuing_country})"


class CryptoCurrency(Currency):
    """Cryptocurrency representation."""

    def __init__(self, name: str, code: str, algorithm: str, market_cap: float = 0.0):
        super().__init__(name, code)
        self._algorithm = algorithm
        self._market_cap = float(market_cap)

    @property
    def algorithm(self) -> str:
        return self._algorithm

    @property
    def market_cap(self) -> float:
        return self._market_cap

    def get_display_info(self) -> str:
        mcap_str = f"{self.market_cap:.2e}" if self.market_cap > 0 else "N/A"
        return f"[CRYPTO] {self.code} — {self.name} (Algo: {self.algorithm}, MCAP: {mcap_str})"


class CurrencyRegistry:
    """Registry and factory for currencies."""

    _currencies = {
        # Fiat currencies
        "USD": FiatCurrency("US Dollar", "USD", "United States"),
        "EUR": FiatCurrency("Euro", "EUR", "Eurozone"),
        "GBP": FiatCurrency("British Pound", "GBP", "United Kingdom"),
        "RUB": FiatCurrency("Russian Ruble", "RUB", "Russia"),
        "JPY": FiatCurrency("Japanese Yen", "JPY", "Japan"),
        "CNY": FiatCurrency("Chinese Yuan", "CNY", "China"),

        # Cryptocurrencies
        "BTC": CryptoCurrency("Bitcoin", "BTC", "SHA-256", 1.12e12),
        "ETH": CryptoCurrency("Ethereum", "ETH", "Ethash", 4.5e11),
        "SOL": CryptoCurrency("Solana", "SOL", "Proof of History", 6.5e10),
        "ADA": CryptoCurrency("Cardano", "ADA", "Ouroboros", 1.8e10),
        "DOT": CryptoCurrency("Polkadot", "DOT", "NPoS", 1.2e10),
    }

    @classmethod
    def get_currency(cls, code: str) -> Currency:
        """Get currency by code."""
        code = code.upper()
        if code not in cls._currencies:
            raise CurrencyNotFoundError(code)
        return cls._currencies[code]

    @classmethod
    def get_all_currencies(cls) -> dict:
        """Get all registered currencies."""
        return cls._currencies.copy()

    @classmethod
    def get_supported_codes(cls) -> list:
        """Get list of all supported currency codes."""
        return list(cls._currencies.keys())

    @classmethod
    def register_currency(cls, currency: Currency):
        """Register a new currency."""
        if currency.code in cls._currencies:
            raise ValueError(f"Currency {currency.code} already registered")
        cls._currencies[currency.code] = currency


# Factory function
def get_currency(code: str) -> Currency:
    """Get currency instance by code."""
    return CurrencyRegistry.get_currency(code)
