"""Tests for data models."""

from datetime import datetime

from app.models.agent_settings import AgentSettings
from app.models.external_agent import ExternalAgent
from app.models.product import Product
from app.models.tenant import Tenant


def test_tenant_creation():
    """Test that Tenant can be created with unique slug and timestamps set."""
    tenant = Tenant(name="Test Publisher", slug="test-publisher")

    assert tenant.name == "Test Publisher"
    assert tenant.slug == "test-publisher"
    assert tenant.id is None  # Not saved yet
    assert isinstance(tenant.created_at, datetime)
    assert isinstance(tenant.updated_at, datetime)


def test_agent_settings_creation():
    """Test that AgentSettings can be created linked to Tenant."""
    tenant = Tenant(name="Test Publisher", slug="test-publisher")
    settings = AgentSettings(
        tenant_id=1,  # Would be tenant.id after save
        prompt_override="Custom prompt for this tenant",
        model_name="claude-3-sonnet",
        timeout_ms=45000,
    )

    assert settings.tenant_id == 1
    assert settings.prompt_override == "Custom prompt for this tenant"
    assert settings.model_name == "claude-3-sonnet"
    assert settings.timeout_ms == 45000


def test_external_agent_creation():
    """Test that ExternalAgent can be created with enabled flag."""
    agent = ExternalAgent(
        name="Test MCP Agent",
        base_url="https://agent.example.com/mcp",
        enabled=True,
        capabilities='{"tools": ["search_products"]}',
    )

    assert agent.name == "Test MCP Agent"
    assert agent.base_url == "https://agent.example.com/mcp"
    assert agent.enabled is True
    assert agent.capabilities == '{"tools": ["search_products"]}'
    assert isinstance(agent.created_at, datetime)

    # Test capabilities methods
    caps = agent.get_capabilities()
    assert caps == {"tools": ["search_products"]}


def test_product_creation_adcp_fields():
    """Test that Product can be created with required AdCP Product fields."""
    product = Product(
        tenant_id=1,
        product_id="prod_123",
        name="Premium Video Ad",
        description="High-quality video advertising slot",
        delivery_type="guaranteed",
        is_fixed_price=True,
        cpm=25.50,
        is_custom=False,
        targeted_ages="adults",
        verified_minimum_age=18,
    )

    # Test core AdCP fields
    assert product.product_id == "prod_123"
    assert product.name == "Premium Video Ad"
    assert product.description == "High-quality video advertising slot"
    assert product.delivery_type == "guaranteed"
    assert product.is_fixed_price is True
    assert product.cpm == 25.50
    assert product.is_custom is False
    assert product.targeted_ages == "adults"
    assert product.verified_minimum_age == 18

    # Test JSON field methods
    assert product.get_formats() == []
    assert product.get_price_guidance() is None
    assert product.get_implementation_config() is None

    # Test setting JSON fields
    formats = [{"format_id": "video_30s", "name": "30 Second Video", "type": "video"}]
    product.set_formats(formats)
    assert product.get_formats() == formats
