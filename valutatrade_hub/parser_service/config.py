"""Parser Service configuration."""

from __future__ import annotations

from dataclasses import dataclass

from valutatrade_hub.infra.settings import settings


@dataclass(frozen=True)
class ParserConfig:
    """Configuration for rate fetching."""

    request_timeout_seconds: int = int(settings.get("requesttimeoutseconds", 10))
    exchangerate_api_key: str = str(settings.get("exchangerate_api_key", ""))


parser_config = ParserConfig()
