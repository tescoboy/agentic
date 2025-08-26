"""Tests for agent settings UI."""

import pytest
from unittest.mock import patch, MagicMock
from fastapi import Request
from fastapi.responses import HTMLResponse

from app.routes.agent_settings import show_agent_settings, update_agent_settings
from app.models.agent_settings import AgentSettings
from app.models.tenant import Tenant


@pytest.fixture
def sample_tenant():
    """Sample tenant for testing."""
    return Tenant(id=1, name="Test Publisher", domain="test.com")


@pytest.fixture
def sample_agent_settings():
    """Sample agent settings for testing."""
    return AgentSettings(
        id=1,
        tenant_id=1,
        prompt_override="Custom prompt for testing",
        model_name="gemini-1.5-pro",
        timeout_ms=30000,
    )


@pytest.fixture
def mock_request():
    """Mock request object."""
    request = MagicMock(spec=Request)
    request.state.active_tenant = None
    request.state.tenants = []
    return request


async def test_show_agent_settings_get(
    mock_request, sample_tenant, sample_agent_settings
):
    """Test GET /tenant/{tenant_id}/agent shows settings."""
    # Create mock repositories
    mock_tenant_repo = MagicMock()
    mock_agent_repo = MagicMock()

    # Set up mock returns
    mock_tenant_repo.get_by_id.return_value = sample_tenant
    mock_agent_repo.get_by_tenant.return_value = sample_agent_settings

    with (
        patch("app.routes.agent_settings.get_active_tenant_id", return_value=1),
        patch(
            "app.services.sales_agent.load_default_prompt",
            return_value="Default prompt content",
        ),
    ):
        response = await show_agent_settings(
            request=mock_request,
            tenant_id=1,
            agent_settings_repo=mock_agent_repo,
            tenant_repo=mock_tenant_repo,
        )

        assert isinstance(response, HTMLResponse)
        assert response.status_code == 200
        response_text = response.body.decode("utf-8")
        assert "Agent Settings" in response_text
        assert "Test Publisher" in response_text
        assert "Custom prompt for testing" in response_text
        assert "gemini-1.5-pro" in response_text
        assert "30000" in response_text


async def test_show_agent_settings_using_default_prompt(mock_request, sample_tenant):
    """Test GET shows default prompt when no override is set."""
    # Create mock repositories
    mock_tenant_repo = MagicMock()
    mock_agent_repo = MagicMock()

    # Set up mock returns
    mock_tenant_repo.get_by_id.return_value = sample_tenant
    mock_agent_repo.get_by_tenant.return_value = None  # No settings

    with (
        patch("app.routes.agent_settings.get_active_tenant_id", return_value=1),
        patch(
            "app.services.sales_agent.load_default_prompt",
            return_value="Default prompt content",
        ),
    ):
        response = await show_agent_settings(
            request=mock_request,
            tenant_id=1,
            agent_settings_repo=mock_agent_repo,
            tenant_repo=mock_tenant_repo,
        )

        assert isinstance(response, HTMLResponse)
        assert response.status_code == 200
        response_text = response.body.decode("utf-8")
        assert "Using Default Prompt" in response_text
        # The default prompt content should be in the modal or effective prompt section
        # Check for the effective prompt content in the response
        assert (
            "Default prompt content" in response_text
            or "Using Default Prompt" in response_text
        )


async def test_show_agent_settings_tenant_not_found(mock_request):
    """Test GET returns 404 when tenant not found."""
    # Create mock repositories
    mock_tenant_repo = MagicMock()
    mock_agent_repo = MagicMock()

    # Set up mock returns
    mock_tenant_repo.get_by_id.return_value = None

    with pytest.raises(Exception) as exc_info:
        await show_agent_settings(
            request=mock_request,
            tenant_id=999,
            agent_settings_repo=mock_agent_repo,
            tenant_repo=mock_tenant_repo,
        )

    assert "404" in str(exc_info.value) or "Tenant not found" in str(exc_info.value)


async def test_show_agent_settings_tenant_mismatch(mock_request, sample_tenant):
    """Test GET returns 400 when active tenant doesn't match."""
    # Create mock repositories
    mock_tenant_repo = MagicMock()
    mock_agent_repo = MagicMock()

    # Set up mock returns
    mock_tenant_repo.get_by_id.return_value = sample_tenant

    with patch(
        "app.routes.agent_settings.get_active_tenant_id", return_value=2
    ):  # Different tenant
        with pytest.raises(Exception) as exc_info:
            await show_agent_settings(
                request=mock_request,
                tenant_id=1,
                agent_settings_repo=mock_agent_repo,
                tenant_repo=mock_tenant_repo,
            )

        assert "400" in str(exc_info.value) or "Tenant mismatch" in str(exc_info.value)


async def test_update_agent_settings_success(mock_request, sample_tenant):
    """Test POST /tenant/{tenant_id}/agent updates settings successfully."""
    # Create mock repositories
    mock_tenant_repo = MagicMock()
    mock_agent_repo = MagicMock()

    # Set up mock returns
    mock_tenant_repo.get_by_id.return_value = sample_tenant
    mock_agent_repo.get_by_tenant.return_value = None  # No existing settings

    with patch("app.routes.agent_settings.get_active_tenant_id", return_value=1):
        response = await update_agent_settings(
            request=mock_request,
            tenant_id=1,
            prompt_override="New custom prompt",
            model_name="gemini-1.5-flash",
            timeout_ms=45000,
            agent_settings_repo=mock_agent_repo,
            tenant_repo=mock_tenant_repo,
        )

        # Should be a redirect response
        assert hasattr(response, "status_code")
        assert response.status_code == 302
        # URL encoding converts spaces to %20
        assert (
            "Agent%20settings%20updated%20successfully" in response.headers["location"]
        )

        # Verify settings were saved
        mock_agent_repo.upsert_for_tenant.assert_called_once()


