"""External API clients for rates.

Note: to make project work without API keys, one client can fallback to "stub" data.
Requests uses explicit timeout to avoid hanging calls.
"""

from __future__ import annotations

from dataclasses import dataclass

import requests
from valuatatrade_hub.core.exceptions import ApiRequestError
from valuatatrade_hub.parser_service.config import parser_config


@dataclass(frozen=True)
class RatesSnapshot:
    """Normalized rates snapshot."""

    base: str
    rates: dict[str, float]
    source: str


class StubRatesClient:
    """Offline stub rates client (always available)."""

    def fetch(self, base: str = "USD") -> RatesSnapshot:
        base = base.upper()
        # Minimal set sufficient for demo/validation:
        if base == "USD":
            rates = {"EUR": 0.92, "RUB": 95.0, "BTC": 1 / 60000, "ETH": 1 / 2500}
        elif base == "EUR":
            rates = {"USD": 1.08, "RUB": 103.0, "BTC": 1 / 65000, "ETH": 1 / 2700}
        else:
            # fallback: provide only USD conversions
            rates = {"USD": 1.0}
        return RatesSnapshot(base=base, rates=rates, source="StubRatesClient")


class ExchangeRateHostClient:
    """Example real API client (exchangerate.host).

    If request fails, raises ApiRequestError.
    """

    BASE_URL = "https://api.exchangerate.host/latest"

    def fetch(self, base: str = "USD") -> RatesSnapshot:
        try:
            r = requests.get(
                self.BASE_URL,
                params={"base": base.upper()},
                timeout=parser_config.request_timeout_seconds,
            )
            r.raise_for_status()
            data = r.json()
            rates = data.get("rates")
            if not isinstance(rates, dict):
                raise ApiRequestError("Некорректный ответ API: rates отсутствует")
            # Keep only what our app supports:
            filtered = {k: float(v) for k, v in rates.items() if k in {"USD", "EUR", "RUB"}}
            return RatesSnapshot(
                base=base.upper(), rates=filtered, source="exchangerate.host"
            )
        except requests.RequestException as e:
            raise ApiRequestError(str(e)) from e
