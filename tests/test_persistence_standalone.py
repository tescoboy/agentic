"""Standalone persistence test that doesn't use conftest.py fixtures."""

import os
import tempfile

from sqlalchemy import text
from sqlmodel import Session, SQLModel, create_engine

from app.repositories.products import ProductRepository
from app.repositories.tenants import TenantRepository


def test_data_persistence_across_restarts_standalone():
    """Test that data persists across simulated server restarts using a standalone database."""
    # Create a temporary database file for this test only
    with tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False) as tmp:
        db_path = tmp.name
    print(f"DEBUG: Using temporary database file: {db_path}")

    try:
        # Set up the test database
        db_url = f"sqlite:///{db_path}"
        original_db_url = os.environ.get("DATABASE_URL")
        os.environ["DATABASE_URL"] = db_url

        # Get engine and initialize database
        # Create a new settings object with the updated DATABASE_URL
        from app.config import Settings

        test_settings = Settings()
        test_settings.database_url = db_url

        # Create engine directly with the test settings
        from app.db import ensure_data_directory

        ensure_data_directory()

        engine = create_engine(
            db_url,
            echo=False,
            connect_args={
                "check_same_thread": False,
                "timeout": 30.0,
            },
        )

        # Set SQLite PRAGMAs
        with engine.connect() as conn:
            conn.execute(text("PRAGMA journal_mode=WAL"))
            conn.execute(text("PRAGMA synchronous=NORMAL"))
            conn.execute(text("PRAGMA foreign_keys=ON"))
            conn.execute(text("PRAGMA cache_size=10000"))
            conn.execute(text("PRAGMA temp_store=MEMORY"))
            conn.commit()

        # Create tables manually in the test database
        from app.models import Product, Tenant

        SQLModel.metadata.create_all(engine, checkfirst=True)

        # Create test data
        tenant_id = None
        product_id = None

        with Session(engine) as session:
            tenant = Tenant(
                name="Test Publisher Restart", slug="test-publisher-restart-standalone"
            )
            session.add(tenant)
            session.commit()
            session.refresh(tenant)
            tenant_id = tenant.id

            product = Product(
                product_id="test-product-restart-standalone",
                name="Test Product",
                description="A test product for persistence.",
                tenant_id=tenant_id,
                delivery_type="display",
                is_fixed_price=True,
                cpm=10.0,
                targeted_ages="18-34",
            )
            session.add(product)
            session.commit()
            session.refresh(product)
            product_id = product.id

        # Dispose the engine to simulate server restart
        engine.dispose()

        # Create new engine (simulating restart)
        new_engine = create_engine(db_url)

        # Create tables in the new engine (important for persistence tests)
        SQLModel.metadata.create_all(new_engine)

        # Verify data still exists
        with Session(new_engine) as session:
            tenant_repo = TenantRepository(session)
            persisted_tenant = tenant_repo.get_by_id(tenant_id)
            assert persisted_tenant is not None
            assert persisted_tenant.name == "Test Publisher Restart"
            assert persisted_tenant.slug == "test-publisher-restart-standalone"

            product_repo = ProductRepository(session)
            persisted_product = product_repo.get_by_product_id(
                "test-product-restart-standalone"
            )
            assert persisted_product is not None
            assert persisted_product.name == "Test Product"
            assert persisted_product.tenant_id == persisted_tenant.id

        # Clean up
        new_engine.dispose()

    finally:
        # Restore original DATABASE_URL
        if original_db_url:
            os.environ["DATABASE_URL"] = original_db_url
        else:
            os.environ.pop("DATABASE_URL", None)

        # Clean up temporary file
        try:
            os.unlink(db_path)
        except OSError:
            pass
