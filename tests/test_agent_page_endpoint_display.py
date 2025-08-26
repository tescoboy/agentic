"""Tests for agent page endpoint URL display."""

import pytest
from unittest.mock import MagicMock
from unittest.mock import patch

from app.routes.agent_settings import show_agent_settings


class TestAgentPageEndpointDisplay:
    """Test agent page shows endpoint URL correctly."""

    @pytest.mark.asyncio
    async def test_agent_page_shows_endpoint_url(self):
        """Test GET /tenant/{id}/agent shows the exact endpoint URL."""
        # Mock repositories
        mock_agent_settings_repo = MagicMock()
        mock_tenant_repo = MagicMock()

        # Mock tenant
        mock_tenant = MagicMock(id=1, name="Publisher A", slug="publisher-a")
        mock_tenant_repo.get_by_id.return_value = mock_tenant
        mock_tenant_repo.get_by_slug.return_value = mock_tenant

        # Mock agent settings
        mock_agent_settings = MagicMock(
            model_name="gemini-1.5-pro", timeout_ms=30000, prompt_override=None
        )
        mock_agent_settings_repo.get_by_tenant.return_value = mock_agent_settings

        # Mock request
        mock_request = MagicMock()
        mock_request.cookies = {"active_tenant_id": "1"}
        mock_request.app.state.templates.TemplateResponse = MagicMock()

        # Mock default prompt
        with patch(
            "app.routes.agent_settings.load_default_prompt",
            return_value="Default prompt text",
        ):
            # Call function
            await show_agent_settings(
                request=mock_request,
                tenant_id=1,
                agent_settings_repo=mock_agent_settings_repo,
                tenant_repo=mock_tenant_repo,
            )

            # Verify template called with correct data
            mock_request.app.state.templates.TemplateResponse.assert_called_once()
            call_args = mock_request.app.state.templates.TemplateResponse.call_args
            assert call_args[0][0] == "agent/index.html"

            template_data = call_args[0][1]
            assert template_data["tenant"] == mock_tenant
            assert template_data["agent_settings"] == mock_agent_settings
            assert template_data["settings"] is not None
            assert template_data["settings"].service_base_url == "http://localhost:8000"

    @pytest.mark.asyncio
    async def test_agent_page_endpoint_url_format(self):
        """Test that the endpoint URL is correctly formatted."""
        # Mock repositories
        mock_agent_settings_repo = MagicMock()
        mock_tenant_repo = MagicMock()

        # Mock tenant with specific slug
        mock_tenant = MagicMock(id=1, name="Test Publisher", slug="test-publisher")
        mock_tenant_repo.get_by_id.return_value = mock_tenant
        mock_tenant_repo.get_by_slug.return_value = mock_tenant

        # Mock agent settings
        mock_agent_settings = MagicMock(
            model_name="gemini-1.5-pro", timeout_ms=30000, prompt_override=None
        )
        mock_agent_settings_repo.get_by_tenant.return_value = mock_agent_settings

        # Mock request
        mock_request = MagicMock()
        mock_request.cookies = {"active_tenant_id": "1"}
        mock_request.app.state.templates.TemplateResponse = MagicMock()

        # Mock default prompt
        with patch(
            "app.routes.agent_settings.load_default_prompt",
            return_value="Default prompt text",
        ):
            # Call function
            await show_agent_settings(
                request=mock_request,
                tenant_id=1,
                agent_settings_repo=mock_agent_settings_repo,
                tenant_repo=mock_tenant_repo,
            )

            # Verify template called with correct data
            mock_request.app.state.templates.TemplateResponse.assert_called_once()
            call_args = mock_request.app.state.templates.TemplateResponse.call_args
            template_data = call_args[0][1]

            # Verify the endpoint URL format
            expected_url = f"{template_data['settings'].service_base_url}/mcp/agents/{mock_tenant.slug}/rank"
            assert (
                expected_url == "http://localhost:8000/mcp/agents/test-publisher/rank"
            )

    @pytest.mark.asyncio
    async def test_agent_page_with_custom_service_base_url(self):
        """Test agent page with custom SERVICE_BASE_URL."""
        # Mock repositories
        mock_agent_settings_repo = MagicMock()
        mock_tenant_repo = MagicMock()

        # Mock tenant
        mock_tenant = MagicMock(id=1, name="Publisher A", slug="publisher-a")
        mock_tenant_repo.get_by_id.return_value = mock_tenant
        mock_tenant_repo.get_by_slug.return_value = mock_tenant

        # Mock agent settings
        mock_agent_settings = MagicMock(
            model_name="gemini-1.5-pro", timeout_ms=30000, prompt_override=None
        )
        mock_agent_settings_repo.get_by_tenant.return_value = mock_agent_settings

        # Mock request
        mock_request = MagicMock()
        mock_request.cookies = {"active_tenant_id": "1"}
        mock_request.app.state.templates.TemplateResponse = MagicMock()

        # Mock default prompt
        with patch(
            "app.routes.agent_settings.load_default_prompt",
            return_value="Default prompt text",
        ):
            # Mock custom service base URL
            with patch("app.routes.agent_settings.settings") as mock_settings:
                mock_settings.service_base_url = "https://custom-domain.com"

                # Call function
                await show_agent_settings(
                    request=mock_request,
                    tenant_id=1,
                    agent_settings_repo=mock_agent_settings_repo,
                    tenant_repo=mock_tenant_repo,
                )

                # Verify template called with correct data
                mock_request.app.state.templates.TemplateResponse.assert_called_once()
                call_args = mock_request.app.state.templates.TemplateResponse.call_args
                template_data = call_args[0][1]

                # Verify the endpoint URL uses custom base URL
                expected_url = f"{template_data['settings'].service_base_url}/mcp/agents/{mock_tenant.slug}/rank"
                assert (
                    expected_url
                    == "https://custom-domain.com/mcp/agents/publisher-a/rank"
                )

    @pytest.mark.asyncio
    async def test_agent_page_tenant_mismatch_handling(self):
        """Test agent page handles tenant mismatch correctly."""
        # Mock repositories
        mock_agent_settings_repo = MagicMock()
        mock_tenant_repo = MagicMock()

        # Mock tenant
        mock_tenant = MagicMock(id=1, name="Publisher A", slug="publisher-a")
        mock_tenant_repo.get_by_id.return_value = mock_tenant

        # Mock request with different active tenant
        mock_request = MagicMock()
        mock_request.cookies = {"active_tenant_id": "2"}  # Different tenant

        # This should raise an HTTPException for tenant mismatch
        with pytest.raises(Exception) as exc_info:
            await show_agent_settings(
                request=mock_request,
                tenant_id=1,
                agent_settings_repo=mock_agent_settings_repo,
                tenant_repo=mock_tenant_repo,
            )

        # Verify exception is raised (tenant mismatch)
        assert "Tenant mismatch" in str(exc_info.value) or "400" in str(exc_info.value)
