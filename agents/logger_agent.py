import logging
from utils.logging_config import setup_logging


class LoggerAgent:
    """Configure and expose application logging."""

    def __init__(self, level=logging.INFO) -> None:
        self.logger = setup_logging(level)

    def get_logger(self, name: str | None = None) -> logging.Logger:
        return logging.getLogger(name)
