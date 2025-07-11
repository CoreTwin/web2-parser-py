"""
Tests for enhanced error handler.
"""

import pytest
from unittest.mock import Mock

from job_instruction_downloader.src.utils.error_handler import EnhancedErrorHandler, RetryConfig


@pytest.fixture
def error_config():
    """Error handling configuration fixture."""
    return {
        "error_handling": {
            "retry_attempts": 3,
            "retry_delay": 0.1,
            "exponential_backoff": True
        }
    }


@pytest.fixture
def error_handler(error_config):
    """Error handler fixture."""
    return EnhancedErrorHandler(error_config)


class TestEnhancedErrorHandler:
    """Test cases for EnhancedErrorHandler."""

    def test_retry_config_initialization(self):
        """Test retry configuration initialization."""
        config = RetryConfig(max_attempts=5, base_delay=2.0)

        assert config.max_attempts == 5
        assert config.base_delay == 2.0
        assert config.exponential_base == 2.0
        assert config.jitter is True

    def test_successful_operation(self, error_handler):
        """Test successful operation without retries."""
        mock_operation = Mock(return_value="success")

        result = error_handler.retry_with_backoff(mock_operation, "arg1", key="value")

        assert result == "success"
        assert mock_operation.call_count == 1
        mock_operation.assert_called_with("arg1", key="value")

    def test_retry_on_failure(self, error_handler):
        """Test retry behavior on failures."""
        mock_operation = Mock(side_effect=[Exception("error1"), Exception("error2"), "success"])

        result = error_handler.retry_with_backoff(mock_operation)

        assert result == "success"
        assert mock_operation.call_count == 3

    def test_max_retries_exceeded(self, error_handler):
        """Test behavior when max retries are exceeded."""
        mock_operation = Mock(side_effect=Exception("persistent error"))

        with pytest.raises(Exception, match="persistent error"):
            error_handler.retry_with_backoff(mock_operation)

        assert mock_operation.call_count == 3

    def test_delay_calculation(self, error_handler):
        """Test exponential backoff delay calculation."""
        delay_0 = error_handler._calculate_delay(0)
        delay_1 = error_handler._calculate_delay(1)
        delay_2 = error_handler._calculate_delay(2)

        assert delay_0 < delay_1 < delay_2
        assert delay_0 >= 0.025  # With jitter, minimum is 50% of base delay
        assert delay_2 <= error_handler.retry_config.max_delay

    def test_retry_decorator(self, error_handler):
        """Test retry decorator functionality."""
        call_count = 0

        @error_handler.retry_on_exception([ValueError], max_attempts=2)
        def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("test error")
            return "success"

        result = failing_function()

        assert result == "success"
        assert call_count == 2
