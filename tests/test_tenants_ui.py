"""Tests for tenant UI CRUD operations."""


def test_create_tenant_via_post(client):
    """Test create tenant via POST /tenants/add then GET /tenants shows it."""
    # Create tenant
    response = client.post(
        "/tenants/add",
        data={"name": "Test Publisher", "slug": "test-publisher"},
        follow_redirects=False,
    )

    # Debug: Print response details
    print(f"Status: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    if response.status_code != 302:
        print(f"Content: {response.text[:500]}")

    # Should redirect to tenants list
    assert response.status_code == 302
    assert response.headers["location"] == "/tenants"

    # Get tenants list
    response = client.get("/tenants")
    assert response.status_code == 200

    # Should show the created tenant
    content = response.text
    assert "Test Publisher" in content
    assert "test-publisher" in content


def test_edit_tenant_via_post(client):
    """Test edit tenant via POST then list reflects changes."""
    # First create a tenant
    client.post(
        "/tenants/add",
        data={"name": "Original Name", "slug": "original-slug"},
        follow_redirects=False,
    )

    # Get the edit form
    response = client.get("/tenants/1/edit")
    assert response.status_code == 200

    # Edit the tenant
    response = client.post(
        "/tenants/1/edit",
        data={"name": "Updated Name", "slug": "updated-slug"},
        follow_redirects=False,
    )

    # Should redirect to tenants list
    assert response.status_code == 302

    # Get tenants list
    response = client.get("/tenants")
    assert response.status_code == 200

    # Should show updated values
    content = response.text
    assert "Updated Name" in content
    assert "updated-slug" in content
    assert "Original Name" not in content


def test_delete_tenant_via_post(client):
    """Test delete tenant via POST then list no longer shows it."""
    # First create a tenant
    client.post(
        "/tenants/add",
        data={"name": "To Delete", "slug": "to-delete"},
        follow_redirects=False,
    )

    # Get the delete confirmation page
    response = client.get("/tenants/1/delete")
    assert response.status_code == 200

    # Delete the tenant
    response = client.post(
        "/tenants/1/delete", data={"confirmation": "DELETE"}, follow_redirects=False
    )

    # Should redirect to tenants list
    assert response.status_code == 302

    # Get tenants list
    response = client.get("/tenants")
    assert response.status_code == 200

    # Should not show the deleted tenant
    content = response.text
    assert "To Delete" not in content
    assert "to-delete" not in content


def test_duplicate_slug_validation(client):
    """Test that duplicate slugs are rejected."""
    # Create first tenant
    response = client.post(
        "/tenants/add",
        data={"name": "First Publisher", "slug": "duplicate-slug"},
        follow_redirects=False,
    )
    assert response.status_code == 302

    # Try to create second tenant with same slug
    response = client.post(
        "/tenants/add",
        data={"name": "Second Publisher", "slug": "duplicate-slug"},
        follow_redirects=False,
    )

    # Should return error (not redirect)
    assert response.status_code == 400

    # Should show error message
    content = response.text
    assert "already taken" in content
