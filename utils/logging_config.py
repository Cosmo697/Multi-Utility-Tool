"""Logging configuration utilities."""

import logging
from logging.handlers import RotatingFileHandler
import os


LOG_DIR = "logs"
APP_LOG = os.path.join(LOG_DIR, "app.log")
DIAG_LOG = os.path.join(LOG_DIR, "diagnostics.log")


def setup_logging(level=logging.INFO):
    """Configure root logging with rotating file handlers."""
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    file_handler = RotatingFileHandler(APP_LOG, maxBytes=1024 * 1024, backupCount=3)
    file_handler.setFormatter(formatter)

    diag_handler = RotatingFileHandler(DIAG_LOG, maxBytes=512 * 1024, backupCount=2)
    diag_handler.setFormatter(formatter)
    diag_handler.setLevel(logging.DEBUG)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logging.basicConfig(
        level=level, handlers=[file_handler, diag_handler, stream_handler]
    )

    logger = logging.getLogger(__name__)
    logger.info("Logging setup complete.")

    return logger
