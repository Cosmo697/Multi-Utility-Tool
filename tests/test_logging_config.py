import logging
from utils import logging_config

def test_logging_config_sets_rotating_handler():
    logging_config.setup_logging()
    root_logger = logging.getLogger()
    handlers = [h for h in root_logger.handlers if isinstance(h, logging.handlers.RotatingFileHandler)]
    assert handlers, "RotatingFileHandler should be present in root logger"
