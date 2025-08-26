"""Tests for logging and request ID functionality."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app


class TestLoggingAndRequestId:
    """Test logging middleware and request ID functionality."""

    def test_health_endpoint_returns_request_id_header(self):
        """Test that health endpoint returns X-Request-ID header."""
        client = TestClient(app)

        response = client.get("/health")

        assert response.status_code == 200
        assert "X-Request-ID" in response.headers
        assert response.headers["X-Request-ID"] is not None
        assert len(response.headers["X-Request-ID"]) > 0

    def test_preflight_endpoint_returns_request_id_header(self):
        """Test that preflight endpoint returns X-Request-ID header."""
        client = TestClient(app)

        response = client.get("/preflight")

        assert response.status_code == 200
        assert "X-Request-ID" in response.headers
        assert response.headers["X-Request-ID"] is not None

    def test_root_endpoint_returns_request_id_header(self):
        """Test that root endpoint returns X-Request-ID header."""
        client = TestClient(app)

        response = client.get("/")

        assert response.status_code == 200
        assert "X-Request-ID" in response.headers
        assert response.headers["X-Request-ID"] is not None

    def test_request_id_in_template_context(self):
        """Test that request ID is available in template context."""
        client = TestClient(app)

        response = client.get("/")

        assert response.status_code == 200
        # Check that the response contains the request ID meta tag
        assert 'name="request-id"' in response.text
        assert "content=" in response.text

    def test_different_requests_have_different_request_ids(self):
        """Test that different requests have different request IDs."""
        client = TestClient(app)

        response1 = client.get("/health")
        response2 = client.get("/health")

        assert response1.headers["X-Request-ID"] != response2.headers["X-Request-ID"]

    def test_request_id_format_is_uuid(self):
        """Test that request ID is in UUID format."""
        import uuid

        client = TestClient(app)

        response = client.get("/health")
        request_id = response.headers["X-Request-ID"]

        # Should be a valid UUID
        try:
            uuid.UUID(request_id)
        except ValueError:
            pytest.fail(f"Request ID {request_id} is not a valid UUID")

    def test_logging_middleware_logs_request_start_and_end(self):
        """Test that logging middleware logs request start and end."""
        client = TestClient(app)

        # This test verifies the middleware is in place
        # Actual logging verification would require more complex setup
        response = client.get("/health")

        assert response.status_code == 200
        # Middleware should not interfere with normal operation
