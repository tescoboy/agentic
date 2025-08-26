"""Tests for rank products contract validation."""

import pytest
from unittest.mock import patch, MagicMock

from app.services.sales_agent import evaluate_brief, product_to_dict
from app.models.product import Product
from app.models.agent_settings import AgentSettings


@pytest.fixture
def sample_products():
    """Sample products for testing."""
    return [
        Product(
            id=1,
            tenant_id=1,
            product_id="product_001",
            name="Premium Video Ad",
            description="High-quality video advertising for premium content",
            delivery_type="guaranteed",
            is_fixed_price=True,
            cpm=25.0,
            is_custom=False,
            policy_compliance="Family-friendly content",
            targeted_ages="adults",
            verified_minimum_age=18,
        ),
        Product(
            id=2,
            tenant_id=1,
            product_id="product_002",
            name="Standard Display Ad",
            description="Standard banner advertising for general content",
            delivery_type="non_guaranteed",
            is_fixed_price=False,
            cpm=None,
            is_custom=False,
            policy_compliance="General content",
            targeted_ages="adults",
            verified_minimum_age=13,
        ),
    ]


def test_product_to_dict_conversion(sample_products):
    """Test product_to_dict converts Product models correctly."""
    product = sample_products[0]
    product_dict = product_to_dict(product)

    # Check required fields are present
    assert product_dict["id"] == 1
    assert product_dict["product_id"] == "product_001"
    assert product_dict["name"] == "Premium Video Ad"
    assert (
        product_dict["description"]
        == "High-quality video advertising for premium content"
    )
    assert product_dict["delivery_type"] == "guaranteed"
    assert product_dict["is_fixed_price"] is True
    assert product_dict["cpm"] == 25.0
    assert product_dict["is_custom"] is False
    assert product_dict["policy_compliance"] == "Family-friendly content"
    assert product_dict["targeted_ages"] == "adults"
    assert product_dict["verified_minimum_age"] == 18
    assert product_dict["expires_at"] is None


def test_product_to_dict_with_expires_at():
    """Test product_to_dict handles expires_at field correctly."""
    from datetime import datetime

    product = Product(
        id=1,
        tenant_id=1,
        product_id="test_product",
        name="Test Product",
        description="Test description",
        delivery_type="guaranteed",
        is_fixed_price=True,
        expires_at=datetime(2024, 12, 31, 23, 59, 59),
    )

    product_dict = product_to_dict(product)
    assert product_dict["expires_at"] == "2024-12-31T23:59:59"


def test_rank_products_response_structure(sample_products):
    """Test that rank_products returns correct response structure."""
    # Mock repositories
    agent_settings_repo = MagicMock()
    product_repo = MagicMock()
    tenant_repo = MagicMock()

    # Mock agent settings
    agent_settings_repo.get_by_tenant.return_value = AgentSettings(
        tenant_id=1, model_name="gemini-1.5-pro", timeout_ms=30000
    )

    # Mock products
    product_repo.list_by_tenant.return_value = sample_products

    # Mock AI provider response
    mock_response = [
        {
            "product_id": "product_001",
            "reason": "This premium video ad matches the brief for high-quality content",
            "score": 0.85,
        },
        {
            "product_id": "product_002",
            "reason": "Standard display ad provides good reach but lower quality",
            "score": 0.65,
        },
    ]

    with patch(
        "app.services.sales_agent.load_default_prompt", return_value="Test prompt"
    ):
        with patch("app.services.sales_agent.get_default_provider") as mock_provider:
            mock_provider_instance = MagicMock()
            mock_provider_instance.rank_products.return_value = mock_response
            mock_provider.return_value = mock_provider_instance

            result = evaluate_brief(
                1,
                "Video ads for premium content",
                agent_settings_repo,
                product_repo,
                tenant_repo,
            )

            # Verify response structure
            assert len(result) == 2
            assert isinstance(result, list)

            # Check first product
            assert result[0]["product_id"] == "product_001"
            assert (
                result[0]["reason"]
                == "This premium video ad matches the brief for high-quality content"
            )
            assert result[0]["score"] == 0.85

            # Check second product
            assert result[1]["product_id"] == "product_002"
            assert (
                result[1]["reason"]
                == "Standard display ad provides good reach but lower quality"
            )
            assert result[1]["score"] == 0.65


