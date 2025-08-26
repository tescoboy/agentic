"""Tests for buyer flow with successful orchestration results."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from app.routes.buyer import show_buyer_page, submit_buyer_brief


class TestBuyerFlow:
    """Test successful buyer flow with multiple agents."""

    @pytest.mark.asyncio
    async def test_show_buyer_page_success(self):
        """Test GET /buyer shows form with agents."""
        # Mock repositories
        mock_tenant_repo = MagicMock()
        mock_external_agent_repo = MagicMock()

        # Mock tenant data
        mock_tenants = [
            MagicMock(id=1, name="Publisher A", slug="publisher-a"),
            MagicMock(id=2, name="Publisher B", slug="publisher-b"),
        ]
        mock_tenant_repo.list_all.return_value = mock_tenants

        # Mock external agent data
        mock_external_agents = [
            MagicMock(
                id=1,
                name="External Agent 1",
                base_url="https://agent1.com/adcp",
                enabled=True,
            ),
            MagicMock(
                id=2,
                name="External Agent 2",
                base_url="https://agent2.com/adcp",
                enabled=True,
            ),
        ]
        mock_external_agent_repo.list_enabled.return_value = mock_external_agents

        # Mock request
        mock_request = MagicMock()
        mock_request.app.state.templates.TemplateResponse = MagicMock()

        # Call function
        await show_buyer_page(
            request=mock_request,
            tenant_repo=mock_tenant_repo,
            external_agent_repo=mock_external_agent_repo,
        )

        # Verify template called with correct data
        mock_request.app.state.templates.TemplateResponse.assert_called_once()
        call_args = mock_request.app.state.templates.TemplateResponse.call_args
        assert call_args[0][0] == "buyer/index.html"
        template_data = call_args[0][1]
        assert template_data["tenants"] == mock_tenants
        assert template_data["external_agents"] == mock_external_agents
        assert template_data["results"] is None
        assert template_data["error"] is None

    @pytest.mark.asyncio
    async def test_submit_buyer_brief_success(self):
        """Test POST /buyer with valid brief and agent selection."""
        # Mock repositories
        mock_tenant_repo = MagicMock()
        mock_external_agent_repo = MagicMock()

        # Mock tenant data
        mock_tenants = [
            MagicMock(id=1, name="Publisher A", slug="publisher-a"),
            MagicMock(id=2, name="Publisher B", slug="publisher-b"),
        ]
        mock_tenant_repo.list_all.return_value = mock_tenants

        # Mock external agent data
        mock_external_agents = [
            MagicMock(
                id=1,
                name="External Agent 1",
                base_url="https://agent1.com/adcp",
                enabled=True,
            ),
            MagicMock(
                id=2,
                name="External Agent 2",
                base_url="https://agent2.com/adcp",
                enabled=True,
            ),
        ]
        mock_external_agent_repo.list_enabled.return_value = mock_external_agents

        # Mock request
        mock_request = MagicMock()
        mock_request.app.state.templates.TemplateResponse = MagicMock()

        # Mock orchestrator response
        mock_orchestrator_response = {
            "results": [
                {
                    "agent": {"type": "internal", "slug": "publisher-a"},
                    "items": [
                        {
                            "product_id": "prod_1",
                            "reason": "Perfect match for sports advertising",
                            "score": 0.95,
                        },
                        {
                            "product_id": "prod_2",
                            "reason": "Good demographic fit",
                            "score": 0.85,
                        },
                    ],
                    "error": None,
                },
                {
                    "agent": {"type": "external", "url": "https://agent1.com/adcp"},
                    "items": [
                        {
                            "product_id": "ext_prod_1",
                            "reason": "Premium video inventory",
                            "score": 0.88,
                        }
                    ],
                    "error": None,
                },
            ],
            "context_id": "ctx-123",
            "total_agents": 2,
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

            # Call function
            await submit_buyer_brief(
                request=mock_request,
                brief="Sports advertising campaign for young adults",
                internal_tenants=["publisher-a"],
                external_agents=["https://agent1.com/adcp"],
                timeout_ms=None,
                tenant_repo=mock_tenant_repo,
                external_agent_repo=mock_external_agent_repo,
            )

        # Verify template called with results
        mock_request.app.state.templates.TemplateResponse.assert_called_once()
        call_args = mock_request.app.state.templates.TemplateResponse.call_args
        assert call_args[0][0] == "buyer/index.html"
        template_data = call_args[0][1]
        assert template_data["results"] == mock_orchestrator_response
        assert template_data["error"] is None
        assert (
            template_data["submitted_brief"]
            == "Sports advertising campaign for young adults"
        )
        assert template_data["selected_internal"] == ["publisher-a"]
        assert template_data["selected_external"] == ["https://agent1.com/adcp"]

    @pytest.mark.asyncio
    async def test_submit_buyer_brief_with_timeout(self):
        """Test POST /buyer with custom timeout."""
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
            "context_id": "ctx-456",
            "total_agents": 1,
            "timeout_ms": 15000,
        }

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

            # Call function with custom timeout
            await submit_buyer_brief(
                request=mock_request,
                brief="Test brief",
                internal_tenants=["publisher-a"],
                external_agents=[],
                timeout_ms=15000,
                tenant_repo=mock_tenant_repo,
                external_agent_repo=mock_external_agent_repo,
            )

        # Verify timeout was passed to orchestrator
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        request_json = call_args[1]["json"]
        assert request_json["timeout_ms"] == 15000

    @pytest.mark.asyncio
    async def test_submit_buyer_brief_orchestrator_error(self):
        """Test POST /buyer when orchestrator returns error."""
        # Mock repositories
        mock_tenant_repo = MagicMock()
        mock_external_agent_repo = MagicMock()
        mock_tenants = [MagicMock(id=1, name="Publisher A", slug="publisher-a")]
        mock_tenant_repo.list_all.return_value = mock_tenants
        mock_external_agent_repo.list_enabled.return_value = []

        # Mock request
        mock_request = MagicMock()
        mock_request.app.state.templates.TemplateResponse = MagicMock()

        # Mock orchestrator error response
        mock_http_response = MagicMock()
        mock_http_response.status_code = 400
        mock_http_response.json.return_value = {"detail": "No agents available"}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__ = AsyncMock(
                return_value=mock_client
            )
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_client.post.return_value = mock_http_response

            # Call function
            await submit_buyer_brief(
                request=mock_request,
                brief="Test brief",
                internal_tenants=["publisher-a"],
                external_agents=[],
                timeout_ms=None,
                tenant_repo=mock_tenant_repo,
                external_agent_repo=mock_external_agent_repo,
            )

        # Verify error is displayed
        mock_request.app.state.templates.TemplateResponse.assert_called_once()
        call_args = mock_request.app.state.templates.TemplateResponse.call_args
        template_data = call_args[0][1]
        assert template_data["error"] == "Orchestration error: No agents available"
        assert template_data["results"] is None
