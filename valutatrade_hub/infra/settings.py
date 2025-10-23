"""Singleton SettingsLoader for configuration management."""
import os
from typing import Any, Optional
from ..core.exceptions import ConfigurationError


class SettingsLoader:
    """Singleton for loading and managing application settings."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SettingsLoader, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._settings = {}
            self._load_configuration()
            self._initialized = True
    
    def _load_configuration(self):
        """Load configuration from pyproject.toml and environment variables."""
        try:
            # Try to load from pyproject.toml
            try:
                import toml
                if os.path.exists('pyproject.toml'):
                    with open('pyproject.toml', 'r', encoding='utf-8') as f:
                        config_data = toml.load(f)
                    
                    # Extract our tool configuration
                    tool_config = config_data.get('tool', {}).get('valutatrade', {})
                    
                    # Base settings
                    self._settings = {
                        'data_dir': tool_config.get('data_dir', 'data'),
                        'rates_ttl_seconds': tool_config.get('rates_ttl_seconds', 300),
                        'default_base_currency': tool_config.get('default_base_currency', 'USD'),
                        'log_file': tool_config.get('log_file', 'logs/valutatrade.log'),
                        'log_level': tool_config.get('log_level', 'INFO'),
                        'log_format': tool_config.get('log_format', 'simple'),
                        'max_log_size_mb': tool_config.get('max_log_size_mb', 10),
                        'log_backup_count': tool_config.get('log_backup_count', 5),
                    }
            except ImportError:
                # Fallback if toml is not available
                self._settings = self._get_default_settings()
            
            # Override with environment variables
            for key in self._settings:
                env_key = f"VALUTATRADE_{key.upper()}"
                if env_key in os.environ:
                    self._settings[key] = self._convert_value(os.environ[env_key])
            
            # Ensure data directory exists
            os.makedirs(self._settings['data_dir'], exist_ok=True)
            
        except Exception as e:
            raise ConfigurationError(f"Ошибка загрузки конфигурации: {e}")
    
    def _get_default_settings(self):
        """Get default settings when toml is not available."""
        return {
            'data_dir': 'data',
            'rates_ttl_seconds': 300,
            'default_base_currency': 'USD',
            'log_file': 'logs/valutatrade.log',
            'log_level': 'INFO',
            'log_format': 'simple',
            'max_log_size_mb': 10,
            'log_backup_count': 5,
        }
    
    def _convert_value(self, value: str) -> Any:
        """Convert string value to appropriate type."""
        if value.isdigit():
            return int(value)
        try:
            return float(value)
        except ValueError:
            pass
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        return value
    
    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Get configuration value by key."""
        return self._settings.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set configuration value."""
        self._settings[key] = value
    
    def reload(self):
        """Reload configuration from sources."""
        self._load_configuration()
    
    def get_all(self) -> dict:
        """Get all settings as dictionary."""
        return self._settings.copy()


# Global singleton instance
settings = SettingsLoader()
