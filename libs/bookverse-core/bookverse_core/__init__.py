

__version__ = "0.1.0"
__author__ = "BookVerse Team"
__email__ = "team@bookverse.com"

from .auth import AuthUser
from .config import BaseConfig, ConfigLoader

__all__ = [
    "AuthUser",
    "BaseConfig",
    "ConfigLoader",
    "__version__",
]
