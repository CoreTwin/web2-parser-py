"""
Configuration management utilities.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigManager:
    """Manages application configuration."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize configuration manager.
        
        Args:
            config_dir: Path to configuration directory. If None, uses default.
        """
        if config_dir is None:
            self.config_dir = Path(__file__).parent.parent.parent / "config"
        else:
            self.config_dir = config_dir
            
        self.logger = logging.getLogger(__name__)
        
    def load_config(self, config_file: str = "settings.json") -> Dict[str, Any]:
        """Load main configuration file.
        
        Args:
            config_file: Name of the configuration file.
            
        Returns:
            Configuration dictionary.
        """
        config_path = self.config_dir / config_file
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            self.logger.info(f"Loaded configuration from {config_path}")
            return config
        except FileNotFoundError:
            self.logger.error(f"Configuration file not found: {config_path}")
            return {}
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in configuration file: {e}")
            return {}
            
    def load_site_config(self, site_name: str) -> Dict[str, Any]:
        """Load site-specific configuration.
        
        Args:
            site_name: Name of the site configuration file (without .json).
            
        Returns:
            Site configuration dictionary.
        """
        config_path = self.config_dir / "sites" / f"{site_name}.json"
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            self.logger.info(f"Loaded site configuration from {config_path}")
            return config
        except FileNotFoundError:
            self.logger.error(f"Site configuration file not found: {config_path}")
            return {}
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in site configuration file: {e}")
            return {}
            
    def load_departments_config(self) -> Dict[str, Any]:
        """Load departments configuration.
        
        Returns:
            Departments configuration dictionary.
        """
        return self.load_config("departments.json")
        
    def save_config(self, config: Dict[str, Any], config_file: str = "settings.json") -> bool:
        """Save configuration to file.
        
        Args:
            config: Configuration dictionary to save.
            config_file: Name of the configuration file.
            
        Returns:
            True if successful, False otherwise.
        """
        config_path = self.config_dir / config_file
        
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Saved configuration to {config_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            return False
