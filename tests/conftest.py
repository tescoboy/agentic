"""Pytest configuration for test database setup."""

import os
import tempfile

import pytest
from sqlalchemy import text
from sqlmodel import Session

from app.db import get_engine, init_db


@pytest.fixture(scope="session")
def test_db_path():
    """Create a temporary test database path."""
    with tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False) as tmp:
        db_path = tmp.name
    yield db_path
    # Cleanup
    try:
        os.unlink(db_path)
    except OSError:
        pass


@pytest.fixture(scope="session")
def test_db_url(test_db_path):
    """Get the test database URL."""
    return f"sqlite:///{test_db_path}"


@pytest.fixture(scope="session", autouse=True)
def setup_test_db(test_db_url):
    """Set up the test database for the entire test session."""
    # Set environment variable for the test session
    os.environ["DATABASE_URL"] = test_db_url

    # Initialize the database
    init_db()

    yield

    # Cleanup
    try:
        engine = get_engine()
        engine.dispose()
    except Exception:
        pass


@pytest.fixture(autouse=True)
def clean_db(request):
    """Clean the database before and after each test."""
    # Skip cleaning for tests marked with no_clean_db
    if hasattr(request.node, "get_closest_marker") and request.node.get_closest_marker(
        "no_clean_db"
    ):
        yield
        return

    engine = get_engine()

    # Clear all data from tables before test
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM product"))
        conn.execute(text("DELETE FROM externalagent"))
        conn.execute(text("DELETE FROM agentsettings"))
        conn.execute(text("DELETE FROM tenant"))
        conn.commit()

    yield

    # Clear all data from tables after test
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM product"))
        conn.execute(text("DELETE FROM externalagent"))
        conn.execute(text("DELETE FROM agentsettings"))
        conn.execute(text("DELETE FROM tenant"))
        conn.commit()


@pytest.fixture
def db_session():
    """Create a database session for each test."""
    engine = get_engine()
    with Session(engine) as session:
        yield session
        # Rollback any changes made during the test
        session.rollback()


@pytest.fixture
def client():
    """Create a test client with initialized database."""
    from fastapi.testclient import TestClient

    from app.main import app

    return TestClient(app)
