import logging
import os
from typing import Optional

from utils.config import CONFIG


def setup_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Create a consistent console logger.
    Priority: explicit level arg > JY_LOG_LEVEL env > INFO.
    """
    raw_level = (level or CONFIG.log_level or os.getenv("JY_LOG_LEVEL") or "INFO").upper()
    log_level = getattr(logging, raw_level, logging.INFO)

    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
        logger.addHandler(handler)

    logger.propagate = False
    return logger
