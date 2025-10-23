"""Enhanced logging configuration with rotation and formatting."""
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from .infra.settings import settings


class CustomFormatter(logging.Formatter):
    """Custom formatter with colors and structured output."""

    # Color codes
    GREY = "\x1b[38;21m"
    GREEN = "\x1b[32;21m"
    YELLOW = "\x1b[33;21m"
    RED = "\x1b[31;21m"
    BOLD_RED = "\x1b[31;1m"
    RESET = "\x1b[0m"

    # Format strings
    FORMATS = {
        logging.DEBUG: f"{GREY}%(asctime)s - %(name)s - %(levelname)s - %(message)s{RESET}",
        logging.INFO: f"{GREEN}%(asctime)s - %(name)s - %(levelname)s - %(message)s{RESET}",
        logging.WARNING: f"{YELLOW}%(asctime)s - %(name)s - %(levelname)s - %(message)s{RESET}",
        logging.ERROR: f"{RED}%(asctime)s - %(name)s - %(levelname)s - %(message)s{RESET}",
        logging.CRITICAL: f"{BOLD_RED}%(asctime)s - %(name)s - %(levelname)s - %(message)s{RESET}",
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt='%Y-%m-%d %H:%M:%S')
        return formatter.format(record)


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record):
        import json

        # Extract custom fields from record
        custom_fields = {}
        reserved_fields = {
            'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
            'module', 'exc_info', 'exc_text', 'stack_info', 'lineno', 'funcName',
            'created', 'msecs', 'relativeCreated', 'thread', 'threadName', 'processName', 'process'
        }

        for key, value in record.__dict__.items():
            if key not in reserved_fields and not key.startswith('_'):
                custom_fields[key] = value

        log_entry = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            **custom_fields
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, ensure_ascii=False)


class SafeFormatter(logging.Formatter):
    """Safe formatter that handles custom fields without conflicts."""

    def __init__(self, fmt=None, datefmt=None, style='%'):
        super().__init__(fmt, datefmt, style)
        self._custom_fields = set()

    def format(self, record):
        # Store custom fields before formatting
        custom_data = {}
        reserved_fields = {
            'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
            'module', 'exc_info', 'exc_text', 'stack_info', 'lineno', 'funcName',
            'created', 'msecs', 'relativeCreated', 'thread', 'threadName', 'processName', 'process'
        }

        for key, value in record.__dict__.items():
            if key not in reserved_fields and not key.startswith('_'):
                custom_data[key] = value
                # Temporarily remove custom fields to avoid conflicts
                if hasattr(record, key):
                    delattr(record, key)

        try:
            result = super().format(record)
        finally:
            # Restore custom fields
            for key, value in custom_data.items():
                setattr(record, key, value)

        return result


def setup_logging():
    """Setup comprehensive logging configuration."""

    # Get logging configuration from settings
    log_file = settings.get('log_file', 'logs/valutatrade.log')
    log_level_name = settings.get('log_level', 'INFO').upper()
    log_format = settings.get('log_format', 'simple')
    max_log_size = settings.get('max_log_size_mb', 10) * 1024 * 1024  # Convert to bytes
    backup_count = settings.get('log_backup_count', 5)

    # Convert log level name to constant
    log_level = getattr(logging, log_level_name, logging.INFO)

    # Ensure log directory exists
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Clear existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create formatter based on configuration
    if log_format == 'json':
        formatter = JSONFormatter(datefmt='%Y-%m-%d %H:%M:%S')
    else:
        formatter = SafeFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    # File handler with rotation
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_log_size,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    logger.addHandler(file_handler)

    # Console handler with colors (only for non-JSON format)
    if log_format != 'json' and sys.stderr.isatty():
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(CustomFormatter())
        console_handler.setLevel(log_level)
        logger.addHandler(console_handler)
    else:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(log_level)
        logger.addHandler(console_handler)

    # Set levels for specific loggers
    logging.getLogger('valutatrade_hub').setLevel(log_level)

    # Log startup information
    logger.info("Logging system initialized")
    logger.info("Log file: %s", log_file)
    logger.info("Log level: %s", log_level_name)
    logger.info("Log format: %s", log_format)


# Initialize logging when module is imported
setup_logging()
