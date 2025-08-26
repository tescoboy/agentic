"""Tests for health endpoint."""

import pytest

from app.main import app


@pytest.mark.asyncio
async def test_health_endpoint():
    """Test that health endpoint returns correct JSON payload."""
    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert "service" in data
    assert "version" in data

    assert data["status"] == "ok"
    assert data["service"] == "adcp-demo-orchestrator"
    assert data["version"] == "0.1.0"
