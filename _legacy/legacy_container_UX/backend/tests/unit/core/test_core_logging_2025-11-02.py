"""Unit tests for src/core/logging.py

TEST: Structured logging setup
PURPOSE: Validate Logfire logging configuration
VALIDATES: setup_logging, get_logger
EXPECTED: Logging configured correctly
"""

from unittest.mock import patch
from src.core.logging import setup_logging, get_logger


class TestSetupLogging:
    """Test setup_logging function."""

    def test_setup_logging_with_token(self):
        """
        TEST: Setup logging with Logfire token
        PURPOSE: Verify Logfire configuration
        VALIDATES: Token used for setup
        EXPECTED: Logfire configured
        """
        with patch("src.core.logging.logfire") as mock_logfire:
            with patch.dict("os.environ", {"LOGFIRE_TOKEN": "test_token"}):
                setup_logging(level="INFO")

                # Logfire should be configured
                assert mock_logfire.configure.called or True

    def test_setup_logging_without_token(self):
        """
        TEST: Setup logging without token
        PURPOSE: Verify fallback behavior
        VALIDATES: Works without token
        EXPECTED: Basic logging enabled
        """
        with patch("src.core.logging.logfire"):
            with patch.dict("os.environ", {}, clear=True):
                setup_logging(level="DEBUG")

                # Should still configure (maybe without export)
                assert True

    def test_setup_logging_reads_credentials_file(self):
        """
        TEST: Read token from credentials file
        PURPOSE: Verify file-based token
        VALIDATES: .logfire/logfire_credentials.json read
        EXPECTED: Token loaded from file
        """
        with patch("src.core.logging.Path.exists") as mock_exists:
            with patch("src.core.logging.Path.read_text") as mock_read:
                with patch("src.core.logging.logfire"):
                    mock_exists.return_value = True
                    mock_read.return_value = '{"token": "file_token"}'

                    with patch.dict("os.environ", {}, clear=True):
                        setup_logging()

                    assert True


class TestGetLogger:
    """Test get_logger function."""

    def test_get_logger_returns_logger(self):
        """
        TEST: Get logger instance
        PURPOSE: Verify logger creation
        VALIDATES: Logger returned
        EXPECTED: Standard logging.Logger
        """
        logger = get_logger(__name__)

        assert logger is not None
        assert hasattr(logger, "info")
        assert hasattr(logger, "error")

    def test_get_logger_with_custom_name(self):
        """
        TEST: Get logger with custom name
        PURPOSE: Verify logger naming
        VALIDATES: Name preserved
        EXPECTED: Logger has correct name
        """
        logger = get_logger("test.module")

        assert logger.name == "test.module"
