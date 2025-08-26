"""Tests for buyer flow with partial agent failures."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from app.routes.buyer import submit_buyer_brief


class TestBuyerPartialFail:
    """Test buyer flow with partial agent failures."""

    @pytest.mark.asyncio
    async def test_submit_buyer_brief_partial_failures(self):
        """Test POST /buyer with mixed success and failure results."""
        # Mock repositories
        mock_tenant_repo = MagicMock()
        mock_external_agent_repo = MagicMock()
        mock_tenants = [MagicMock(id=1, name="Publisher A", slug="publisher-a")]
        mock_tenant_repo.list_all.return_value = mock_tenants
        mock_external_agent_repo.list_enabled.return_value = []

        # Mock request
        mock_request = MagicMock()
        mock_request.app.state.templates.TemplateResponse = MagicMock()

        # Mock orchestrator response with mixed results
        mock_orchestrator_response = {
            "results": [
                {
                    "agent": {"type": "internal", "slug": "publisher-a"},
                    "items": [
                        {
                            "product_id": "prod_1",
                            "reason": "Successfully found matching products",
                            "score": 0.92,
                        }
                    ],
                    "error": None,
                },
                {
                    "agent": {
                        "type": "external",
                        "url": "https://failing-agent.com/adcp",
                    },
                    "items": [],
                    "error": {
                        "type": "timeout",
                        "message": "Request timed out after 8000ms",
                        "status": 408,
                    },
                },
            ],
            "context_id": "ctx-mixed",
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
                brief="Test brief with mixed results",
                internal_tenants=["publisher-a"],
                external_agents=["https://failing-agent.com/adcp"],
                timeout_ms=None,
                tenant_repo=mock_tenant_repo,
                external_agent_repo=mock_external_agent_repo,
            )

        # Verify template called with mixed results
        mock_request.app.state.templates.TemplateResponse.assert_called_once()
        call_args = mock_request.app.state.templates.TemplateResponse.call_args
        template_data = call_args[0][1]
        assert template_data["results"] == mock_orchestrator_response
        assert template_data["error"] is None

        # Verify results contain both success and failure
        results = template_data["results"]["results"]
        assert len(results) == 2

        # First agent should have items
        assert results[0]["agent"]["slug"] == "publisher-a"
        assert results[0]["error"] is None
        assert len(results[0]["items"]) == 1
        assert results[0]["items"][0]["product_id"] == "prod_1"

        # Second agent should have error
        assert results[1]["agent"]["url"] == "https://failing-agent.com/adcp"
        assert results[1]["error"]["type"] == "timeout"
        assert results[1]["error"]["message"] == "Request timed out after 8000ms"
        assert len(results[1]["items"]) == 0

    @pytest.mark.asyncio
    async def test_submit_buyer_brief_circuit_breaker_error(self):
        """Test POST /buyer with circuit breaker error."""
        # Mock repositories
        mock_tenant_repo = MagicMock()
        mock_external_agent_repo = MagicMock()
        mock_tenants = [MagicMock(id=1, name="Publisher A", slug="publisher-a")]
        mock_tenant_repo.list_all.return_value = mock_tenants
        mock_external_agent_repo.list_enabled.return_value = []

        # Mock request
        mock_request = MagicMock()
        mock_request.app.state.templates.TemplateResponse = MagicMock()

        # Mock orchestrator response with circuit breaker error
        mock_orchestrator_response = {
            "results": [
                {
                    "agent": {"type": "internal", "slug": "publisher-a"},
                    "items": [],
                    "error": {
                        "type": "breaker",
                        "message": "Circuit breaker open - agent skipped",
                        "status": None,
                    },
                }
            ],
            "context_id": "ctx-breaker",
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

            # Call function
            await submit_buyer_brief(
                request=mock_request,
                brief="Test brief with circuit breaker",
                internal_tenants=["publisher-a"],
                external_agents=[],
                timeout_ms=None,
                tenant_repo=mock_tenant_repo,
                external_agent_repo=mock_external_agent_repo,
            )

        # Verify template called with circuit breaker error
        mock_request.app.state.templates.TemplateResponse.assert_called_once()
        call_args = mock_request.app.state.templates.TemplateResponse.call_args
        template_data = call_args[0][1]
        assert template_data["results"] == mock_orchestrator_response

        # Verify circuit breaker error
        results = template_data["results"]["results"]
        assert len(results) == 1
        assert results[0]["error"]["type"] == "breaker"
        assert "Circuit breaker open" in results[0]["error"]["message"]

    @pytest.mark.asyncio
    async def test_submit_buyer_brief_invalid_response_error(self):
        """Test POST /buyer with invalid response error."""
        # Mock repositories
        mock_tenant_repo = MagicMock()
        mock_external_agent_repo = MagicMock()
        mock_tenants = [MagicMock(id=1, name="Publisher A", slug="publisher-a")]
        mock_tenant_repo.list_all.return_value = mock_tenants
        mock_external_agent_repo.list_enabled.return_value = []

        # Mock request
        mock_request = MagicMock()
        mock_request.app.state.templates.TemplateResponse = MagicMock()

        # Mock orchestrator response with invalid response error
        mock_orchestrator_response = {
            "results": [
                {
                    "agent": {
                        "type": "external",
                        "url": "https://invalid-agent.com/adcp",
                    },
                    "items": [],
                    "error": {
                        "type": "invalid_response",
                        "message": "Agent response does not match AdCP contract",
                        "status": 200,
                    },
                }
            ],
            "context_id": "ctx-invalid",
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

            # Call function
            await submit_buyer_brief(
                request=mock_request,
                brief="Test brief with invalid response",
                internal_tenants=[],
                external_agents=["https://invalid-agent.com/adcp"],
                timeout_ms=None,
                tenant_repo=mock_tenant_repo,
                external_agent_repo=mock_external_agent_repo,
            )

        # Verify template called with invalid response error
        mock_request.app.state.templates.TemplateResponse.assert_called_once()
        call_args = mock_request.app.state.templates.TemplateResponse.call_args
        template_data = call_args[0][1]
        assert template_data["results"] == mock_orchestrator_response

        # Verify invalid response error
        results = template_data["results"]["results"]
        assert len(results) == 1
        assert results[0]["error"]["type"] == "invalid_response"
        assert "AdCP contract" in results[0]["error"]["message"]

    @pytest.mark.asyncio
    async def test_submit_buyer_brief_http_error(self):
        """Test POST /buyer with HTTP error from agent."""
        # Mock repositories
        mock_tenant_repo = MagicMock()
        mock_external_agent_repo = MagicMock()
        mock_tenants = [MagicMock(id=1, name="Publisher A", slug="publisher-a")]
        mock_tenant_repo.list_all.return_value = mock_tenants
        mock_external_agent_repo.list_enabled.return_value = []

        # Mock request
        mock_request = MagicMock()
        mock_request.app.state.templates.TemplateResponse = MagicMock()

        # Mock orchestrator response with HTTP error
        mock_orchestrator_response = {
            "results": [
                {
                    "agent": {
                        "type": "external",
                        "url": "https://http-error-agent.com/adcp",
                    },
                    "items": [],
                    "error": {
                        "type": "http",
                        "message": "HTTP 500: Internal server error",
                        "status": 500,
                    },
                }
            ],
            "context_id": "ctx-http-error",
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

            # Call function
            await submit_buyer_brief(
                request=mock_request,
                brief="Test brief with HTTP error",
                internal_tenants=[],
                external_agents=["https://http-error-agent.com/adcp"],
                timeout_ms=None,
                tenant_repo=mock_tenant_repo,
                external_agent_repo=mock_external_agent_repo,
            )

        # Verify template called with HTTP error
        mock_request.app.state.templates.TemplateResponse.assert_called_once()
        call_args = mock_request.app.state.templates.TemplateResponse.call_args
        template_data = call_args[0][1]
        assert template_data["results"] == mock_orchestrator_response

        # Verify HTTP error
        results = template_data["results"]["results"]
        assert len(results) == 1
        assert results[0]["error"]["type"] == "http"
        assert "HTTP 500" in results[0]["error"]["message"]
        assert results[0]["error"]["status"] == 500
