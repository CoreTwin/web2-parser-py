"""
Tests for structured logging system.
"""

import pytest
import json
import logging
from unittest.mock import patch

from job_instruction_downloader.src.utils.structured_logger import (
    StructuredLogger, StructuredFormatter, TimedOperation
)


@pytest.fixture
def logging_config():
    """Logging configuration fixture."""
    return {
        "logging": {
            "file_path": "logs/test.log",
            "max_file_size": "1MB",
            "backup_count": 3,
            "console_output": False,
            "structured_logging": True,
            "level": "INFO"
        }
    }


@pytest.fixture
def structured_logger(logging_config, tmp_path):
    """Structured logger fixture."""
    logging_config["logging"]["file_path"] = str(tmp_path / "test.log")
    return StructuredLogger(logging_config)


class TestStructuredFormatter:
    """Test cases for StructuredFormatter."""

    def test_format_basic_record(self):
        """Test formatting of basic log record."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.module = "test_module"
        record.funcName = "test_function"

        result = formatter.format(record)
        log_data = json.loads(result)

        assert log_data["level"] == "INFO"
        assert log_data["logger"] == "test_logger"
        assert log_data["message"] == "Test message"
        assert log_data["module"] == "test_module"
        assert log_data["function"] == "test_function"
        assert log_data["line"] == 10
        assert "timestamp" in log_data

    def test_format_with_extra_fields(self):
        """Test formatting with extra structured fields."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.module = "test_module"
        record.funcName = "test_function"
        record.operation = "test_operation"
        record.department = "test_department"
        record.document_title = "test_document"
        record.duration = 1.5

        result = formatter.format(record)
        log_data = json.loads(result)

        assert log_data["operation"] == "test_operation"
        assert log_data["department"] == "test_department"
        assert log_data["document_title"] == "test_document"
        assert log_data["duration"] == 1.5


class TestStructuredLogger:
    """Test cases for StructuredLogger."""

    def test_initialization(self, structured_logger):
        """Test structured logger initialization."""
        assert structured_logger.config is not None

    def test_parse_size(self, structured_logger):
        """Test size string parsing."""
        assert structured_logger._parse_size("10MB") == 10 * 1024 * 1024
        assert structured_logger._parse_size("500KB") == 500 * 1024
        assert structured_logger._parse_size("1024") == 1024
        assert structured_logger._parse_size("invalid") == 10 * 1024 * 1024

    def test_log_operation(self, structured_logger):
        """Test structured operation logging."""
        logger = logging.getLogger("test")

        with patch.object(logger, 'info') as mock_info:
            structured_logger.log_operation(
                logger, "info", "Test message",
                operation="test_op", department="test_dept"
            )

            mock_info.assert_called_once()
            args, kwargs = mock_info.call_args
            assert args[0] == "Test message"
            assert kwargs["extra"]["operation"] == "test_op"
            assert kwargs["extra"]["department"] == "test_dept"

    def test_timed_operation_context_manager(self, structured_logger):
        """Test timed operation context manager."""
        logger = logging.getLogger("test")

        with patch.object(structured_logger, 'log_operation') as mock_log:
            with structured_logger.timed_operation(
                logger, "info", "Test operation", operation="test"
            ):
                pass

            mock_log.assert_called_once()
            args, kwargs = mock_log.call_args
            assert "Test operation completed" in args[2]
            assert kwargs["operation"] == "test"
            assert "duration" in kwargs


class TestTimedOperation:
    """Test cases for TimedOperation."""

    def test_successful_operation(self, structured_logger):
        """Test successful timed operation."""
        logger = logging.getLogger("test")

        with patch.object(structured_logger, 'log_operation') as mock_log:
            with TimedOperation(structured_logger, logger, "info", "Test", "test_op"):
                pass

            mock_log.assert_called_once()
            args, kwargs = mock_log.call_args
            assert "Test completed" in args[2]
            assert kwargs["operation"] == "test_op"

    def test_failed_operation(self, structured_logger):
        """Test failed timed operation."""
        logger = logging.getLogger("test")

        with patch.object(structured_logger, 'log_operation') as mock_log:
            try:
                with TimedOperation(structured_logger, logger, "info", "Test", "test_op"):
                    raise ValueError("Test error")
            except ValueError:
                pass

            mock_log.assert_called_once()
            args, kwargs = mock_log.call_args
            assert "Test failed" in args[2]
            assert "Test error" in args[2]
            assert kwargs["operation"] == "test_op"
