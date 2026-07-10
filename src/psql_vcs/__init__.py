"""Core imports, define PostgresMigrator and needed types of arguments
 - AuthArgs and URLArgs.
Also, setup logger.
"""

from .models import AuthArgs, URLArgs
from .modules import PostgresMigrator, setup_logger

setup_logger()

__all__ = ["PostgresMigrator", "AuthArgs", "URLArgs"]

__version__ = "0.2.1"
