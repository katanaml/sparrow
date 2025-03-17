import configparser
import os
from typing import Dict, Any, Optional, List
import json


class SparrowConfig:
    """
    Unified configuration utility for Sparrow services.
    Reads configuration from config.properties file.
    """
    _instance = None  # Singleton instance
    _config = None  # Config object

    def __new__(cls):
        """Implement singleton pattern"""
        if cls._instance is None:
            cls._instance = super(SparrowConfig, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        """Load configuration from config.properties file"""
        self._config = configparser.ConfigParser()

        # Determine the config file path
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.properties')

        # Read the config file
        if os.path.exists(config_path):
            self._config.read(config_path)
        else:
            # Create default config if file doesn't exist
            self._create_default_config()
            self._config.read(config_path)

    def _create_default_config(self):
        """Create default configuration file if it doesn't exist"""
        default_config = configparser.ConfigParser()

        default_config['settings'] = {
            'llm_function': 'adrienbrault/nous-hermes2theta-llama3-8b:q5_K_M',
            'ollama_base_url': 'http://127.0.0.1:11434/v1',
            'protected_access': 'false',
            'version': '0.5.5',
            'backend_url': 'http://localhost:8002/api/v1/sparrow-llm/inference',
            'backend_options': 'mlx,mlx-community/Qwen2.5-VL-7B-Instruct-8bit'
        }

        default_config['keys'] = {
            'key1_value': 'value1',
            'key1_usage_count': '0',
            'key1_usage_limit': '5',
            'key2_value': 'value2',
            'key2_usage_count': '0',
            'key2_usage_limit': '3'
        }

        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.properties')
        with open(config_path, 'w') as configfile:
            default_config.write(configfile)

    def get_str(self, section: str, key: str, default: str = "") -> str:
        """Get a string value from the configuration"""
        if section in self._config and key in self._config[section]:
            return self._config[section][key]
        return default

    def get_int(self, section: str, key: str, default: int = 0) -> int:
        """Get an integer value from the configuration"""
        try:
            return int(self.get_str(section, key, str(default)))
        except ValueError:
            return default

    def get_float(self, section: str, key: str, default: float = 0.0) -> float:
        """Get a float value from the configuration"""
        try:
            return float(self.get_str(section, key, str(default)))
        except ValueError:
            return default

    def get_bool(self, section: str, key: str, default: bool = False) -> bool:
        """Get a boolean value from the configuration"""
        value = self.get_str(section, key, str(default)).lower()
        return value in ('true', 'yes', '1', 'on')

    def get_list(self, section: str, key: str, default: List[str] = None) -> List[str]:
        """Get a list of values from the configuration (comma-separated)"""
        if default is None:
            default = []
        value = self.get_str(section, key, "")
        if not value:
            return default
        return [item.strip() for item in value.split(',')]

    def get_sparrow_keys(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all Sparrow API keys from the configuration.
        Returns a dictionary in the same format as the old YAML config.
        """
        if 'keys' not in self._config:
            return {}

        keys = {}
        key_indices = set()

        # Collect all unique key indices
        for option in self._config['keys']:
            if option.endswith('_value'):
                key_index = option.split('_')[0]
                key_indices.add(key_index)

        # Process each key
        for index in key_indices:
            value_key = f"{index}_value"
            usage_count_key = f"{index}_usage_count"
            usage_limit_key = f"{index}_usage_limit"

            if value_key in self._config['keys']:
                key_data = {
                    'value': self._config['keys'][value_key],
                    'usage_count': self.get_int('keys', usage_count_key, 0),
                    'usage_limit': self.get_int('keys', usage_limit_key, float('inf'))
                }
                keys[index] = key_data

        return keys

    def update_key_usage(self, key_name: str, new_count: int) -> None:
        """Update the usage count for a specific key"""
        usage_count_key = f"{key_name}_usage_count"
        if 'keys' in self._config and key_name in self.get_sparrow_keys():
            self._config['keys'][usage_count_key] = str(new_count)
            self._save_config()

    def _save_config(self) -> None:
        """Save the configuration back to the file"""
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.properties')
        with open(config_path, 'w') as configfile:
            self._config.write(configfile)

    def get_sparrow_key_value(self, key_name: str) -> Optional[str]:
        """Get the value of a specific key"""
        keys = self.get_sparrow_keys()
        if key_name in keys:
            return keys[key_name]['value']
        return None


# Convenience function to get config instance
def get_config() -> SparrowConfig:
    """Get the singleton configuration instance"""
    return SparrowConfig()


if __name__ == "__main__":
    # Test the configuration
    config = get_config()
    print(f"LLM Function: {config.get_str('settings', 'llm_function')}")
    print(f"Protected Access: {config.get_bool('settings', 'protected_access')}")
    print(f"Sparrow Keys: {json.dumps(config.get_sparrow_keys(), indent=2)}")