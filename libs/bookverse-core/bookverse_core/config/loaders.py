



import os
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional, Type, TypeVar, Union

try:
    import yaml
except ImportError:
    yaml = None

from .base import BaseConfig

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseConfig)


class ConfigValidationError(Exception):
    pass


class ConfigLoader:
    
    
    def __init__(self, config_class: Type[T]):
        
        self.config_class = config_class
    
    def load_from(
        self,
        yaml_file: Optional[Union[str, Path]] = None,
        env_prefix: str = "",
        defaults: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> T:
        
        
            
            
        config_data = {}
        
        if defaults:
            config_data.update(defaults)
            logger.debug(f"Loaded {len(defaults)} default values")
        
        if yaml_file:
            yaml_data = self._load_yaml_file(yaml_file)
            if yaml_data:
                config_data = self._deep_merge(config_data, yaml_data)
                logger.debug(f"Loaded configuration from {yaml_file}")
        
        env_data = self._load_env_vars(env_prefix)
        if env_data:
            config_data = self._deep_merge(config_data, env_data)
            logger.debug(f"Loaded {len(env_data)} environment variables")
        
        if kwargs:
            config_data = self._deep_merge(config_data, kwargs)
            logger.debug(f"Applied {len(kwargs)} direct overrides")
        
        try:
            return self.config_class(**config_data)
        except Exception as e:
            raise ConfigValidationError(f"Configuration validation failed: {e}") from e
    
    def _load_yaml_file(self, yaml_file: Union[str, Path]) -> Dict[str, Any]:
        if yaml is None:
            logger.warning("PyYAML not available, skipping YAML file loading")
            return {}
        
        yaml_path = Path(yaml_file)
        if not yaml_path.exists():
            logger.warning(f"YAML file not found: {yaml_path}")
            return {}
        
        try:
            with yaml_path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            
            if not isinstance(data, dict):
                logger.warning(f"YAML file {yaml_path} does not contain a dictionary")
                return {}
            
            return data
        except Exception as e:
            logger.error(f"Failed to load YAML file {yaml_path}: {e}")
            return {}
    
    def _load_env_vars(self, prefix: str) -> Dict[str, Any]:
        env_data = {}
        
        for key, value in os.environ.items():
            config_key = None
            
            if prefix and key.startswith(prefix):
                config_key = key[len(prefix):].lower()
            elif not prefix:
                config_key = key.lower()
            
            if config_key:
                converted_value = self._convert_env_value(value)
                env_data[config_key] = converted_value
        
        return env_data
    
    def _convert_env_value(self, value: str) -> Any:
        if value.lower() in ("true", "yes", "1", "on"):
            return True
        elif value.lower() in ("false", "no", "0", "off"):
            return False
        
        try:
            if "." not in value:
                return int(value)
            else:
                return float(value)
        except ValueError:
            pass
        
        return value
    
    def _deep_merge(self, base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
        
        
        
            
        result = base.copy()
        
        for key, value in update.items():
            if (key in result and 
                isinstance(result[key], dict) and 
                isinstance(value, dict)):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _load_env_vars_with_nesting(self, prefix: str) -> Dict[str, Any]:
        
        
        
            
        env_data = {}
        
        for key, value in os.environ.items():
            if not prefix or not key.startswith(prefix):
                continue
            
            config_key = key[len(prefix):] if prefix else key
            
            if "__" in config_key:
                parts = config_key.lower().split("__")
                converted_value = self._convert_env_value(value)
                
                current = env_data
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[parts[-1]] = converted_value
            else:
                config_key = config_key.lower()
                env_data[config_key] = self._convert_env_value(value)
        
        return env_data


@lru_cache(maxsize=32)
def load_config_with_defaults(
    config_class: Type[T],
    yaml_file: Optional[str] = None,
    env_prefix: str = "",
    defaults: Optional[Dict[str, Any]] = None
) -> T:
    
    
        
    loader = ConfigLoader(config_class)
    return loader.load_from(
        yaml_file=yaml_file,
        env_prefix=env_prefix,
        defaults=defaults
    )


