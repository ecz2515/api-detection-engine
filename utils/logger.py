import logging
import os
import sys
from typing import Optional


def get_logger(name: str, log_level: Optional[int] = None) -> logging.Logger:
    """
    Configure and return a logger with the specified name.

    Args:
        name: Logger name, typically __name__ of the calling module
        log_level: Optional override for log level, uses environment variable or INFO by default

    Returns:
        A configured logger instance
    """
    # Get the logger
    logger = logging.getLogger(name)

    # Only configure handlers if they don't already exist
    if not logger.handlers:
        # Determine log level from environment variable or use default
        if log_level is None:
            env_level = os.environ.get("LOG_LEVEL", "INFO").upper()
            try:
                log_level = getattr(logging, env_level)
            except AttributeError:
                log_level = logging.INFO

        # Set logger level
        logger.setLevel(log_level)

        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)

        # Create formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Add formatter to handler
        console_handler.setFormatter(formatter)

        # Add handler to logger
        logger.addHandler(console_handler)

    return logger
