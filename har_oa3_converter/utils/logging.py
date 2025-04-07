"""Logging utilities for har-oa3-converter.

This module provides consistent logging functionality across the entire package.
It configures loggers with appropriate formats and log levels based on configuration.
"""

import logging
import os
import sys
from typing import Any, Dict, Optional, Union

# Default log format includes timestamp, level, and message
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Default console format is simpler
CONSOLE_LOG_FORMAT = "%(levelname)s: %(message)s"

# Map string log levels to logging module constants
LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger by name.

    Args:
        name: Logger name, typically the module name using __name__

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Avoid duplicate handlers if logger already exists
    if logger.handlers:
        return logger

    # Get log level from environment or default to INFO
    log_level_name = os.environ.get("HAR_OA3_LOG_LEVEL", "info").lower()
    log_level = LOG_LEVELS.get(log_level_name, logging.INFO)

    logger.setLevel(log_level)

    # Add console handler if not running in a non-interactive environment
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(CONSOLE_LOG_FORMAT))
    console_handler.setLevel(log_level)
    logger.addHandler(console_handler)

    return logger


def configure_logging(
    log_level: Optional[Union[str, int]] = None,
    log_file: Optional[str] = None,
    log_format: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
) -> None:
    """Configure global logging settings.

    Args:
        log_level: Log level as string name or integer constant
        log_file: Path to log file (if not provided, logs only go to console)
        log_format: Custom log format string
        config: Additional logging configuration options
    """
    # Allow string or integer log levels
    if isinstance(log_level, str):
        level = LOG_LEVELS.get(log_level.lower(), logging.INFO)
    else:
        level = log_level or logging.INFO

    # Set environment variable for future logger instances
    for level_name, level_value in LOG_LEVELS.items():
        if level_value == level:
            os.environ["HAR_OA3_LOG_LEVEL"] = level_name
            break

    # Basic configuration
    logging.basicConfig(
        level=level,
        format=log_format or DEFAULT_LOG_FORMAT,
        filename=log_file,
        filemode="a" if log_file else None,
    )

    # Configure root logger for console output if no file is specified
    if not log_file:
        root_logger = logging.getLogger()
        if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
            console = logging.StreamHandler(sys.stdout)
            console.setFormatter(logging.Formatter(CONSOLE_LOG_FORMAT))
            console.setLevel(level)
            root_logger.addHandler(console)

    # Apply any additional configuration
    if config:
        logging.config.dictConfig(config)
