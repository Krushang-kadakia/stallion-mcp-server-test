import logging
import re
import sys
from typing import Any
from app.config.settings import settings


class SecretMaskingFormatter(logging.Formatter):
    """
    Custom formatter that scrubs potential JWT tokens and secrets from log messages.
    """
    JWT_PATTERN = re.compile(r'eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+')

    def format(self, record: logging.LogRecord) -> str:
        original = super().format(record)
        # Scrub JWT pattern
        scrubbed = self.JWT_PATTERN.sub("[REDACTED_JWT]", original)
        return scrubbed


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = SecretMaskingFormatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
    return logger
