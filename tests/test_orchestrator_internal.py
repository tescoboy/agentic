"""Tests for orchestrator internal agent fan-out functionality."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.orchestrator import orchestrate


class TestOrchestratorInternal:
    """Test internal agent orchestration."""

    @pytest.mark.asyncio
    async def test_orchestrate_two_internal_agents_success(self):
        """Test successful orchestration to two internal agents."""
        # Mock httpx.AsyncClient.post to return valid AdCP responses
        mock_responses = [
            MagicMock(
                status_code=200,
                json=lambda: {
                    "items": [
                        {
                            "product_id": "prod_1",
                            "reason": "Perfect match for sports",
                            "score": 0.95,
                        },
                        {
                            "product_id": "prod_2",
                            "reason": "Good demographic fit",
                            "score": 0.85,
                        },
                    ]
                },
            ),
            MagicMock(
                status_code=200,
                json=lambda: {
                    "items": [
                        {
                            "product_id": "prod_3",
                            "reason": "Premium inventory",
                            "score": 0.92,
                        },
                        {
                            "product_id": "prod_4",
                            "reason": "High engagement rates",
                            "score": 0.78,
                        },
                    ]
                },
            ),
        ]

        with patch("httpx.AsyncClient.post", side_effect=mock_responses):
            result = await orchestrate(
                brief="Sports advertising campaign",
                internal_tenant_slugs=["tenant-a", "tenant-b"],
                external_urls=[],
                timeout_ms=5000,
            )

        # Verify structure
        assert "results" in result
        assert "context_id" in result
        assert "total_agents" in result
        assert "timeout_ms" in result

        # Verify agent count
        assert result["total_agents"] == 2
        assert len(result["results"]) == 2

        # Verify first agent results
        agent1 = result["results"][0]
        assert agent1["agent"]["type"] == "internal"
        assert agent1["agent"]["slug"] == "tenant-a"
        assert agent1["error"] is None
        assert len(agent1["items"]) == 2
        assert agent1["items"][0]["product_id"] == "prod_1"
        assert agent1["items"][0]["reason"] == "Perfect match for sports"
        assert agent1["items"][0]["score"] == 0.95

        # Verify second agent results
        agent2 = result["results"][1]
        assert agent2["agent"]["type"] == "internal"
        assert agent2["agent"]["slug"] == "tenant-b"
        assert agent2["error"] is None
        assert len(agent2["items"]) == 2
        assert agent2["items"][0]["product_id"] == "prod_3"
        assert agent2["items"][0]["reason"] == "Premium inventory"
        assert agent2["items"][0]["score"] == 0.92

    @pytest.mark.asyncio
    async def test_orchestrate_internal_agent_timeout(self):
        """Test internal agent timeout handling."""
        from httpx import TimeoutException

        with patch(
            "httpx.AsyncClient.post", side_effect=TimeoutException("Request timed out")
        ):
            result = await orchestrate(
                brief="Test brief",
                internal_tenant_slugs=["tenant-timeout"],
                external_urls=[],
                timeout_ms=1000,
            )

        assert len(result["results"]) == 1
        agent_result = result["results"][0]
        assert agent_result["agent"]["type"] == "internal"
        assert agent_result["agent"]["slug"] == "tenant-timeout"
        assert agent_result["error"]["type"] == "timeout"
        assert "timed out" in agent_result["error"]["message"]
        assert agent_result["error"]["status"] == 408
        assert len(agent_result["items"]) == 0

    @pytest.mark.asyncio
    async def test_orchestrate_internal_agent_invalid_response(self):
        """Test internal agent invalid response handling."""
        mock_response = MagicMock(
            status_code=200,
            json=lambda: {"invalid": "response"},  # Missing required 'items' field
        )

        with patch("httpx.AsyncClient.post", return_value=mock_response):
            result = await orchestrate(
                brief="Test brief",
                internal_tenant_slugs=["tenant-invalid"],
                external_urls=[],
                timeout_ms=5000,
            )

        assert len(result["results"]) == 1
        agent_result = result["results"][0]
        assert agent_result["agent"]["type"] == "internal"
        assert agent_result["agent"]["slug"] == "tenant-invalid"
        assert agent_result["error"]["type"] == "invalid_response"
        assert "AdCP contract" in agent_result["error"]["message"]
        assert agent_result["error"]["status"] == 200
        assert len(agent_result["items"]) == 0

    @pytest.mark.asyncio
    async def test_orchestrate_empty_brief_validation(self):
        """Test validation of empty brief."""
        with pytest.raises(ValueError, match="Brief must be non-empty"):
            await orchestrate(
                brief="",
                internal_tenant_slugs=["tenant-a"],
                external_urls=[],
                timeout_ms=5000,
            )

    @pytest.mark.asyncio
    async def test_orchestrate_no_agents_validation(self):
        """Test validation when no agents are specified."""
        with pytest.raises(ValueError, match="At least one agent"):
            await orchestrate(
                brief="Test brief",
                internal_tenant_slugs=[],
                external_urls=[],
                timeout_ms=5000,
            )

    @pytest.mark.asyncio
    async def test_orchestrator_no_repository_imports(self):
        """Test that orchestrator service has no repository imports."""
        import app.services.orchestrator as orchestrator_module

        # Check that the module doesn't import any repositories
        module_source = orchestrator_module.__file__
        with open(module_source, "r") as f:
            content = f.read()

        # Verify no repository imports
        assert "from ..repositories" not in content
        assert "import repositories" not in content
        assert "repository" not in content.lower()

        # Verify it only imports what it needs
        assert "import httpx" in content
        assert "import asyncio" in content
        assert "from ..config import settings" in content
