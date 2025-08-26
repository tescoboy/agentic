"""Structured logging configuration."""

import logging
import sys
from typing import Optional


def configure_logging(level: str = "INFO") -> None:
    """Configure structured logging with request IDs."""
    # Create formatter
    formatter = logging.Formatter(
        fmt='{"ts": "%(asctime)s", "level": "%(levelname)s", "msg": "%(message)s", "request_id": "%(request_id)s"}',
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    root_logger.addHandler(handler)

    # Remove existing handlers to avoid duplicates
    for existing_handler in root_logger.handlers[:-1]:
        root_logger.removeHandler(existing_handler)


class RequestIdFilter(logging.Filter):
    """Add request_id to log records."""

    def __init__(self, request_id: Optional[str] = None):
        super().__init__()
        self.request_id = request_id or "no-request-id"

    def filter(self, record):
        record.request_id = self.request_id
        return True


def get_logger(name: str, request_id: Optional[str] = None) -> logging.Logger:
    """Get a logger with request ID filter."""
    logger = logging.getLogger(name)

    if request_id:
        # Remove existing request ID filters
        logger.filters = [
            f for f in logger.filters if not isinstance(f, RequestIdFilter)
        ]
        # Add new request ID filter
        logger.addFilter(RequestIdFilter(request_id))

    return logger


# Configure default logging without request_id for non-request contexts
def configure_default_logging(level: str = "INFO") -> None:
    """Configure default logging for non-request contexts."""
    formatter = logging.Formatter(
        fmt='{"ts": "%(asctime)s", "level": "%(levelname)s", "msg": "%(message)s", "request_id": "no-request-id"}',
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    root_logger.addHandler(handler)
