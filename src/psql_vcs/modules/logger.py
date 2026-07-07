"""Setup logger used in lib."""

import logging


def setup_logger() -> None:
    """Setup logger.

    :rtype: None
    """
    logger = logging.getLogger(__name__)

    logger.addHandler(logging.NullHandler())
