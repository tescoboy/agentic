"""Tests for orchestrator external agent functionality."""

import pytest
from unittest.mock import patch, MagicMock

from app.services.orchestrator import orchestrate


class TestOrchestratorExternal:
    """Test external agent orchestration."""

    @pytest.mark.asyncio
    async def test_orchestrate_external_agent_success(self):
        """Test successful orchestration to external agent."""
        mock_response = MagicMock(
            status_code=200,
            json=lambda: {
                "items": [
                    {
                        "product_id": "ext_prod_1",
                        "reason": "Premium video inventory",
                        "score": 0.88,
                    },
                    {
                        "product_id": "ext_prod_2",
                        "reason": "Targeted audience match",
                        "score": 0.76,
                    },
                ]
            },
        )

        with patch("httpx.AsyncClient.post", return_value=mock_response):
            result = await orchestrate(
                brief="Video advertising campaign",
                internal_tenant_slugs=[],
                external_urls=["https://api.external-agent.com/adcp"],
                timeout_ms=5000,
            )

        # Verify structure
        assert result["total_agents"] == 1
        assert len(result["results"]) == 1

        # Verify external agent results
        agent_result = result["results"][0]
        assert agent_result["agent"]["type"] == "external"
        assert agent_result["agent"]["url"] == "https://api.external-agent.com/adcp"
        assert agent_result["error"] is None
        assert len(agent_result["items"]) == 2
        assert agent_result["items"][0]["product_id"] == "ext_prod_1"
        assert agent_result["items"][0]["reason"] == "Premium video inventory"
        assert agent_result["items"][0]["score"] == 0.88

    @pytest.mark.asyncio
    async def test_orchestrate_external_agent_timeout(self):
        """Test external agent timeout handling."""
        from httpx import TimeoutException

        with patch(
            "httpx.AsyncClient.post", side_effect=TimeoutException("Request timed out")
        ):
            result = await orchestrate(
                brief="Test brief",
                internal_tenant_slugs=[],
                external_urls=["https://slow-external-agent.com/adcp"],
                timeout_ms=1000,
            )

        assert len(result["results"]) == 1
        agent_result = result["results"][0]
        assert agent_result["agent"]["type"] == "external"
        assert agent_result["agent"]["url"] == "https://slow-external-agent.com/adcp"
        assert agent_result["error"]["type"] == "timeout"
        assert "timed out" in agent_result["error"]["message"]
        assert agent_result["error"]["status"] == 408
        assert len(agent_result["items"]) == 0

    @pytest.mark.asyncio
    async def test_orchestrate_external_agent_http_error(self):
        """Test external agent HTTP error handling."""
        mock_response = MagicMock(status_code=500, text="Internal server error")

        with patch("httpx.AsyncClient.post", return_value=mock_response):
            result = await orchestrate(
                brief="Test brief",
                internal_tenant_slugs=[],
                external_urls=["https://error-external-agent.com/adcp"],
                timeout_ms=5000,
            )

        assert len(result["results"]) == 1
        agent_result = result["results"][0]
        assert agent_result["agent"]["type"] == "external"
        assert agent_result["agent"]["url"] == "https://error-external-agent.com/adcp"
        assert agent_result["error"]["type"] == "http"
        assert "HTTP 500" in agent_result["error"]["message"]
        assert agent_result["error"]["status"] == 500
        assert len(agent_result["items"]) == 0

    @pytest.mark.asyncio
    async def test_orchestrate_external_agent_wrapped_response(self):
        """Test external agent with wrapped AdCP response."""
        # Some external agents might wrap responses in message/context_id/data
        mock_response = MagicMock(
            status_code=200,
            json=lambda: {
                "message": "Success",
                "context_id": "ctx-123",
                "data": {
                    "items": [
                        {
                            "product_id": "wrapped_prod_1",
                            "reason": "Wrapped response",
                            "score": 0.90,
                        }
                    ]
                },
            },
        )

        with patch("httpx.AsyncClient.post", return_value=mock_response):
            result = await orchestrate(
                brief="Test brief",
                internal_tenant_slugs=[],
                external_urls=["https://wrapped-external-agent.com/adcp"],
                timeout_ms=5000,
            )

        # Should still be invalid because items is not at root level
        assert len(result["results"]) == 1
        agent_result = result["results"][0]
        assert agent_result["error"]["type"] == "invalid_response"
        assert "AdCP contract" in agent_result["error"]["message"]
        assert len(agent_result["items"]) == 0

    @pytest.mark.asyncio
    async def test_orchestrate_mixed_internal_external_agents(self):
        """Test orchestration with both internal and external agents."""
        mock_responses = [
            # Internal agent response
            MagicMock(
                status_code=200,
                json=lambda: {
                    "items": [
                        {
                            "product_id": "int_prod_1",
                            "reason": "Internal match",
                            "score": 0.85,
                        }
                    ]
                },
            ),
            # External agent response
            MagicMock(
                status_code=200,
                json=lambda: {
                    "items": [
                        {
                            "product_id": "ext_prod_1",
                            "reason": "External match",
                            "score": 0.92,
                        }
                    ]
                },
            ),
        ]

        with patch("httpx.AsyncClient.post", side_effect=mock_responses):
            result = await orchestrate(
                brief="Mixed campaign",
                internal_tenant_slugs=["tenant-mixed"],
                external_urls=["https://mixed-external-agent.com/adcp"],
                timeout_ms=5000,
            )

        assert result["total_agents"] == 2
        assert len(result["results"]) == 2

        # Verify internal agent
        internal_result = result["results"][0]
        assert internal_result["agent"]["type"] == "internal"
        assert internal_result["agent"]["slug"] == "tenant-mixed"
        assert internal_result["error"] is None
        assert internal_result["items"][0]["product_id"] == "int_prod_1"

        # Verify external agent
        external_result = result["results"][1]
        assert external_result["agent"]["type"] == "external"
        assert (
            external_result["agent"]["url"] == "https://mixed-external-agent.com/adcp"
        )
        assert external_result["error"] is None
        assert external_result["items"][0]["product_id"] == "ext_prod_1"

    @pytest.mark.asyncio
    async def test_orchestrate_external_agent_malformed_items(self):
        """Test external agent with malformed items array."""
        mock_response = MagicMock(
            status_code=200,
            json=lambda: {
                "items": [
                    {"product_id": "valid_prod", "reason": "Valid item"},
                    {"invalid": "item"},  # Missing required fields
                    {"product_id": "another_valid", "reason": "Another valid"},
                ]
            },
        )

        with patch("httpx.AsyncClient.post", return_value=mock_response):
            result = await orchestrate(
                brief="Test brief",
                internal_tenant_slugs=[],
                external_urls=["https://malformed-external-agent.com/adcp"],
                timeout_ms=5000,
            )

        # Should be invalid due to malformed item
        assert len(result["results"]) == 1
        agent_result = result["results"][0]
        assert agent_result["error"]["type"] == "invalid_response"
        assert "AdCP contract" in agent_result["error"]["message"]
        assert len(agent_result["items"]) == 0
