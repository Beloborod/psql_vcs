import logging


def setup_logger():
    logger = logging.getLogger(__name__)

    logger.addHandler(logging.NullHandler())