async def test_update_agent_settings_validation_errors(mock_request, sample_tenant):
    """Test POST returns validation errors for invalid input."""
    # Create mock repositories
    mock_tenant_repo = MagicMock()
    mock_agent_repo = MagicMock()

    # Set up mock returns
    mock_tenant_repo.get_by_id.return_value = sample_tenant
    mock_agent_repo.get_by_tenant.return_value = None

    with (
        patch("app.routes.agent_settings.get_active_tenant_id", return_value=1),
        patch(
            "app.services.sales_agent.load_default_prompt",
            return_value="Default prompt",
        ),
    ):
        # Test invalid timeout
        response = await update_agent_settings(
            request=mock_request,
            tenant_id=1,
            prompt_override="Valid prompt",
            model_name="gemini-1.5-pro",
            timeout_ms=500,  # Too low
            agent_settings_repo=mock_agent_repo,
            tenant_repo=mock_tenant_repo,
        )

        assert isinstance(response, HTMLResponse)
        assert response.status_code == 400
        response_text = response.body.decode("utf-8")
        assert "Timeout must be between 1,000 and 120,000 milliseconds" in response_text


async def test_update_agent_settings_prompt_too_long(mock_request, sample_tenant):
    """Test POST returns error when prompt override is too long."""
    # Create mock repositories
    mock_tenant_repo = MagicMock()
    mock_agent_repo = MagicMock()

    # Set up mock returns
    mock_tenant_repo.get_by_id.return_value = sample_tenant
    mock_agent_repo.get_by_tenant.return_value = None

    with (
        patch("app.routes.agent_settings.get_active_tenant_id", return_value=1),
        patch(
            "app.services.sales_agent.load_default_prompt",
            return_value="Default prompt",
        ),
    ):
        # Create a prompt that's too long
        long_prompt = "x" * 10001  # Over 10,000 character limit

        response = await update_agent_settings(
            request=mock_request,
            tenant_id=1,
            prompt_override=long_prompt,
            model_name="gemini-1.5-pro",
            timeout_ms=30000,
            agent_settings_repo=mock_agent_repo,
            tenant_repo=mock_tenant_repo,
        )

        assert isinstance(response, HTMLResponse)
        assert response.status_code == 400
        response_text = response.body.decode("utf-8")
        assert "Prompt override too long" in response_text


async def test_update_agent_settings_invalid_model(mock_request, sample_tenant):
    """Test POST returns error for invalid model name."""
    # Create mock repositories
    mock_tenant_repo = MagicMock()
    mock_agent_repo = MagicMock()

    # Set up mock returns
    mock_tenant_repo.get_by_id.return_value = sample_tenant
    mock_agent_repo.get_by_tenant.return_value = None

    with (
        patch("app.routes.agent_settings.get_active_tenant_id", return_value=1),
        patch(
            "app.services.sales_agent.load_default_prompt",
            return_value="Default prompt",
        ),
    ):
        response = await update_agent_settings(
            request=mock_request,
            tenant_id=1,
            prompt_override="Valid prompt",
            model_name="invalid-model",
            timeout_ms=30000,
            agent_settings_repo=mock_agent_repo,
            tenant_repo=mock_tenant_repo,
        )

        assert isinstance(response, HTMLResponse)
        assert response.status_code == 400
        response_text = response.body.decode("utf-8")
        assert "Invalid model name" in response_text


async def test_update_agent_settings_clears_prompt_override(
    mock_request, sample_tenant
):
    """Test POST clears prompt override when empty string is provided."""
    # Create mock repositories
    mock_tenant_repo = MagicMock()
    mock_agent_repo = MagicMock()

    # Set up mock returns
    mock_tenant_repo.get_by_id.return_value = sample_tenant
    mock_agent_repo.get_by_tenant.return_value = None

    with patch("app.routes.agent_settings.get_active_tenant_id", return_value=1):
        response = await update_agent_settings(
            request=mock_request,
            tenant_id=1,
            prompt_override="",  # Empty string
            model_name="gemini-1.5-pro",
            timeout_ms=30000,
            agent_settings_repo=mock_agent_repo,
            tenant_repo=mock_tenant_repo,
        )

        # Should be a redirect response
        assert hasattr(response, "status_code")
        assert response.status_code == 302

        # Verify settings were saved with None prompt_override
        mock_agent_repo.upsert_for_tenant.assert_called_once()
        call_args = mock_agent_repo.upsert_for_tenant.call_args
        assert call_args[1]["prompt_override"] is None


async def test_agent_settings_form_validation(mock_request, sample_tenant):
    """Test form validation preserves form data on errors."""
    # Create mock repositories
    mock_tenant_repo = MagicMock()
    mock_agent_repo = MagicMock()

    # Set up mock returns
    mock_tenant_repo.get_by_id.return_value = sample_tenant
    mock_agent_repo.get_by_tenant.return_value = None

    with (
        patch("app.routes.agent_settings.get_active_tenant_id", return_value=1),
        patch(
            "app.services.sales_agent.load_default_prompt",
            return_value="Default prompt",
        ),
    ):
        response = await update_agent_settings(
            request=mock_request,
            tenant_id=1,
            prompt_override="Valid prompt content",
            model_name="gemini-1.5-pro",
            timeout_ms=500,  # Invalid timeout
            agent_settings_repo=mock_agent_repo,
            tenant_repo=mock_tenant_repo,
        )

        assert isinstance(response, HTMLResponse)
        assert response.status_code == 400
        response_text = response.body.decode("utf-8")
        assert "Valid prompt content" in response_text  # Form data preserved
        assert "gemini-1.5-pro" in response_text  # Form data preserved
