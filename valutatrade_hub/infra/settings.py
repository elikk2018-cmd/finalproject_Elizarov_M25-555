"""Thread-safe Singleton SettingsLoader with caching."""
import os
import threading
from typing import Any, Dict, Optional

from ..core.exceptions import ConfigurationError


class SettingsLoader:
    """
    Thread-safe Singleton for loading and managing application settings
    with caching and environment variable support.
    """

    _instance = None
    _initialized = False
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(SettingsLoader, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        with self._lock:
            if not self._initialized:
                self._settings = {}
                self._cache = {}
                self._cache_lock = threading.Lock()
                self._load_configuration()
                self._initialized = True

    def _load_configuration(self):
        """Load configuration with comprehensive error handling."""
        try:
            # Start with default settings
            self._settings = self._get_default_settings()

            # Load from environment variables
            self._load_from_env()

            # Try to load from configuration file if exists
            self._load_from_file()

            # Validate critical settings
            self._validate_settings()

            # Ensure required directories exist
            self._ensure_directories()

        except Exception as e:
            raise ConfigurationError(
                reason=f"Failed to load configuration: {str(e)}",
                details={"error_type": type(e).__name__}
            )

    def _get_default_settings(self) -> Dict[str, Any]:
        """Get comprehensive default settings."""
        return {
            # Data and storage
            'data_dir': 'data',
            'backup_dir': 'backups',

            # Rates and trading
            'rates_ttl_seconds': 300,
            'default_base_currency': 'USD',
            'max_currency_precision': 8,

            # Logging
            'log_file': 'logs/valutatrade.log',
            'log_level': 'INFO',
            'log_format': 'simple',
            'max_log_size_mb': 10,
            'log_backup_count': 5,
            'enable_console_log': True,

            # Security
            'min_password_length': 4,
            'max_login_attempts': 5,
            'session_timeout_minutes': 30,

            # Performance
            'cache_ttl_seconds': 60,
            'max_cache_size': 1000,
            'enable_caching': True,

            # API and external services
            'request_timeout_seconds': 30,
            'max_retry_attempts': 3,
        }

    def _load_from_env(self):
        """Load settings from environment variables with prefix."""
        env_prefix = "VALUTATRADE_"

        for key in list(self._settings.keys()):
            env_key = f"{env_prefix}{key.upper()}"
            if env_key in os.environ:
                self._settings[key] = self._convert_value(os.environ[env_key])

    def _load_from_file(self):
        """Attempt to load settings from configuration file."""
        config_files = [
            'valutatrade.config.toml',
            'config.toml',
            'pyproject.toml'
        ]

        for config_file in config_files:
            if os.path.exists(config_file):
                try:
                    self._load_toml_config(config_file)
                    break
                except Exception:
                    # Continue to next file if this one fails
                    continue

    def _load_toml_config(self, file_path: str):
        """Load configuration from TOML file."""
        try:
            import toml
            with open(file_path, 'r', encoding='utf-8') as f:
                config_data = toml.load(f)

            # Extract our configuration from different possible sections
            tool_config = config_data.get('tool', {}).get('valutatrade', {})
            app_config = config_data.get('valutatrade', {})

            # Merge configurations (tool section takes precedence)
            file_config = {**app_config, **tool_config}

            # Update settings with file configuration
            for key, value in file_config.items():
                if key in self._settings:
                    self._settings[key] = value

        except ImportError:
            # toml not available, skip file loading
            pass
        except Exception as e:
            raise ConfigurationError(
                f"Error reading config file {file_path}",
                {"file": file_path, "error": str(e)}
            )

    def _validate_settings(self):
        """Validate critical settings."""
        # Validate data directory
        data_dir = self._settings['data_dir']
        if not data_dir or not isinstance(data_dir, str):
            raise ConfigurationError("Data directory must be a non-empty string")

        # Validate numeric settings
        numeric_settings = [
            'rates_ttl_seconds', 'max_log_size_mb', 'log_backup_count',
            'min_password_length', 'max_login_attempts', 'session_timeout_minutes'
        ]

        for setting in numeric_settings:
            value = self._settings[setting]
            if not isinstance(value, (int, float)) or value <= 0:
                raise ConfigurationError(
                    f"Setting '{setting}' must be a positive number",
                    {"setting": setting, "value": value}
                )

    def _ensure_directories(self):
        """Ensure required directories exist."""
        directories = [
            self._settings['data_dir'],
            os.path.dirname(self._settings['log_file']),
            self._settings['backup_dir']
        ]

        for directory in directories:
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)

    def _convert_value(self, value: str) -> Any:
        """Convert string value to appropriate type with comprehensive parsing."""
        # Handle boolean values
        if value.lower() in ('true', 'false', 'yes', 'no', '1', '0', 'on', 'off'):
            return value.lower() in ('true', 'yes', '1', 'on')

        # Handle integers
        if value.isdigit() or (value.startswith('-') and value[1:].isdigit()):
            return int(value)

        # Handle floats
        try:
            return float(value)
        except ValueError:
            pass

        # Handle lists (comma-separated)
        if ',' in value:
            return [self._convert_value(item.strip()) for item in value.split(',')]

        # Return as string
        return value

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Get configuration value by key with caching."""
        # Check cache first if caching is enabled
        if self._settings.get('enable_caching', True):
            with self._cache_lock:
                if key in self._cache:
                    cached_value, timestamp = self._cache[key]
                    cache_ttl = self._settings.get('cache_ttl_seconds', 60)
                    if time.time() - timestamp < cache_ttl:
                        return cached_value

        # Get value from settings
        value = self._settings.get(key, default)

        # Cache the value
        if self._settings.get('enable_caching', True):
            with self._cache_lock:
                self._cache[key] = (value, time.time())

                # Enforce cache size limit
                max_size = self._settings.get('max_cache_size', 1000)
                if len(self._cache) > max_size:
                    # Remove oldest entry
                    oldest_key = min(self._cache.keys(),
                                   key=lambda k: self._cache[k][1])
                    del self._cache[oldest_key]

        return value

    def set(self, key: str, value: Any, persist: bool = False):
        """Set configuration value with optional persistence."""
        with self._lock:
            self._settings[key] = value

            # Invalidate cache for this key
            with self._cache_lock:
                if key in self._cache:
                    del self._cache[key]

            # TODO: Implement persistence to file if requested
            if persist:
                self._persist_setting(key, value)

    def reload(self):
        """Reload configuration from all sources."""
        with self._lock:
            self._cache.clear()
            self._load_configuration()

    def get_all(self) -> Dict[str, Any]:
        """Get all settings as dictionary."""
        return self._settings.copy()

    def _persist_setting(self, key: str, value: Any):
        """Persist setting to configuration file (placeholder)."""
        # This would implement writing back to a configuration file
        # For now, it's a placeholder for future implementation
        pass


# Import time for cache functionality
import time

# Global singleton instance
settings = SettingsLoader()
