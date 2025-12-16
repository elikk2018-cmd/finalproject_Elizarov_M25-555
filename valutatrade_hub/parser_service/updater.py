"""RatesUpdater: updates data/rates.json with normalized pairs."""

from __future__ import annotations

from typing import Any

from valutatrade_hub.core.currencies import get_currency
from valutatrade_hub.core.utils import normalize_currency_code
from valutatrade_hub.decorators import log_action
from valutatrade_hub.parser_service.api_clients import (
    ExchangeRateHostClient,
    StubRatesClient,
)
from valutatrade_hub.parser_service.storage import RatesStorage


class RatesUpdater:
    """Fetch rates and build pair table like BTC_USD, USD_BTC, EUR_USD..."""

    def __init__(self) -> None:
        self._storage = RatesStorage()
        # First try real API, fallback to stub.
        self._clients = [ExchangeRateHostClient(), StubRatesClient()]

    def read_cache(self) -> dict[str, Any]:
        """Read current cache."""
        return self._storage.read()

    @log_action("UPDATE_RATES")
    def update(self, base: str = "USD") -> dict[str, Any]:
        """Update cache for supported currencies."""
        base_code = normalize_currency_code(base)
        get_currency(base_code)

        snapshot = None
        last_error = None
        for client in self._clients:
            try:
                snapshot = client.fetch(base=base_code)
                break
            except Exception as e:
                last_error = e

        if snapshot is None:
            raise RuntimeError(f"Не удалось получить курсы: {last_error}")

        supported = ["USD", "EUR", "RUB", "BTC", "ETH"]
        for c in supported:
            get_currency(c)

        # Normalize: base->X rates.
        # For crypto we use stub-only numbers (already in stub). If real API doesn't provide BTC/ETH,
        # we just won't overwrite them (or we can keep stub values).
        rates = snapshot.rates.copy()

        # Ensure base exists
        rates[base_code] = 1.0

        pairs: dict[str, Any] = {}
        updated_at = self._storage.now_iso()

        # Build pair table among supported currencies using base as bridge.
        for frm in supported:
            for to in supported:
                if frm == to:
                    continue
                frm = normalize_currency_code(frm)
                to = normalize_currency_code(to)

                # Convert frm->to:
                # rate(frm->to) = (base->to) / (base->frm)
                if frm not in rates or to not in rates:
                    continue
                r = float(rates[to]) / float(rates[frm])
                pairs[f"{frm}_{to}"] = {"rate": r, "updated_at": updated_at}

        payload: dict[str, Any] = {
            **pairs,
            "source": snapshot.source,
            "last_refresh": updated_at,
        }
        self._storage.write(payload)
        return payload
