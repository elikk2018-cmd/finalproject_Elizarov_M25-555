"""Singleton SettingsLoader.

Loads configuration from defaults and environment variables with prefix VALUTATRADE_.

Why __new__:
- Simple and readable singleton implementation.
- Prevents creation of multiple instances across imports.
- Thread-safe via class-level lock.
"""

from __future__ import annotations

import os
import threading
from typing import Any

from valutatrade_hub.core.exceptions import ConfigurationError


class SettingsLoader:
    """Thread-safe Singleton for project settings."""

    _instance: SettingsLoader | None = None
    _lock = threading.Lock()

    def __new__(cls) -> SettingsLoader:
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init_once()
            return cls._instance

    def _init_once(self) -> None:
        self._settings: dict[str, Any] = self._defaults()
        self._load_env()

    def _defaults(self) -> dict[str, Any]:
        return {
            "datadir": "data",
            "ratesttlseconds": 300,
            "defaultbasecurrency": "USD",
            "logfile": "logs/valutatrade.log",
            "loglevel": "INFO",
            "logformat": "simple",  # "simple" or "json"
            "maxlogsizemb": 10,
            "logbackupcount": 5,
            "requesttimeoutseconds": 10,
            "exchangerate_api_key": "",
        }

    def _load_env(self) -> None:
        prefix = "VALUTATRADE_"
        for key in list(self._settings.keys()):
            env_key = prefix + key.upper()
            if env_key in os.environ:
                value: str = os.environ[env_key]
                self._settings[key] = self._convert(value)

    def _convert(self, raw: str) -> Any:
        v = raw.strip()
        low = v.lower()
        if low in {"true", "false"}:
            return low == "true"
        # int
        if v.isdigit() or (v.startswith("-") and v[1:].isdigit()):
            try:
                return int(v)
            except ValueError:
                return v
        # float
        try:
            return float(v)
        except ValueError:
            return v

    def get(self, key: str, default: Any = None) -> Any:
        """Get value by key."""
        return self._settings.get(key, default)

    def reload(self) -> None:
        """Reload defaults + env."""
        try:
            self._settings = self._defaults()
            self._load_env()
        except Exception as e:
            raise ConfigurationError(str(e)) from e


settings = SettingsLoader()
