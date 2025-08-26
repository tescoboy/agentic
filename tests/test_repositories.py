"""Tests for repository layer."""

import pytest
from sqlmodel import Session, create_engine

from app.models.external_agent import ExternalAgent
from app.models.product import Product
from app.models.tenant import Tenant
from app.repositories.agent_settings import AgentSettingsRepository
from app.repositories.external_agents import ExternalAgentRepository
from app.repositories.products import ProductRepository
from app.repositories.tenants import TenantRepository


@pytest.fixture
def session():
    """Create a test database session."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    from sqlmodel import SQLModel

    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_tenants_repository_crud(session):
    """Test Tenants repo: create → get_by_slug → update → delete."""
    repo = TenantRepository(session)

    # Create
    tenant = Tenant(name="Test Publisher", slug="test-publisher")
    created = repo.create(tenant)
    assert created.id is not None
    assert created.name == "Test Publisher"
    assert created.slug == "test-publisher"

    # Get by slug
    found = repo.get_by_slug("test-publisher")
    assert found is not None
    assert found.id == created.id

    # Update
    found.name = "Updated Publisher"
    updated = repo.update(found)
    assert updated.name == "Updated Publisher"

    # Delete
    deleted = repo.delete(created.id)
    assert deleted is True

    # Verify deleted
    not_found = repo.get_by_slug("test-publisher")
    assert not_found is None


def test_products_repository_bulk_create(session):
    """Test Products repo: bulk_create with two rows for a tenant → list_by_tenant returns 2."""
    # Create tenant first
    tenant_repo = TenantRepository(session)
    tenant = tenant_repo.create(Tenant(name="Test Publisher", slug="test-publisher"))

    # Create products
    product_repo = ProductRepository(session)
    products = [
        Product(
            tenant_id=tenant.id,
            product_id="prod_1",
            name="Product 1",
            description="First product",
            delivery_type="guaranteed",
            is_fixed_price=True,
        ),
        Product(
            tenant_id=tenant.id,
            product_id="prod_2",
            name="Product 2",
            description="Second product",
            delivery_type="non_guaranteed",
            is_fixed_price=False,
        ),
    ]

    created = product_repo.bulk_create(products)
    assert len(created) == 2
    assert all(p.id is not None for p in created)

    # List by tenant
    tenant_products = product_repo.list_by_tenant(tenant.id)
    assert len(tenant_products) == 2
    assert {p.product_id for p in tenant_products} == {"prod_1", "prod_2"}


def test_agent_settings_repository_upsert(session):
    """Test AgentSettings repo: upsert_for_tenant then get_by_tenant returns override."""
    # Create tenant first
    tenant_repo = TenantRepository(session)
    tenant = tenant_repo.create(Tenant(name="Test Publisher", slug="test-publisher"))

    # Test upsert
    settings_repo = AgentSettingsRepository(session)
    settings = settings_repo.upsert_for_tenant(
        tenant.id,
        prompt_override="Custom prompt",
        model_name="claude-3-sonnet",
        timeout_ms=45000,
    )

    assert settings.tenant_id == tenant.id
    assert settings.prompt_override == "Custom prompt"
    assert settings.model_name == "claude-3-sonnet"
    assert settings.timeout_ms == 45000

    # Get by tenant
    found = settings_repo.get_by_tenant(tenant.id)
    assert found is not None
    assert found.prompt_override == "Custom prompt"

    # Test update via upsert
    updated = settings_repo.upsert_for_tenant(
        tenant.id, prompt_override="Updated prompt", timeout_ms=60000
    )
    assert updated.prompt_override == "Updated prompt"
    assert updated.timeout_ms == 60000
    assert updated.model_name == "claude-3-sonnet"  # Should be preserved


def test_external_agents_repository_enabled_filter(session):
    """Test ExternalAgents repo: create two where one enabled false → list_enabled returns only enabled."""
    repo = ExternalAgentRepository(session)

    # Create enabled agent
    enabled_agent = repo.create(
        ExternalAgent(
            name="Enabled Agent",
            base_url="https://enabled.example.com/mcp",
            enabled=True,
        )
    )

    # Create disabled agent
    disabled_agent = repo.create(
        ExternalAgent(
            name="Disabled Agent",
            base_url="https://disabled.example.com/mcp",
            enabled=False,
        )
    )

    # List all
    all_agents = repo.list_all()
    assert len(all_agents) == 2

    # List enabled only
    enabled_agents = repo.list_enabled()
    assert len(enabled_agents) == 1
    assert enabled_agents[0].id == enabled_agent.id
    assert enabled_agents[0].name == "Enabled Agent"
