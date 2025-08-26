"""Shared dependencies for FastAPI application."""

from collections.abc import Generator

from .config import settings
from .db import get_session


def get_settings():
    """Get application settings."""
    return settings


def get_db_session() -> Generator:
    """Get database session dependency."""
    with get_session() as session:
        yield session
