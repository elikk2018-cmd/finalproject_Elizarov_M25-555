"""Storage helpers for rates cache."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from valutatrade_hub.infra.database import db


class RatesStorage:
    """Read/write rates.json."""

    def read(self) -> dict[str, Any]:
        return db.read_obj("rates", default={})

    def write(self, payload: dict[str, Any]) -> None:
        db.write_obj("rates", payload)

    def now_iso(self) -> str:
        return datetime.now().replace(microsecond=0).isoformat()
