"""
Enhanced error handling with exponential backoff and retry logic.
"""

import logging
import time
import random
from typing import Any, Callable, Optional, Dict, TypeVar, List
from functools import wraps


T = TypeVar('T')


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(self,
                 max_attempts: int = 3,
                 base_delay: float = 1.0,
                 max_delay: float = 60.0,
                 exponential_base: float = 2.0,
                 jitter: bool = True):
        """Initialize retry configuration.

        Args:
            max_attempts: Maximum number of retry attempts.
            base_delay: Base delay between retries in seconds.
            max_delay: Maximum delay between retries in seconds.
            exponential_base: Base for exponential backoff calculation.
            jitter: Whether to add randomness to delay times.
        """
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter


class EnhancedErrorHandler:
    """Enhanced error handling with exponential backoff."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize error handler.

        Args:
            config: Application configuration dictionary.
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        error_config = config.get("error_handling", {})
        self.retry_config = RetryConfig(
            max_attempts=error_config.get("retry_attempts", 3),
            base_delay=error_config.get("retry_delay", 5),
            exponential_base=2.0 if error_config.get("exponential_backoff", True) else 1.0
        )

    def retry_with_backoff(self, operation: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Execute operation with exponential backoff retry.

        Args:
            operation: Function to execute with retry logic.
            *args: Positional arguments for the operation.
            **kwargs: Keyword arguments for the operation.

        Returns:
            Result of the operation.

        Raises:
            Exception: The last exception encountered after all retries.
        """
        last_exception = None

        for attempt in range(self.retry_config.max_attempts):
            try:
                return operation(*args, **kwargs)

            except Exception as e:
                last_exception = e

                if attempt == self.retry_config.max_attempts - 1:
                    self.logger.error(f"Operation failed after {self.retry_config.max_attempts} attempts: {e}")
                    break

                delay = self._calculate_delay(attempt)
                self.logger.warning(
                    f"Operation failed (attempt {attempt + 1}/{self.retry_config.max_attempts}): {e}. "
                    f"Retrying in {delay:.2f}s"
                )
                time.sleep(delay)

        if last_exception:
            raise last_exception

        raise RuntimeError("Unexpected error in retry logic")

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for exponential backoff.

        Args:
            attempt: Current attempt number (0-based).

        Returns:
            Delay time in seconds.
        """
        delay = self.retry_config.base_delay * (self.retry_config.exponential_base ** attempt)
        delay = min(delay, self.retry_config.max_delay)

        if self.retry_config.jitter:
            delay *= (0.5 + random.random() * 0.5)

        return delay

    def retry_on_exception(self,
                           exceptions: Optional[List[type]] = None,
                           max_attempts: Optional[int] = None,
                           base_delay: Optional[float] = None):
        """Decorator for retrying functions on specific exceptions.

        Args:
            exceptions: List of exception types to retry on. If None, retries on all exceptions.
            max_attempts: Override default max attempts.
            base_delay: Override default base delay.

        Returns:
            Decorated function with retry logic.
        """
        if exceptions is None:
            exceptions = [Exception]

        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> T:
                max_retry = max_attempts or self.retry_config.max_attempts
                delay = base_delay or self.retry_config.base_delay

                last_exception = None

                for attempt in range(max_retry):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        if not any(isinstance(e, exc_type) for exc_type in exceptions):
                            raise
                        last_exception = e

                        if attempt == max_retry - 1:
                            self.logger.error(f"Function {func.__name__} failed after {max_retry} attempts: {e}")
                            break

                        retry_delay = delay * (self.retry_config.exponential_base ** attempt)
                        retry_delay = min(retry_delay, self.retry_config.max_delay)

                        if self.retry_config.jitter:
                            retry_delay *= (0.5 + random.random() * 0.5)

                        self.logger.warning(
                            f"Function {func.__name__} failed (attempt {attempt + 1}/{max_retry}): {e}. "
                            f"Retrying in {retry_delay:.2f}s"
                        )
                        time.sleep(retry_delay)

                if last_exception:
                    raise last_exception

                raise RuntimeError("Unexpected error in retry decorator")

            return wrapper
        return decorator
