"""Tests for orchestrator integration with internal MCP endpoints."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from app.routes.orchestrator import orchestrate_brief


class TestOrchestratorLoopback:
    """Test orchestrator calling internal MCP endpoints."""

    @pytest.mark.asyncio
    async def test_orchestrator_internal_loopback_success(self):
        """Test orchestrator calling internal MCP endpoints successfully."""
        # Mock repositories
        mock_tenant_repo = MagicMock()
        mock_external_agent_repo = MagicMock()

        # Mock tenants
        mock_tenants = [
            MagicMock(id=1, name="Publisher A", slug="publisher-a"),
            MagicMock(id=2, name="Publisher B", slug="publisher-b"),
        ]
        mock_tenant_repo.list_all.return_value = mock_tenants
        mock_external_agent_repo.list_enabled.return_value = []

        # Mock HTTP responses for internal MCP calls
        mock_response_1 = MagicMock()
        mock_response_1.status_code = 200
        mock_response_1.json.return_value = {
            "items": [
                {
                    "product_id": "prod_1",
                    "reason": "Perfect match from Publisher A",
                    "score": 0.95,
                }
            ]
        }

        mock_response_2 = MagicMock()
        mock_response_2.status_code = 200
        mock_response_2.json.return_value = {
            "items": [
                {
                    "product_id": "prod_2",
                    "reason": "Good match from Publisher B",
                    "score": 0.85,
                }
            ]
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__ = AsyncMock(
                return_value=mock_client
            )
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

            # Mock different responses for different URLs
            def mock_post(url, **kwargs):
                if "publisher-a" in url:
                    return mock_response_1
                elif "publisher-b" in url:
                    return mock_response_2
                else:
                    raise Exception(f"Unexpected URL: {url}")

            mock_client.post.side_effect = mock_post

            # Create request
            from app.routes.orchestrator import OrchestrateRequest

            request = OrchestrateRequest(
                brief="Sports advertising campaign",
                internal_tenant_slugs=["publisher-a", "publisher-b"],
                external_urls=None,
            )

            # Call orchestrator
            result = await orchestrate_brief(
                request=request,
                tenant_repo=mock_tenant_repo,
                external_agent_repo=mock_external_agent_repo,
            )

            # Verify result
            assert result.total_agents == 2
            assert len(result.results) == 2

            # Verify both internal agents were called
            assert mock_client.post.call_count == 2

            # Verify the URLs that were called
            call_args = mock_client.post.call_args_list
            urls_called = [call[1]["url"] for call in call_args]
            assert "http://localhost:8000/mcp/agents/publisher-a/rank" in urls_called
            assert "http://localhost:8000/mcp/agents/publisher-b/rank" in urls_called

            # Verify results are aggregated correctly
            results = result.results
            assert results[0]["agent"]["type"] == "internal"
            assert results[0]["agent"]["slug"] == "publisher-a"
            assert results[0]["error"] is None
            assert len(results[0]["items"]) == 1
            assert results[0]["items"][0]["product_id"] == "prod_1"

            assert results[1]["agent"]["type"] == "internal"
            assert results[1]["agent"]["slug"] == "publisher-b"
            assert results[1]["error"] is None
            assert len(results[1]["items"]) == 1
            assert results[1]["items"][0]["product_id"] == "prod_2"

    @pytest.mark.asyncio
    async def test_orchestrator_internal_loopback_partial_failure(self):
        """Test orchestrator with one internal agent failing."""
        # Mock repositories
        mock_tenant_repo = MagicMock()
        mock_external_agent_repo = MagicMock()

        # Mock tenants
        mock_tenants = [
            MagicMock(id=1, name="Publisher A", slug="publisher-a"),
            MagicMock(id=2, name="Publisher B", slug="publisher-b"),
        ]
        mock_tenant_repo.list_all.return_value = mock_tenants
        mock_external_agent_repo.list_enabled.return_value = []

        # Mock HTTP responses - one success, one failure
        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            "items": [
                {
                    "product_id": "prod_1",
                    "reason": "Perfect match from Publisher A",
                    "score": 0.95,
                }
            ]
        }

        mock_response_failure = MagicMock()
        mock_response_failure.status_code = 422
        mock_response_failure.json.return_value = {
            "error": {
                "type": "invalid_request",
                "message": "No products found for tenant 'publisher-b'",
                "status": 422,
            }
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__ = AsyncMock(
                return_value=mock_client
            )
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

            # Mock different responses for different URLs
            def mock_post(url, **kwargs):
                if "publisher-a" in url:
                    return mock_response_success
                elif "publisher-b" in url:
                    return mock_response_failure
                else:
                    raise Exception(f"Unexpected URL: {url}")

            mock_client.post.side_effect = mock_post

            # Create request
            from app.routes.orchestrator import OrchestrateRequest

            request = OrchestrateRequest(
                brief="Sports advertising campaign",
                internal_tenant_slugs=["publisher-a", "publisher-b"],
                external_urls=None,
            )

            # Call orchestrator
            result = await orchestrate_brief(
                request=request,
                tenant_repo=mock_tenant_repo,
                external_agent_repo=mock_external_agent_repo,
            )

            # Verify result
            assert result.total_agents == 2
            assert len(result.results) == 2

            # Verify both internal agents were called
            assert mock_client.post.call_count == 2

            # Verify results - one success, one failure
            results = result.results
            assert results[0]["agent"]["type"] == "internal"
            assert results[0]["agent"]["slug"] == "publisher-a"
            assert results[0]["error"] is None
            assert len(results[0]["items"]) == 1

            assert results[1]["agent"]["type"] == "internal"
            assert results[1]["agent"]["slug"] == "publisher-b"
            assert results[1]["error"] is not None
            assert results[1]["error"]["type"] == "invalid_request"
            assert "No products found" in results[1]["error"]["message"]
            assert len(results[1]["items"]) == 0

    @pytest.mark.asyncio
    async def test_orchestrator_mixed_internal_external(self):
        """Test orchestrator with both internal and external agents."""
        # Mock repositories
        mock_tenant_repo = MagicMock()
        mock_external_agent_repo = MagicMock()

        # Mock tenants
        mock_tenants = [MagicMock(id=1, name="Publisher A", slug="publisher-a")]
        mock_tenant_repo.list_all.return_value = mock_tenants

        # Mock external agents
        mock_external_agents = [
            MagicMock(
                id=1,
                name="External Agent",
                base_url="https://external.com/adcp",
                enabled=True,
            )
        ]
        mock_external_agent_repo.list_enabled.return_value = mock_external_agents

        # Mock HTTP responses
        mock_internal_response = MagicMock()
        mock_internal_response.status_code = 200
        mock_internal_response.json.return_value = {
            "items": [
                {"product_id": "prod_1", "reason": "Internal agent match", "score": 0.9}
            ]
        }

        mock_external_response = MagicMock()
        mock_external_response.status_code = 200
        mock_external_response.json.return_value = {
            "items": [
                {
                    "product_id": "ext_prod_1",
                    "reason": "External agent match",
                    "score": 0.85,
                }
            ]
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__ = AsyncMock(
                return_value=mock_client
            )
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

            # Mock different responses for different URLs
            def mock_post(url, **kwargs):
                if "publisher-a" in url:
                    return mock_internal_response
                elif "external.com" in url:
                    return mock_external_response
                else:
                    raise Exception(f"Unexpected URL: {url}")

            mock_client.post.side_effect = mock_post

            # Create request
            from app.routes.orchestrator import OrchestrateRequest

            request = OrchestrateRequest(
                brief="Sports advertising campaign",
                internal_tenant_slugs=["publisher-a"],
                external_urls=["https://external.com/adcp"],
            )

            # Call orchestrator
            result = await orchestrate_brief(
                request=request,
                tenant_repo=mock_tenant_repo,
                external_agent_repo=mock_external_agent_repo,
            )

            # Verify result
            assert result.total_agents == 2
            assert len(result.results) == 2

            # Verify both agents were called
            assert mock_client.post.call_count == 2

            # Verify the URLs that were called
            call_args = mock_client.post.call_args_list
            urls_called = [call[1]["url"] for call in call_args]
            assert "http://localhost:8000/mcp/agents/publisher-a/rank" in urls_called
            assert "https://external.com/adcp" in urls_called

            # Verify results are aggregated correctly
            results = result.results
            assert results[0]["agent"]["type"] == "internal"
            assert results[0]["agent"]["slug"] == "publisher-a"
            assert results[0]["error"] is None
            assert len(results[0]["items"]) == 1
            assert results[0]["items"][0]["product_id"] == "prod_1"

            assert results[1]["agent"]["type"] == "external"
            assert results[1]["agent"]["url"] == "https://external.com/adcp"
            assert results[1]["error"] is None
            assert len(results[1]["items"]) == 1
            assert results[1]["items"][0]["product_id"] == "ext_prod_1"
