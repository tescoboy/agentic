"""Tests for prompt selection logic."""

import pytest
from unittest.mock import patch, MagicMock

from app.services.sales_agent import evaluate_brief, load_default_prompt
from app.models.agent_settings import AgentSettings
from app.models.product import Product
from app.models.tenant import Tenant
from app.ai.errors import AIConfigError


@pytest.fixture
def mock_repos():
    """Mock repositories for testing."""
    agent_settings_repo = MagicMock()
    product_repo = MagicMock()
    tenant_repo = MagicMock()
    return agent_settings_repo, product_repo, tenant_repo


@pytest.fixture
def sample_products():
    """Sample products for testing."""
    return [
        Product(
            id=1,
            tenant_id=1,
            product_id="test_product_1",
            name="Test Product 1",
            description="A test product",
            delivery_type="guaranteed",
            is_fixed_price=True,
            cpm=10.0,
        ),
        Product(
            id=2,
            tenant_id=1,
            product_id="test_product_2",
            name="Test Product 2",
            description="Another test product",
            delivery_type="non_guaranteed",
            is_fixed_price=False,
        ),
    ]


def test_load_default_prompt_success():
    """Test loading default prompt from file."""
    with patch("builtins.open", create=True) as mock_open:
        mock_open.return_value.__enter__.return_value.read.return_value = (
            "Test prompt content"
        )

        prompt = load_default_prompt()
        assert prompt == "Test prompt content"


def test_load_default_prompt_file_not_found():
    """Test error when default prompt file is missing."""
    with patch("os.path.exists", return_value=False):
        with pytest.raises(AIConfigError) as exc_info:
            load_default_prompt()

        assert "Default prompt file not found" in str(exc_info.value)


def test_evaluate_brief_uses_custom_prompt(mock_repos, sample_products):
    """Test that custom prompt override is used when available."""
    agent_settings_repo, product_repo, tenant_repo = mock_repos

    # Mock agent settings with custom prompt
    custom_settings = AgentSettings(
        tenant_id=1,
        prompt_override="Custom prompt for testing",
        model_name="gemini-1.5-pro",
        timeout_ms=30000,
    )
    agent_settings_repo.get_by_tenant.return_value = custom_settings

    # Mock products
    product_repo.list_by_tenant.return_value = sample_products

    # Mock AI provider
    with patch("app.services.sales_agent.get_default_provider") as mock_provider:
        mock_provider_instance = MagicMock()
        mock_provider_instance.rank_products.return_value = [
            {"product_id": "test_product_1", "reason": "Matches brief", "score": 0.8}
        ]
        mock_provider.return_value = mock_provider_instance

        result = evaluate_brief(
            1, "Test brief", agent_settings_repo, product_repo, tenant_repo
        )

        # Verify custom prompt was used
        mock_provider_instance.rank_products.assert_called_once()
        call_args = mock_provider_instance.rank_products.call_args
        assert call_args[1]["prompt"] == "Custom prompt for testing"


def test_evaluate_brief_uses_default_prompt(mock_repos, sample_products):
    """Test that default prompt is used when no override is set."""
    agent_settings_repo, product_repo, tenant_repo = mock_repos

    # Mock agent settings without custom prompt
    default_settings = AgentSettings(
        tenant_id=1, prompt_override=None, model_name="gemini-1.5-pro", timeout_ms=30000
    )
    agent_settings_repo.get_by_tenant.return_value = default_settings

    # Mock products
    product_repo.list_by_tenant.return_value = sample_products

    # Mock default prompt loading
    with patch(
        "app.services.sales_agent.load_default_prompt",
        return_value="Default prompt content",
    ):
        # Mock AI provider
        with patch("app.services.sales_agent.get_default_provider") as mock_provider:
            mock_provider_instance = MagicMock()
            mock_provider_instance.rank_products.return_value = [
                {
                    "product_id": "test_product_1",
                    "reason": "Matches brief",
                    "score": 0.8,
                }
            ]
            mock_provider.return_value = mock_provider_instance

            result = evaluate_brief(
                1, "Test brief", agent_settings_repo, product_repo, tenant_repo
            )

            # Verify default prompt was used
            mock_provider_instance.rank_products.assert_called_once()
            call_args = mock_provider_instance.rank_products.call_args
            assert call_args[1]["prompt"] == "Default prompt content"


def test_evaluate_brief_no_products_error(mock_repos):
    """Test error when tenant has no products."""
    agent_settings_repo, product_repo, tenant_repo = mock_repos

    # Mock agent settings
    agent_settings_repo.get_by_tenant.return_value = AgentSettings(tenant_id=1)

    # Mock no products
    product_repo.list_by_tenant.return_value = []

    with pytest.raises(AIConfigError) as exc_info:
        evaluate_brief(1, "Test brief", agent_settings_repo, product_repo, tenant_repo)

    assert "No products found for tenant" in str(exc_info.value)


def test_evaluate_brief_creates_default_settings(mock_repos, sample_products):
    """Test that default settings are created when none exist."""
    agent_settings_repo, product_repo, tenant_repo = mock_repos

    # Mock no existing settings
    agent_settings_repo.get_by_tenant.return_value = None

    # Mock products
    product_repo.list_by_tenant.return_value = sample_products

    # Mock default prompt loading
    with patch(
        "app.services.sales_agent.load_default_prompt", return_value="Default prompt"
    ):
        # Mock AI provider
        with patch("app.services.sales_agent.get_default_provider") as mock_provider:
            mock_provider_instance = MagicMock()
            mock_provider_instance.rank_products.return_value = [
                {
                    "product_id": "test_product_1",
                    "reason": "Matches brief",
                    "score": 0.8,
                }
            ]
            mock_provider.return_value = mock_provider_instance

            result = evaluate_brief(
                1, "Test brief", agent_settings_repo, product_repo, tenant_repo
            )

            # Verify default settings were created
            agent_settings_repo.upsert_for_tenant.assert_called_once()
            created_settings = agent_settings_repo.upsert_for_tenant.call_args[0][0]
            assert created_settings.tenant_id == 1
            assert created_settings.model_name == "gemini-1.5-pro"
            assert created_settings.timeout_ms == 30000
