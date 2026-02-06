"""Configuration loader for Wi-Fi Aware Simulator."""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional


class Config:
    """Configuration manager that loads and validates YAML config files."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration.

        Args:
            config_path: Path to YAML config file. If None, loads default config.
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "default.yaml"
        else:
            config_path = Path(config_path)

        with open(config_path, 'r', encoding='utf-8') as f:
            self.config: Dict[str, Any] = yaml.safe_load(f)

    def get(self, key_path: str, default=None) -> Any:
        """Get configuration value using dot notation.

        Args:
            key_path: Dot-separated path (e.g., 'time.dw_interval')
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key_path.split('.')
        value = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def set(self, key_path: str, value: Any) -> None:
        """Set configuration value using dot notation.

        Args:
            key_path: Dot-separated path (e.g., 'time.dw_interval')
            value: Value to set
        """
        keys = key_path.split('.')
        config = self.config

        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]

        config[keys[-1]] = value

    def to_dict(self) -> Dict[str, Any]:
        """Return configuration as dictionary."""
        return self.config.copy()
