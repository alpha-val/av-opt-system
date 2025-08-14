import logging, os
from ..config_adapter import SETTINGS

def get_logger(name: str) -> logging.Logger:
    level = getattr(logging, (SETTINGS.log_level or 'INFO').upper(), logging.INFO)
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(level)
        h = logging.StreamHandler()
        h.setLevel(level)
        h.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
        logger.addHandler(h)
    return logger
