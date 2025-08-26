"""Database configuration and session management."""

from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import text
from sqlmodel import Session, SQLModel, create_engine

from .config import settings


def ensure_data_directory():
    """Ensure the data directory exists."""
    data_dir = Path("./data")
    data_dir.mkdir(exist_ok=True)


def get_engine():
    """Get database engine from settings with proper configuration."""
    # Ensure data directory exists
    ensure_data_directory()

    # Get database URL with fallback
    db_url = getattr(settings, "database_url", "sqlite:///./data/adcp_demo.sqlite3")

    # Create engine with SQLite-specific configuration
    engine = create_engine(
        db_url,
        echo=False,  # Set to True for SQL debugging
        connect_args=(
            {
                "check_same_thread": False,
                "timeout": 30.0,
            }
            if "sqlite" in db_url
            else {}
        ),
    )

    # Set SQLite PRAGMAs for better performance and safety
    if "sqlite" in db_url:
        with engine.connect() as conn:
            conn.execute(text("PRAGMA journal_mode=WAL"))
            conn.execute(text("PRAGMA synchronous=NORMAL"))
            conn.execute(text("PRAGMA foreign_keys=ON"))
            conn.execute(text("PRAGMA cache_size=10000"))
            conn.execute(text("PRAGMA temp_store=MEMORY"))
            conn.commit()

    return engine


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Context manager for database sessions."""
    engine = get_engine()
    with Session(engine) as session:
        yield session


def init_db():
    """Initialize database by creating all tables if they don't exist."""
    # Import all models to ensure they are registered with SQLModel
    from .models.tenant import Tenant
    from .models.product import Product
    from .models.agent_settings import AgentSettings
    from .models.external_agent import ExternalAgent

    engine = get_engine()

    # Only create tables if they don't exist (never drop)
    SQLModel.metadata.create_all(engine, checkfirst=True)
