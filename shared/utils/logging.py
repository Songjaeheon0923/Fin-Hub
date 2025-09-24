"""
Unified Logging Configuration for Fin-Hub
Provides structured JSON logging with correlation IDs
"""

import logging
import logging.config
import sys
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from contextvars import ContextVar
from pathlib import Path


# Context variable for correlation ID (tracks requests across services)
correlation_id_ctx: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)


class CorrelationIDFilter(logging.Filter):
    """Add correlation ID to log records"""

    def filter(self, record: logging.LogRecord) -> bool:
        correlation_id = correlation_id_ctx.get()
        record.correlation_id = correlation_id or "none"
        return True


class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging"""

    def __init__(self, service_name: str = "fin-hub"):
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "service": self.service_name,
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": getattr(record, 'correlation_id', 'none'),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in {
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                'thread', 'threadName', 'processName', 'process', 'getMessage',
                'correlation_id', 'message', 'asctime'
            }:
                if not key.startswith('_'):
                    log_entry[key] = value

        return json.dumps(log_entry, default=str, ensure_ascii=False)


def setup_logging(
    service_name: str,
    log_level: str = "INFO",
    log_format: str = "json",
    log_file_path: Optional[str] = None,
    enable_console: bool = True
) -> logging.Logger:
    """
    Setup unified logging configuration

    Args:
        service_name: Name of the service (hub-server, market-spoke, etc.)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Format type ('json' or 'text')
        log_file_path: Path to log file (optional)
        enable_console: Whether to enable console logging

    Returns:
        Configured logger instance
    """

    # Create formatters
    if log_format.lower() == "json":
        formatter = JSONFormatter(service_name)
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - [%(correlation_id)s] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

    # Configure handlers
    handlers = []

    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.addFilter(CorrelationIDFilter())
        handlers.append(console_handler)

    if log_file_path:
        # Ensure log directory exists
        log_path = Path(log_file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.addFilter(CorrelationIDFilter())
        handlers.append(file_handler)

    # Logging configuration
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": JSONFormatter,
                "service_name": service_name
            },
            "text": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - [%(correlation_id)s] - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            }
        },
        "filters": {
            "correlation": {
                "()": CorrelationIDFilter
            }
        },
        "handlers": {},
        "loggers": {
            "": {  # Root logger
                "level": log_level.upper(),
                "handlers": [],
                "propagate": False
            },
            service_name: {
                "level": log_level.upper(),
                "handlers": [],
                "propagate": False
            },
            # Third-party library loggers
            "aiohttp": {
                "level": "WARNING",
                "handlers": [],
                "propagate": True
            },
            "urllib3": {
                "level": "WARNING",
                "handlers": [],
                "propagate": True
            },
            "asyncio": {
                "level": "WARNING",
                "handlers": [],
                "propagate": True
            }
        }
    }

    # Add handlers to config
    handler_names = []

    if enable_console:
        logging_config["handlers"]["console"] = {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": log_format,
            "filters": ["correlation"]
        }
        handler_names.append("console")

    if log_file_path:
        logging_config["handlers"]["file"] = {
            "class": "logging.FileHandler",
            "filename": log_file_path,
            "encoding": "utf-8",
            "formatter": log_format,
            "filters": ["correlation"]
        }
        handler_names.append("file")

    # Assign handlers to loggers
    for logger_name in ["", service_name]:
        logging_config["loggers"][logger_name]["handlers"] = handler_names

    # Apply configuration
    logging.config.dictConfig(logging_config)

    # Get service logger
    logger = logging.getLogger(service_name)
    logger.info(f"Logging initialized for {service_name}", extra={
        "log_level": log_level,
        "log_format": log_format,
        "log_file": log_file_path,
        "console_enabled": enable_console
    })

    return logger


def set_correlation_id(correlation_id: Optional[str] = None) -> str:
    """
    Set correlation ID for current context

    Args:
        correlation_id: Correlation ID (generates UUID if None)

    Returns:
        The correlation ID that was set
    """
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())

    correlation_id_ctx.set(correlation_id)
    return correlation_id


def get_correlation_id() -> Optional[str]:
    """Get current correlation ID"""
    return correlation_id_ctx.get()


def clear_correlation_id():
    """Clear correlation ID from context"""
    correlation_id_ctx.set(None)


class LoggerMixin:
    """Mixin class to add logging capabilities to any class"""

    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class"""
        if not hasattr(self, '_logger'):
            self._logger = logging.getLogger(
                f"{self.__class__.__module__}.{self.__class__.__name__}"
            )
        return self._logger

    def log_method_call(self, method_name: str, **kwargs):
        """Log method call with parameters"""
        self.logger.debug(
            f"Calling {method_name}",
            extra={"method": method_name, "parameters": kwargs}
        )

    def log_method_result(self, method_name: str, result: Any = None, execution_time: float = None):
        """Log method result"""
        extra_data = {"method": method_name}
        if execution_time is not None:
            extra_data["execution_time"] = execution_time
        if result is not None:
            extra_data["result_type"] = type(result).__name__

        self.logger.debug(f"Method {method_name} completed", extra=extra_data)

    def log_error(self, message: str, exc: Exception = None, **context):
        """Log error with context"""
        extra_data = context.copy()
        if exc:
            extra_data["exception_type"] = type(exc).__name__

        self.logger.error(message, exc_info=exc, extra=extra_data)


def log_async_method(logger: logging.Logger):
    """Decorator to log async method calls and results"""
    def decorator(func):
        import functools
        import time

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            method_name = f"{func.__qualname__}"
            correlation_id = get_correlation_id()

            logger.debug(
                f"Starting async method {method_name}",
                extra={
                    "method": method_name,
                    "correlation_id": correlation_id,
                    "parameters": {k: v for k, v in kwargs.items() if not k.startswith('_')}
                }
            )

            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time

                logger.debug(
                    f"Completed async method {method_name}",
                    extra={
                        "method": method_name,
                        "correlation_id": correlation_id,
                        "execution_time": execution_time,
                        "result_type": type(result).__name__ if result is not None else None
                    }
                )
                return result

            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    f"Error in async method {method_name}",
                    exc_info=e,
                    extra={
                        "method": method_name,
                        "correlation_id": correlation_id,
                        "execution_time": execution_time,
                        "exception_type": type(e).__name__
                    }
                )
                raise

        return wrapper
    return decorator