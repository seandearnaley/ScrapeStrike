"""Logging configuration for the project."""
import logging
import logging.config
import os
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Optional, TypeVar

from config import LOG_COLORS, LOG_FILE_PATH, LOG_NAME

F = TypeVar("F", bound=Callable[..., Any])

AppLogger = logging.Logger

# Define the logging configuration as a dictionary
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "color": {
            "()": "colorlog.ColoredFormatter",
            "format": "%(log_color)s%(levelname)s:%(message)s",
            "log_colors": LOG_COLORS,
        }
    },
    "handlers": {
        "file": {
            "class": "logging.FileHandler",
            "formatter": "color",
            "filename": os.path.abspath(LOG_FILE_PATH),
        },
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "color",
        },
    },
    "loggers": {
        LOG_NAME: {
            "handlers": ["file", "console"],
            "level": logging.INFO,
        }
    },
}


# Load the logging configuration using dictConfig
try:
    logging.config.dictConfig(LOGGING_CONFIG)
except ValueError as e:
    print(f"Error occurred during logging configuration: {str(e)}")
    raise

app_logger = logging.getLogger(LOG_NAME)
app_logger.debug("Logging is configured.")


def log(func: Any, logger: Optional[logging.Logger] = None) -> Any:
    """Decorator to log function calls and return values."""
    if logger is None:
        logger = logging.getLogger(func.__module__)

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        result = func(*args, **kwargs)
        timestamp: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info("%s: %s returned %s", timestamp, func.__name__, result)
        return result

    return wrapper
