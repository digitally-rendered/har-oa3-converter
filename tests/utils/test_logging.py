"""Tests for logging utilities."""

import io
import logging
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

from har_oa3_converter.utils import configure_logging, get_logger


def test_get_logger():
    """Test that get_logger returns a logger with expected configuration."""
    logger = get_logger("test_logger")
    assert logger.name == "test_logger"
    assert isinstance(logger, logging.Logger)

    # Check that the logger has at least one handler
    assert len(logger.handlers) > 0

    # Check that the handler is a StreamHandler
    assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers)


def test_get_logger_cached():
    """Test that get_logger returns the same logger for the same name."""
    # This test verifies that calling get_logger twice with the same name
    # returns the same logger instance and doesn't add duplicate handlers

    # Clean up existing loggers to ensure test isolation
    logging.Logger.manager.loggerDict.pop("test_logger_cached", None)

    # Get two loggers with the same name
    logger1 = get_logger("test_logger_cached")
    handler_count = len(logger1.handlers)  # Should have 1 handler after first call

    logger2 = get_logger("test_logger_cached")

    # Verify it's the same object
    assert logger1 is logger2

    # Verify no duplicate handlers were added
    assert len(logger2.handlers) == handler_count


@patch.dict(os.environ, {}, clear=True)
def test_log_levels():
    """Test that log levels are correctly set based on environment variable."""
    # Test with different log levels set through environment variables

    # Helper function to get a fresh logger with a specific environment setting
    def get_test_logger(log_level, logger_name):
        # Clear any existing logger
        logging.Logger.manager.loggerDict.pop(logger_name, None)
        # Set environment variable
        os.environ["HAR_OA3_LOG_LEVEL"] = log_level
        # Get logger
        return get_logger(logger_name)

    # Test debug level
    logger = get_test_logger("debug", "test_debug_logger")
    assert logger.level == logging.DEBUG
    assert logger.handlers[0].level == logging.DEBUG

    # Test info level
    logger = get_test_logger("info", "test_info_logger")
    assert logger.level == logging.INFO
    assert logger.handlers[0].level == logging.INFO

    # Test warning level
    logger = get_test_logger("warning", "test_warning_logger")
    assert logger.level == logging.WARNING
    assert logger.handlers[0].level == logging.WARNING

    # Test error level
    logger = get_test_logger("error", "test_error_logger")
    assert logger.level == logging.ERROR
    assert logger.handlers[0].level == logging.ERROR

    # Test invalid level (should default to INFO)
    logger = get_test_logger("invalid_level", "test_invalid_logger")
    assert logger.level == logging.INFO
    assert logger.handlers[0].level == logging.INFO


@patch.dict(os.environ, {}, clear=True)
def test_configure_logging():
    """Test the configure_logging function with various options."""
    # Reset for clean testing
    with patch("logging.basicConfig") as mock_config:
        # Test with level parameter
        configure_logging(log_level="debug")
        mock_config.assert_called_once()
        kwargs = mock_config.call_args[1]
        assert kwargs["level"] == logging.DEBUG
        mock_config.reset_mock()

        # Test with integer level parameter
        configure_logging(log_level=logging.ERROR)
        mock_config.assert_called_once()
        kwargs = mock_config.call_args[1]
        assert kwargs["level"] == logging.ERROR
        mock_config.reset_mock()

        # Test with log file parameter
        configure_logging(log_file="test.log")
        mock_config.assert_called_once()
        kwargs = mock_config.call_args[1]
        assert kwargs["filename"] == "test.log"
        assert kwargs["filemode"] == "a"
        mock_config.reset_mock()

        # Test with format parameter
        configure_logging(log_format="%(levelname)s - %(message)s")
        mock_config.assert_called_once()
        kwargs = mock_config.call_args[1]
        assert "format" in kwargs
        assert kwargs["format"] == "%(levelname)s - %(message)s"


def test_logging_output():
    """Test that log messages are correctly output."""
    # Use a StringIO buffer to capture the output
    log_buffer = io.StringIO()

    # Set the environment variable for debug level
    os.environ["HAR_OA3_LOG_LEVEL"] = "debug"

    # Clear any existing logger
    logging.Logger.manager.loggerDict.pop("test_output_logger", None)

    # Create a handler that writes to our buffer instead of stdout
    with patch("sys.stdout", log_buffer):
        # Get logger through the module function
        logger = get_logger("test_output_logger")

        # Log messages at different levels
        logger.debug("This is a debug message")
        logger.info("This is an info message")
        logger.warning("This is a warning message")
        logger.error("This is an error message")

        # Get output from buffer
        output = log_buffer.getvalue()

        # Check that all messages are present - since we patched sys.stdout
        # and the handler uses the CONSOLE_LOG_FORMAT
        assert "DEBUG: This is a debug message" in output
        assert "INFO: This is an info message" in output
        assert "WARNING: This is a warning message" in output
        assert "ERROR: This is an error message" in output

    # Clean up
    os.environ.pop("HAR_OA3_LOG_LEVEL", None)
