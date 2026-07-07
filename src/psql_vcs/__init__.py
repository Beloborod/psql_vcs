"""Core imports, define PostgresMigrator and needed types of arguments - AuthArgs and URLArgs.
Also, setup logger.
"""

from .modules import setup_logger, PostgresMigrator
from .models import AuthArgs, URLArgs


setup_logger()

__all__ = [
    'PostgresMigrator',
    'AuthArgs',
    'URLArgs',
]

__version__ = "0.2.1"