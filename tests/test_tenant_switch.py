"""Tests for tenant switching functionality."""


def test_tenant_switch_flow(client):
    """Test complete tenant switching flow."""

    # Create two tenants
    client.post(
        "/tenants/add",
        data={"name": "First Publisher", "slug": "first-publisher"},
        follow_redirects=False,
    )
    client.post(
        "/tenants/add",
        data={"name": "Second Publisher", "slug": "second-publisher"},
        follow_redirects=False,
    )

    # Select first tenant
    response = client.post(
        "/tenants/select", data={"tenant_id": 1}, follow_redirects=False
    )
    assert response.status_code == 302

    # Check cookie was set
    assert "active_tenant_id=1" in response.headers.get("set-cookie", "")

    # Get current tenant
    response = client.get("/tenants/current")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "First Publisher"
    assert data["slug"] == "first-publisher"

    # Switch to second tenant
    response = client.post(
        "/tenants/select", data={"tenant_id": 2}, follow_redirects=False
    )
    assert response.status_code == 302

    # Check cookie was updated
    assert "active_tenant_id=2" in response.headers.get("set-cookie", "")

    # Get current tenant
    response = client.get("/tenants/current")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 2
    assert data["name"] == "Second Publisher"
    assert data["slug"] == "second-publisher"


def test_no_active_tenant(client):
    """Test that /tenants/current returns 404 when no cookie is set."""
    response = client.get("/tenants/current")
    assert response.status_code == 404

    data = response.json()
    assert "detail" in data
    assert "error" in data["detail"]
    assert "No active tenant selected" in data["detail"]["error"]


def test_invalid_tenant_id(client):
    """Test that selecting invalid tenant ID returns 404."""
    response = client.post(
        "/tenants/select", data={"tenant_id": 999}, follow_redirects=False
    )
    assert response.status_code == 404


def test_tenant_switch_with_cookies(client):
    """Test tenant switching with cookies in subsequent requests."""

    # Create tenant
    client.post(
        "/tenants/add",
        data={"name": "Test Publisher", "slug": "test-publisher"},
        follow_redirects=False,
    )

    # Select tenant
    response = client.post(
        "/tenants/select", data={"tenant_id": 1}, follow_redirects=False
    )
    assert response.status_code == 302

    # Get cookies from response
    cookies = response.headers.get("set-cookie", "")

    # Make request with cookies
    headers = {"Cookie": cookies}
    response = client.get("/tenants/current", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "Test Publisher"