def test_rank_products_preserves_provider_order(sample_products):
    """Test that rank_products preserves the order returned by the provider."""
    # Mock repositories
    agent_settings_repo = MagicMock()
    product_repo = MagicMock()
    tenant_repo = MagicMock()

    # Mock agent settings
    agent_settings_repo.get_by_tenant.return_value = AgentSettings(tenant_id=1)

    # Mock products
    product_repo.list_by_tenant.return_value = sample_products

    # Mock AI provider response in specific order
    mock_response = [
        {
            "product_id": "product_002",  # Second product first
            "reason": "Standard display ad is most relevant",
            "score": 0.9,
        },
        {
            "product_id": "product_001",  # First product second
            "reason": "Premium video ad is less relevant",
            "score": 0.7,
        },
    ]

    with patch(
        "app.services.sales_agent.load_default_prompt", return_value="Test prompt"
    ):
        with patch("app.services.sales_agent.get_default_provider") as mock_provider:
            mock_provider_instance = MagicMock()
            mock_provider_instance.rank_products.return_value = mock_response
            mock_provider.return_value = mock_provider_instance

            result = evaluate_brief(
                1,
                "Standard display ads",
                agent_settings_repo,
                product_repo,
                tenant_repo,
            )

            # Verify order is preserved
            assert result[0]["product_id"] == "product_002"
            assert result[1]["product_id"] == "product_001"


def test_rank_products_no_extra_fields(sample_products):
    """Test that rank_products response contains only expected fields."""
    # Mock repositories
    agent_settings_repo = MagicMock()
    product_repo = MagicMock()
    tenant_repo = MagicMock()

    # Mock agent settings
    agent_settings_repo.get_by_tenant.return_value = AgentSettings(tenant_id=1)

    # Mock products
    product_repo.list_by_tenant.return_value = sample_products

    # Mock AI provider response
    mock_response = [
        {"product_id": "product_001", "reason": "Matches the brief", "score": 0.8}
    ]

    with patch(
        "app.services.sales_agent.load_default_prompt", return_value="Test prompt"
    ):
        with patch("app.services.sales_agent.get_default_provider") as mock_provider:
            mock_provider_instance = MagicMock()
            mock_provider_instance.rank_products.return_value = mock_response
            mock_provider.return_value = mock_provider_instance

            result = evaluate_brief(
                1, "Test brief", agent_settings_repo, product_repo, tenant_repo
            )

            # Verify only expected fields
            assert len(result) == 1
            product_result = result[0]
            expected_fields = {"product_id", "reason", "score"}
            actual_fields = set(product_result.keys())

            assert actual_fields == expected_fields, (
                f"Unexpected fields: {actual_fields - expected_fields}"
            )


def test_rank_products_optional_score_field(sample_products):
    """Test that score field is optional in response."""
    # Mock repositories
    agent_settings_repo = MagicMock()
    product_repo = MagicMock()
    tenant_repo = MagicMock()

    # Mock agent settings
    agent_settings_repo.get_by_tenant.return_value = AgentSettings(tenant_id=1)

    # Mock products
    product_repo.list_by_tenant.return_value = sample_products

    # Mock AI provider response with optional score
    mock_response = [
        {
            "product_id": "product_001",
            "reason": "Matches the brief",
            # No score field
        },
        {"product_id": "product_002", "reason": "Partial match", "score": 0.6},
    ]

    with patch(
        "app.services.sales_agent.load_default_prompt", return_value="Test prompt"
    ):
        with patch("app.services.sales_agent.get_default_provider") as mock_provider:
            mock_provider_instance = MagicMock()
            mock_provider_instance.rank_products.return_value = mock_response
            mock_provider.return_value = mock_provider_instance

            result = evaluate_brief(
                1, "Test brief", agent_settings_repo, product_repo, tenant_repo
            )

            # Verify first product has no score
            assert "score" not in result[0]
            assert result[0]["product_id"] == "product_001"
            assert result[0]["reason"] == "Matches the brief"

            # Verify second product has score
            assert result[1]["score"] == 0.6
            assert result[1]["product_id"] == "product_002"
            assert result[1]["reason"] == "Partial match"
