"""Logging configuration for ValutaTrade Hub."""
import logging
import os
from logging.handlers import RotatingFileHandler
from .infra.settings import settings


def setup_logging():
    """Setup application logging configuration."""
    
    # Get logging configuration
    log_file = settings.get('log_file', 'logs/valutatrade.log')
    log_level = settings.get('log_level', 'INFO').upper()
    log_format = settings.get('log_format', 'simple')
    max_log_size = settings.get('max_log_size_mb', 10) * 1024 * 1024
    backup_count = settings.get('log_backup_count', 5)
    
    # Ensure log directory exists
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level, logging.INFO))
    
    # Clear existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create formatters
    if log_format == 'json':
        formatter = logging.Formatter(
            '{"time": "%(asctime)s", "level": "%(levelname)s", "module": "%(name)s", "message": "%(message)s"}',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        formatter = logging.Formatter(
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
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


# Initialize logging when module is imported
setup_logging()
