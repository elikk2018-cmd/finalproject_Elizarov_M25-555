"""JSON storage abstraction (Singleton).

Writes are atomic: write to *.tmp then os.replace().
"""

from __future__ import annotations

import json
import os
import threading
from typing import Any

from valutatrade_hub.core.exceptions import DatabaseError
from valutatrade_hub.infra.settings import settings


class DatabaseManager:
    """Thread-safe singleton JSON storage helper."""

    _instance: DatabaseManager | None = None
    _lock = threading.Lock()

    def __new__(cls) -> DatabaseManager:
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init_once()
            return cls._instance

    def _init_once(self) -> None:
        self._data_dir = str(settings.get("datadir", "data"))
        os.makedirs(self._data_dir, exist_ok=True)

    def _path(self, name: str) -> str:
        if not name.endswith(".json"):
            name = f"{name}.json"
        return os.path.join(self._data_dir, name)

    def read_list(self, name: str) -> list[dict[str, Any]]:
        """Read JSON list from file, return [] if file does not exist."""
        path = self._path(name)
        if not os.path.exists(path):
            return []
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list):
                raise DatabaseError(f"{name}.json должен содержать список")
            return data
        except Exception as e:
            raise DatabaseError(f"Ошибка чтения {path}: {e}") from e

    def write_list(self, name: str, data: list[dict[str, Any]]) -> None:
        """Write JSON list atomically."""
        if not isinstance(data, list):
            raise DatabaseError("write_list ожидает list")
        path = self._path(name)
        tmp = path + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, path)
        except Exception as e:
            raise DatabaseError(f"Ошибка записи {path}: {e}") from e

    def read_obj(self, name: str, default: dict[str, Any] | None = None) -> dict[str, Any]:
        """Read JSON object from file, return default/{} if file missing."""
        path = self._path(name)
        if not os.path.exists(path):
            return default or {}
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                raise DatabaseError(f"{name}.json должен содержать объект")
            return data
        except Exception as e:
            raise DatabaseError(f"Ошибка чтения {path}: {e}") from e

    def write_obj(self, name: str, data: dict[str, Any]) -> None:
        """Write JSON object atomically."""
        if not isinstance(data, dict):
            raise DatabaseError("write_obj ожидает dict")
        path = self._path(name)
        tmp = path + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, path)
        except Exception as e:
            raise DatabaseError(f"Ошибка записи {path}: {e}") from e


db = DatabaseManager()
