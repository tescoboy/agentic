"""Tests for strict MCP validation and error handling."""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.main import app


class TestMCPValidationStrict:
    """Test strict MCP validation and error handling."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)

    def test_wrong_content_type_returns_415(self):
        """Test that wrong content type returns 415 Unsupported Media Type."""
        # Test with text/plain instead of application/json
        response = self.client.post(
            "/mcp/agents/test-tenant/rank",
            data="{'brief': 'test brief'}",
            headers={"Content-Type": "text/plain"},
        )

        assert response.status_code == 415
        assert "unsupported media type" in response.text.lower()

    def test_malformed_json_returns_400(self):
        """Test that malformed JSON returns 400 Bad Request."""
        # Test with invalid JSON
        response = self.client.post(
            "/mcp/agents/test-tenant/rank",
            data='{"brief": "test brief", "context_id": "invalid json}',
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 400
        assert "json" in response.text.lower()

    def test_missing_brief_field_returns_400(self):
        """Test that missing brief field returns 400 with field name in message."""
        # Test with empty JSON object
        response = self.client.post(
            "/mcp/agents/test-tenant/rank",
            json={},
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 400
        assert "brief" in response.text.lower()
        assert "field" in response.text.lower() or "required" in response.text.lower()

    def test_null_brief_field_returns_400(self):
        """Test that null brief field returns 400."""
        response = self.client.post(
            "/mcp/agents/test-tenant/rank",
            json={"brief": None},
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 400
        assert "brief" in response.text.lower()

    def test_unknown_tenant_slug_returns_404(self):
        """Test that unknown tenant slug returns 404 Not Found."""
        response = self.client.post(
            "/mcp/agents/unknown-tenant/rank",
            json={"brief": "test brief"},
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 404
        assert "unknown-tenant" in response.text.lower()
        assert "not found" in response.text.lower()

    def test_invalid_tenant_slug_format_returns_404(self):
        """Test that invalid tenant slug format returns 404."""
        # Test with invalid slug format
        response = self.client.post(
            "/mcp/agents/invalid@slug!format/rank",
            json={"brief": "test brief"},
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 404
        assert "not found" in response.text.lower()

    def test_empty_tenant_slug_returns_404(self):
        """Test that empty tenant slug returns 404."""
        response = self.client.post(
            "/mcp/agents//rank",
            json={"brief": "test brief"},
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 404

    def test_missing_context_id_is_optional(self):
        """Test that context_id is optional and can be omitted."""
        # Mock tenant and products to avoid actual processing
        with patch("app.routes.mcp.rank_products") as mock_rank:
            mock_rank.return_value = {"items": []}

            response = self.client.post(
                "/mcp/agents/test-tenant/rank",
                json={"brief": "test brief"},  # No context_id
                headers={"Content-Type": "application/json"},
            )

            # Should not return 400 for missing context_id
            assert response.status_code != 400

    def test_invalid_context_id_type_returns_400(self):
        """Test that invalid context_id type returns 400."""
        response = self.client.post(
            "/mcp/agents/test-tenant/rank",
            json={"brief": "test brief", "context_id": 123},  # Should be string
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 400
        assert (
            "context_id" in response.text.lower()
            or "validation" in response.text.lower()
        )

    def test_extra_fields_are_ignored(self):
        """Test that extra fields in request are ignored."""
        # Mock tenant and products to avoid actual processing
        with patch("app.routes.mcp.rank_products") as mock_rank:
            mock_rank.return_value = {"items": []}

            response = self.client.post(
                "/mcp/agents/test-tenant/rank",
                json={
                    "brief": "test brief",
                    "extra_field": "should be ignored",
                    "another_extra": 123,
                },
                headers={"Content-Type": "application/json"},
            )

            # Should not return 400 for extra fields
            assert response.status_code != 400

    def test_brief_with_whitespace_only_returns_400(self):
        """Test that brief with only whitespace returns 400."""
        response = self.client.post(
            "/mcp/agents/test-tenant/rank",
            json={"brief": "   \n\t   "},
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 400
        assert "brief" in response.text.lower()
        assert "empty" in response.text.lower() or "required" in response.text.lower()

    def test_brief_with_empty_string_returns_400(self):
        """Test that brief with empty string returns 400."""
        response = self.client.post(
            "/mcp/agents/test-tenant/rank",
            json={"brief": ""},
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 400
        assert "brief" in response.text.lower()
        assert "empty" in response.text.lower() or "required" in response.text.lower()

    def test_brief_with_maximum_length_is_accepted(self):
        """Test that brief with maximum reasonable length is accepted."""
        # Create a brief with 1000 characters
        long_brief = "a" * 1000

        # Mock tenant and products to avoid actual processing
        with patch("app.routes.mcp.rank_products") as mock_rank:
            mock_rank.return_value = {"items": []}

            response = self.client.post(
                "/mcp/agents/test-tenant/rank",
                json={"brief": long_brief},
                headers={"Content-Type": "application/json"},
            )

            # Should not return 400 for reasonable length
            assert response.status_code != 400

    def test_brief_with_extreme_length_returns_400(self):
        """Test that brief with extreme length returns 400."""
        # Create a brief with 100,000 characters (unreasonable)
        extreme_brief = "a" * 100000

        response = self.client.post(
            "/mcp/agents/test-tenant/rank",
            json={"brief": extreme_brief},
            headers={"Content-Type": "application/json"},
        )

        # Should return 400 for extreme length
        assert response.status_code == 400

    def test_mcp_info_endpoint_returns_correct_format(self):
        """Test that GET /mcp/ returns correct format."""
        response = self.client.get("/mcp/")

        assert response.status_code == 200
        data = response.json()

        # Verify required fields
        assert "service" in data
        assert "adcp_version" in data
        assert "commit_hash" in data
        assert "capabilities" in data

        # Verify data types
        assert isinstance(data["service"], str)
        assert isinstance(data["adcp_version"], str)
        assert isinstance(data["commit_hash"], str)
        assert isinstance(data["capabilities"], list)

        # Verify capabilities contains ranking
        assert "ranking" in data["capabilities"]

    def test_mcp_info_endpoint_accepts_no_parameters(self):
        """Test that GET /mcp/ accepts no parameters."""
        response = self.client.get("/mcp/")

        assert response.status_code == 200

    def test_mcp_info_endpoint_rejects_post(self):
        """Test that GET /mcp/ rejects POST requests."""
        response = self.client.post("/mcp/")

        assert response.status_code == 405  # Method Not Allowed

    def test_rank_endpoint_rejects_get(self):
        """Test that POST /mcp/agents/{slug}/rank rejects GET requests."""
        response = self.client.get("/mcp/agents/test-tenant/rank")

        assert response.status_code == 405  # Method Not Allowed

    def test_rank_endpoint_rejects_put(self):
        """Test that POST /mcp/agents/{slug}/rank rejects PUT requests."""
        response = self.client.put("/mcp/agents/test-tenant/rank")

        assert response.status_code == 405  # Method Not Allowed

    def test_rank_endpoint_rejects_delete(self):
        """Test that POST /mcp/agents/{slug}/rank rejects DELETE requests."""
        response = self.client.delete("/mcp/agents/test-tenant/rank")

        assert response.status_code == 405  # Method Not Allowed
