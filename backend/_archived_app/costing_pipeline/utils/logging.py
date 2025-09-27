import logging, os
from ..config_adapter import SETTINGS


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.handlers.clear()  # Remove existing handlers
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger