import structlog
import logging
from logging.handlers import RotatingFileHandler
import os

# Define logger at module level
logger = structlog.get_logger()


def setup_logging():
    log_dir = "logs"  # Use local directory
    os.makedirs(log_dir, exist_ok=True)

    file_info = RotatingFileHandler(
        f"{log_dir}/app.log", maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_debug = RotatingFileHandler(
        f"{log_dir}/debug.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_error = RotatingFileHandler(
        f"{log_dir}/error.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )

    file_info.setLevel(logging.INFO)
    file_debug.setLevel(logging.DEBUG)
    file_error.setLevel(logging.ERROR)

    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    root_logger = logging.getLogger()
    root_logger.addHandler(file_info)
    root_logger.addHandler(file_debug)
    root_logger.addHandler(file_error)
    root_logger.setLevel(logging.DEBUG)
