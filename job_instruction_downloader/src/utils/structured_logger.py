"""
Structured logging system with JSON format and operation tracking.
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Union
from logging.handlers import RotatingFileHandler


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.
        
        Args:
            record: Log record to format.
            
        Returns:
            JSON formatted log entry.
        """
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        if hasattr(record, 'operation'):
            log_entry['operation'] = record.operation
        
        if hasattr(record, 'department'):
            log_entry['department'] = record.department
        
        if hasattr(record, 'document_title'):
            log_entry['document_title'] = record.document_title
        
        if hasattr(record, 'duration'):
            log_entry['duration'] = record.duration
        
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, ensure_ascii=False)


class StructuredLogger:
    """Structured logging manager."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize structured logger.
        
        Args:
            config: Application configuration dictionary.
        """
        self.config = config
        self.setup_logging()
    
    def setup_logging(self) -> None:
        """Setup structured logging configuration."""
        logging_config = self.config.get("logging", {})
        
        log_path = logging_config.get("file_path", "logs/app.log")
        log_dir = Path(log_path).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        if logging_config.get("structured_logging", False):
            formatter: logging.Formatter = StructuredFormatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        max_size = self._parse_size(logging_config.get("max_file_size", "10MB"))
        backup_count = logging_config.get("backup_count", 5)
        
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=max_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        
        root_logger = logging.getLogger()
        
        level_name = logging_config.get("level", "INFO")
        level = getattr(logging, level_name.upper(), logging.INFO)
        root_logger.setLevel(level)
        
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        root_logger.addHandler(file_handler)
        
        if logging_config.get("console_output", True):
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
    
    def _parse_size(self, size_str: str) -> int:
        """Parse size string to bytes.
        
        Args:
            size_str: Size string (e.g., "10MB", "500KB").
            
        Returns:
            Size in bytes.
        """
        size_str = str(size_str).upper()
        if size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        else:
            try:
                return int(size_str)
            except ValueError:
                return 10 * 1024 * 1024  # Default to 10MB
    
    def log_operation(self, 
                     logger: logging.Logger, 
                     level: str, 
                     message: str, 
                     operation: Optional[str] = None, 
                     department: Optional[str] = None,
                     document_title: Optional[str] = None, 
                     duration: Optional[float] = None,
                     **kwargs: Any) -> None:
        """Log operation with structured data.
        
        Args:
            logger: Logger instance to use.
            level: Log level (debug, info, warning, error, critical).
            message: Log message.
            operation: Operation name.
            department: Department name.
            document_title: Document title.
            duration: Operation duration in seconds.
            **kwargs: Additional log data.
        """
        extra = {}
        if operation:
            extra['operation'] = operation
        if department:
            extra['department'] = department
        if document_title:
            extra['document_title'] = document_title
        if duration is not None:
            extra['duration'] = str(duration)
        
        for key, value in kwargs.items():
            extra[key] = value
        
        level_method = getattr(logger, level.lower(), logger.info)
        if not callable(level_method):
            level_method = logger.info
        level_method(message, extra=extra)
    
    def timed_operation(self, 
                       logger: logging.Logger, 
                       level: str, 
                       message: str, 
                       operation: Optional[str] = None, 
                       **kwargs: Any) -> 'TimedOperation':
        """Create context manager for timing operations.
        
        Args:
            logger: Logger instance to use.
            level: Log level (debug, info, warning, error, critical).
            message: Log message.
            operation: Operation name.
            **kwargs: Additional log data.
            
        Returns:
            TimedOperation context manager.
        """
        return TimedOperation(self, logger, level, message, operation, **kwargs)


class TimedOperation:
    """Context manager for timing operations."""
    
    def __init__(self, 
                structured_logger: StructuredLogger, 
                logger: logging.Logger, 
                level: str, 
                message: str, 
                operation: Optional[str] = None, 
                **kwargs: Any):
        """Initialize timed operation.
        
        Args:
            structured_logger: StructuredLogger instance.
            logger: Logger instance to use.
            level: Log level (debug, info, warning, error, critical).
            message: Log message.
            operation: Operation name.
            **kwargs: Additional log data.
        """
        self.structured_logger = structured_logger
        self.logger = logger
        self.level = level
        self.message = message
        self.operation = operation
        self.kwargs = kwargs
        self.start_time: float = 0.0
    
    def __enter__(self) -> 'TimedOperation':
        """Start timing operation.
        
        Returns:
            Self for context manager.
        """
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """End timing operation and log result.
        
        Args:
            exc_type: Exception type if raised.
            exc_val: Exception value if raised.
            exc_tb: Exception traceback if raised.
        """
        duration = time.time() - self.start_time
        
        if exc_type:
            self.structured_logger.log_operation(
                self.logger, 
                "error", 
                f"{self.message} failed: {exc_val}", 
                operation=self.operation, 
                duration=duration, 
                **self.kwargs
            )
        else:
            self.structured_logger.log_operation(
                self.logger, 
                self.level, 
                f"{self.message} completed", 
                operation=self.operation, 
                duration=duration, 
                **self.kwargs
            )
