"""Tests for orchestrator validation and error handling."""

import pytest
from unittest.mock import patch, MagicMock

from app.services.orchestrator import orchestrate
from app.routes.orchestrator import orchestrate_brief


class TestOrchestratorValidation:
    """Test orchestrator validation and error handling."""

    @pytest.mark.asyncio
    async def test_orchestrate_empty_brief_validation(self):
        """Test validation of empty brief in service."""
        with pytest.raises(ValueError, match="Brief must be non-empty"):
            await orchestrate(
                brief="",
                internal_tenant_slugs=["tenant-a"],
                external_urls=[],
                timeout_ms=5000,
            )

    @pytest.mark.asyncio
    async def test_orchestrate_whitespace_brief_validation(self):
        """Test validation of whitespace-only brief."""
        with pytest.raises(ValueError, match="Brief must be non-empty"):
            await orchestrate(
                brief="   \n\t   ",
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
    async def test_orchestrate_malformed_agent_response(self):
        """Test handling of malformed agent response."""
        mock_response = MagicMock(
            status_code=200,
            json=lambda: {
                "items": [
                    {"product_id": "valid_prod", "reason": "Valid item"},
                    {"product_id": "missing_reason"},  # Missing required 'reason' field
                    {
                        "reason": "missing_product_id"
                    },  # Missing required 'product_id' field
                ]
            },
        )

        with patch("httpx.AsyncClient.post", return_value=mock_response):
            result = await orchestrate(
                brief="Test brief",
                internal_tenant_slugs=["tenant-malformed"],
                external_urls=[],
                timeout_ms=5000,
            )

        # Should be invalid due to malformed items
        assert len(result["results"]) == 1
        agent_result = result["results"][0]
        assert agent_result["error"]["type"] == "invalid_response"
        assert "AdCP contract" in agent_result["error"]["message"]
        assert len(agent_result["items"]) == 0

    @pytest.mark.asyncio
    async def test_orchestrate_agent_response_with_extra_fields(self):
        """Test handling of agent response with extra fields (should be tolerated)."""
        mock_response = MagicMock(
            status_code=200,
            json=lambda: {
                "items": [
                    {
                        "product_id": "prod_1",
                        "reason": "Valid item with extra fields",
                        "score": 0.85,
                        "extra_field": "should be ignored",
                        "another_extra": {"nested": "data"},
                    }
                ],
                "extra_response_field": "should be ignored",
            },
        )

        with patch("httpx.AsyncClient.post", return_value=mock_response):
            result = await orchestrate(
                brief="Test brief",
                internal_tenant_slugs=["tenant-extra-fields"],
                external_urls=[],
                timeout_ms=5000,
            )

        # Should be valid despite extra fields
        assert len(result["results"]) == 1
        agent_result = result["results"][0]
        assert agent_result["error"] is None
        assert len(agent_result["items"]) == 1
        assert agent_result["items"][0]["product_id"] == "prod_1"
        assert agent_result["items"][0]["reason"] == "Valid item with extra fields"
        assert agent_result["items"][0]["score"] == 0.85

    @pytest.mark.asyncio
    async def test_orchestrate_agent_error_response(self):
        """Test handling of agent error response."""
        mock_response = MagicMock(
            status_code=200,
            json=lambda: {
                "error": {
                    "type": "ai_config_error",
                    "message": "AI provider not configured",
                    "status": 500,
                }
            },
        )

        with patch("httpx.AsyncClient.post", return_value=mock_response):
            result = await orchestrate(
                brief="Test brief",
                internal_tenant_slugs=["tenant-error"],
                external_urls=[],
                timeout_ms=5000,
            )

        # Should be valid error response
        assert len(result["results"]) == 1
        agent_result = result["results"][0]
        assert agent_result["error"]["type"] == "ai_config_error"
        assert agent_result["error"]["message"] == "AI provider not configured"
        assert agent_result["error"]["status"] == 500
        assert len(agent_result["items"]) == 0

    @pytest.mark.asyncio
    async def test_orchestrate_malformed_error_response(self):
        """Test handling of malformed error response."""
        mock_response = MagicMock(
            status_code=200,
            json=lambda: {
                "error": {
                    "message": "Missing type field"
                    # Missing required 'type' field
                }
            },
        )

        with patch("httpx.AsyncClient.post", return_value=mock_response):
            result = await orchestrate(
                brief="Test brief",
                internal_tenant_slugs=["tenant-malformed-error"],
                external_urls=[],
                timeout_ms=5000,
            )

        # Should be invalid due to malformed error
        assert len(result["results"]) == 1
        agent_result = result["results"][0]
        assert agent_result["error"]["type"] == "invalid_response"
        assert "AdCP contract" in agent_result["error"]["message"]
        assert len(agent_result["items"]) == 0

    @pytest.mark.asyncio
    async def test_orchestrate_agent_response_without_items_or_error(self):
        """Test handling of response with neither items nor error."""
        mock_response = MagicMock(
            status_code=200,
            json=lambda: {"message": "Success but no items", "context_id": "ctx-123"},
        )

        with patch("httpx.AsyncClient.post", return_value=mock_response):
            result = await orchestrate(
                brief="Test brief",
                internal_tenant_slugs=["tenant-no-items"],
                external_urls=[],
                timeout_ms=5000,
            )

        # Should be invalid
        assert len(result["results"]) == 1
        agent_result = result["results"][0]
        assert agent_result["error"]["type"] == "invalid_response"
        assert "AdCP contract" in agent_result["error"]["message"]
        assert len(agent_result["items"]) == 0

    @pytest.mark.asyncio
    async def test_orchestrate_agent_response_with_both_items_and_error(self):
        """Test handling of response with both items and error (invalid)."""
        mock_response = MagicMock(
            status_code=200,
            json=lambda: {
                "items": [{"product_id": "prod_1", "reason": "Valid item"}],
                "error": {
                    "type": "internal",
                    "message": "Should not have both items and error",
                },
            },
        )

        with patch("httpx.AsyncClient.post", return_value=mock_response):
            result = await orchestrate(
                brief="Test brief",
                internal_tenant_slugs=["tenant-both"],
                external_urls=[],
                timeout_ms=5000,
            )

        # Should be invalid
        assert len(result["results"]) == 1
        agent_result = result["results"][0]
        assert agent_result["error"]["type"] == "invalid_response"
        assert "AdCP contract" in agent_result["error"]["message"]
        assert len(agent_result["items"]) == 0

    @pytest.mark.asyncio
    async def test_orchestrate_http_exception_handling(self):
        """Test handling of HTTP exceptions."""
        with patch("httpx.AsyncClient.post", side_effect=Exception("Unexpected error")):
            result = await orchestrate(
                brief="Test brief",
                internal_tenant_slugs=["tenant-exception"],
                external_urls=[],
                timeout_ms=5000,
            )

        # Should handle unexpected exceptions
        assert len(result["results"]) == 1
        agent_result = result["results"][0]
        assert agent_result["error"]["type"] == "internal"
        assert "Unexpected error" in agent_result["error"]["message"]
        assert agent_result["error"]["status"] == 500
        assert len(agent_result["items"]) == 0

    @pytest.mark.asyncio
    async def test_orchestrate_context_id_generation(self):
        """Test that context_id is generated for cross-request tracing."""
        mock_response = MagicMock(
            status_code=200,
            json=lambda: {"items": [{"product_id": "prod_1", "reason": "Test item"}]},
        )

        with patch("httpx.AsyncClient.post", return_value=mock_response):
            result = await orchestrate(
                brief="Test brief",
                internal_tenant_slugs=["tenant-context"],
                external_urls=[],
                timeout_ms=5000,
            )

        # Should have context_id
        assert "context_id" in result
        assert result["context_id"] is not None
        assert len(result["context_id"]) > 0

        # Should be a UUID format
        import uuid

        try:
            uuid.UUID(result["context_id"])
        except ValueError:
            pytest.fail("context_id should be a valid UUID")
