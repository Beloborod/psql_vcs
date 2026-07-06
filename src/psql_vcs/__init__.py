from .modules import setup_logger, PostgresMigrator
from .models import AuthArgs, URLArgs
from importlib.metadata import version, PackageNotFoundError


setup_logger()

__all__ = [
    'PostgresMigrator',
    'AuthArgs',
    'URLArgs',
]

try:
    __version__ = version(__name__)
except PackageNotFoundError:
    __version__ = "0.0.1a0"
