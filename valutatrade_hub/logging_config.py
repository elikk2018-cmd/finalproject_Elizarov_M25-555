"""Logging configuration with rotation and optional JSON format."""

from __future__ import annotations

import json
import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Any

from valutatrade_hub.infra.settings import settings


class JsonFormatter(logging.Formatter):
    """Format log records as JSON (keeps extra fields)."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        reserved = {
            "name",
            "msg",
            "args",
            "levelname",
            "levelno",
            "pathname",
            "filename",
            "module",
            "exc_info",
            "exc_text",
            "stack_info",
            "lineno",
            "funcName",
            "created",
            "msecs",
            "relativeCreated",
            "thread",
            "threadName",
            "processName",
            "process",
        }

        for key, value in record.__dict__.items():
            if key in reserved or key.startswith("_"):
                continue
            payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


def setup_logging() -> None:
    """Setup root logger handlers, levels, rotation."""
    log_file = str(settings.get("logfile", "logs/valutatrade.log"))
    log_level = str(settings.get("loglevel", "INFO")).upper()
    log_format = str(settings.get("logformat", "simple")).lower()

    os.makedirs(os.path.dirname(log_file) or ".", exist_ok=True)

    root = logging.getLogger()
    root.setLevel(getattr(logging, log_level, logging.INFO))
    root.handlers.clear()

    handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=int(settings.get("maxlogsizemb", 10)) * 1024 * 1024,
        backupCount=int(settings.get("logbackupcount", 5)),
        encoding="utf-8",
    )

    if log_format == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )

    root.addHandler(handler)
