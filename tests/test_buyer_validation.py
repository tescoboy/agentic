"""Tests for buyer form validation."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from app.routes.buyer import submit_buyer_brief


class TestBuyerValidation:
    """Test buyer form validation."""

    @pytest.mark.asyncio
    async def test_submit_buyer_brief_empty_brief(self):
        """Test POST /buyer with empty brief returns validation error."""
        # Mock repositories
        mock_tenant_repo = MagicMock()
        mock_external_agent_repo = MagicMock()
        mock_tenants = [MagicMock(id=1, name="Publisher A", slug="publisher-a")]
        mock_tenant_repo.list_all.return_value = mock_tenants
        mock_external_agent_repo.list_enabled.return_value = []

        # Mock request
        mock_request = MagicMock()
        mock_request.app.state.templates.TemplateResponse = MagicMock()

        # Call function with empty brief
        await submit_buyer_brief(
            request=mock_request,
            brief="",
            internal_tenants=["publisher-a"],
            external_agents=[],
            timeout_ms=None,
            tenant_repo=mock_tenant_repo,
            external_agent_repo=mock_external_agent_repo,
        )

        # Verify template called with validation error
        mock_request.app.state.templates.TemplateResponse.assert_called_once()
        call_args = mock_request.app.state.templates.TemplateResponse.call_args
        template_data = call_args[0][1]
        assert template_data["error"] == "Brief is required"
        assert template_data["results"] is None

    @pytest.mark.asyncio
    async def test_submit_buyer_brief_whitespace_brief(self):
        """Test POST /buyer with whitespace-only brief returns validation error."""
        # Mock repositories
        mock_tenant_repo = MagicMock()
        mock_external_agent_repo = MagicMock()
        mock_tenants = [MagicMock(id=1, name="Publisher A", slug="publisher-a")]
        mock_tenant_repo.list_all.return_value = mock_tenants
        mock_external_agent_repo.list_enabled.return_value = []

        # Mock request
        mock_request = MagicMock()
        mock_request.app.state.templates.TemplateResponse = MagicMock()

        # Call function with whitespace-only brief
        await submit_buyer_brief(
            request=mock_request,
            brief="   \n\t   ",
            internal_tenants=["publisher-a"],
            external_agents=[],
            timeout_ms=None,
            tenant_repo=mock_tenant_repo,
            external_agent_repo=mock_external_agent_repo,
        )

        # Verify template called with validation error
        mock_request.app.state.templates.TemplateResponse.assert_called_once()
        call_args = mock_request.app.state.templates.TemplateResponse.call_args
        template_data = call_args[0][1]
        assert template_data["error"] == "Brief is required"
        assert template_data["results"] is None

    @pytest.mark.asyncio
    async def test_submit_buyer_brief_no_agents_selected(self):
        """Test POST /buyer with no agents selected returns validation error."""
        # Mock repositories
        mock_tenant_repo = MagicMock()
        mock_external_agent_repo = MagicMock()
        mock_tenants = [MagicMock(id=1, name="Publisher A", slug="publisher-a")]
        mock_tenant_repo.list_all.return_value = mock_tenants
        mock_external_agent_repo.list_enabled.return_value = []

        # Mock request
        mock_request = MagicMock()
        mock_request.app.state.templates.TemplateResponse = MagicMock()

        # Call function with no agents selected
        await submit_buyer_brief(
            request=mock_request,
            brief="Valid brief text",
            internal_tenants=[],
            external_agents=[],
            timeout_ms=None,
            tenant_repo=mock_tenant_repo,
            external_agent_repo=mock_external_agent_repo,
        )

        # Verify template called with validation error
        mock_request.app.state.templates.TemplateResponse.assert_called_once()
        call_args = mock_request.app.state.templates.TemplateResponse.call_args
        template_data = call_args[0][1]
        assert template_data["error"] == "Please select at least one agent"
        assert template_data["results"] is None

    @pytest.mark.asyncio
    async def test_submit_buyer_brief_empty_lists(self):
        """Test POST /buyer with empty lists for agents returns validation error."""
        # Mock repositories
        mock_tenant_repo = MagicMock()
        mock_external_agent_repo = MagicMock()
        mock_tenants = [MagicMock(id=1, name="Publisher A", slug="publisher-a")]
        mock_tenant_repo.list_all.return_value = mock_tenants
        mock_external_agent_repo.list_enabled.return_value = []

        # Mock request
        mock_request = MagicMock()
        mock_request.app.state.templates.TemplateResponse = MagicMock()

        # Call function with empty lists
        await submit_buyer_brief(
            request=mock_request,
            brief="Valid brief text",
            internal_tenants=[],
            external_agents=[],
            timeout_ms=None,
            tenant_repo=mock_tenant_repo,
            external_agent_repo=mock_external_agent_repo,
        )

        # Verify template called with validation error
        mock_request.app.state.templates.TemplateResponse.assert_called_once()
        call_args = mock_request.app.state.templates.TemplateResponse.call_args
        template_data = call_args[0][1]
        assert template_data["error"] == "Please select at least one agent"
        assert template_data["results"] is None

    @pytest.mark.asyncio
    async def test_submit_buyer_brief_valid_with_internal_only(self):
        """Test POST /buyer with valid brief and internal agents only."""
        # Mock repositories
        mock_tenant_repo = MagicMock()
        mock_external_agent_repo = MagicMock()
        mock_tenants = [MagicMock(id=1, name="Publisher A", slug="publisher-a")]
        mock_tenant_repo.list_all.return_value = mock_tenants
        mock_external_agent_repo.list_enabled.return_value = []

        # Mock request
        mock_request = MagicMock()
        mock_request.app.state.templates.TemplateResponse = MagicMock()

        # Mock orchestrator response
        mock_orchestrator_response = {
            "results": [
                {
                    "agent": {"type": "internal", "slug": "publisher-a"},
                    "items": [{"product_id": "prod_1", "reason": "Test", "score": 0.9}],
                    "error": None,
                }
            ],
            "context_id": "ctx-valid",
            "total_agents": 1,
            "timeout_ms": 8000,
        }

        # Mock HTTP client
        mock_http_response = MagicMock()
        mock_http_response.status_code = 200
        mock_http_response.json.return_value = mock_orchestrator_response

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__ = AsyncMock(
                return_value=mock_client
            )
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_client.post.return_value = mock_http_response

            # Call function with valid data
            await submit_buyer_brief(
                request=mock_request,
                brief="Valid brief text",
                internal_tenants=["publisher-a"],
                external_agents=[],
                timeout_ms=None,
                tenant_repo=mock_tenant_repo,
                external_agent_repo=mock_external_agent_repo,
            )

        # Verify template called with results (no validation error)
        mock_request.app.state.templates.TemplateResponse.assert_called_once()
        call_args = mock_request.app.state.templates.TemplateResponse.call_args
        template_data = call_args[0][1]
        assert template_data["error"] is None
        assert template_data["results"] == mock_orchestrator_response

    @pytest.mark.asyncio
    async def test_submit_buyer_brief_valid_with_external_only(self):
        """Test POST /buyer with valid brief and external agents only."""
        # Mock repositories
        mock_tenant_repo = MagicMock()
        mock_external_agent_repo = MagicMock()
        mock_tenants = []
        mock_tenant_repo.list_all.return_value = mock_tenants
        mock_external_agents = [
            MagicMock(
                id=1,
                name="External Agent",
                base_url="https://agent.com/adcp",
                enabled=True,
            )
        ]
        mock_external_agent_repo.list_enabled.return_value = mock_external_agents

        # Mock request
        mock_request = MagicMock()
        mock_request.app.state.templates.TemplateResponse = MagicMock()

        # Mock orchestrator response
        mock_orchestrator_response = {
            "results": [
                {
                    "agent": {"type": "external", "url": "https://agent.com/adcp"},
                    "items": [
                        {"product_id": "ext_prod_1", "reason": "Test", "score": 0.9}
                    ],
                    "error": None,
                }
            ],
            "context_id": "ctx-valid",
            "total_agents": 1,
            "timeout_ms": 8000,
        }

        # Mock HTTP client
        mock_http_response = MagicMock()
        mock_http_response.status_code = 200
        mock_http_response.json.return_value = mock_orchestrator_response

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__ = AsyncMock(
                return_value=mock_client
            )
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_client.post.return_value = mock_http_response

            # Call function with valid data
            await submit_buyer_brief(
                request=mock_request,
                brief="Valid brief text",
                internal_tenants=[],
                external_agents=["https://agent.com/adcp"],
                timeout_ms=None,
                tenant_repo=mock_tenant_repo,
                external_agent_repo=mock_external_agent_repo,
            )

        # Verify template called with results (no validation error)
        mock_request.app.state.templates.TemplateResponse.assert_called_once()
        call_args = mock_request.app.state.templates.TemplateResponse.call_args
        template_data = call_args[0][1]
        assert template_data["error"] is None
        assert template_data["results"] == mock_orchestrator_response

    @pytest.mark.asyncio
    async def test_submit_buyer_brief_timeout_validation(self):
        """Test POST /buyer with invalid timeout values."""
        # Mock repositories
        mock_tenant_repo = MagicMock()
        mock_external_agent_repo = MagicMock()
        mock_tenants = [MagicMock(id=1, name="Publisher A", slug="publisher-a")]
        mock_tenant_repo.list_all.return_value = mock_tenants
        mock_external_agent_repo.list_enabled.return_value = []

        # Mock request
        mock_request = MagicMock()
        mock_request.app.state.templates.TemplateResponse = MagicMock()

        # Mock orchestrator response
        mock_orchestrator_response = {
            "results": [
                {
                    "agent": {"type": "internal", "slug": "publisher-a"},
                    "items": [{"product_id": "prod_1", "reason": "Test", "score": 0.9}],
                    "error": None,
                }
            ],
            "context_id": "ctx-valid",
            "total_agents": 1,
            "timeout_ms": 8000,
        }

        # Mock HTTP client
        mock_http_response = MagicMock()
        mock_http_response.status_code = 200
        mock_http_response.json.return_value = mock_orchestrator_response

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__ = AsyncMock(
                return_value=mock_client
            )
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_client.post.return_value = mock_http_response

            # Call function with negative timeout (should be ignored)
            await submit_buyer_brief(
                request=mock_request,
                brief="Valid brief text",
                internal_tenants=["publisher-a"],
                external_agents=[],
                timeout_ms=-1000,
                tenant_repo=mock_tenant_repo,
                external_agent_repo=mock_external_agent_repo,
            )

        # Verify template called with results (timeout should be ignored)
        mock_request.app.state.templates.TemplateResponse.assert_called_once()
        call_args = mock_request.app.state.templates.TemplateResponse.call_args
        template_data = call_args[0][1]
        assert template_data["error"] is None
        assert template_data["results"] == mock_orchestrator_response
