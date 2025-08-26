"""Tests for bulk delete functionality."""


def test_bulk_delete_products_with_confirmation(client):
    """Test bulk delete with confirmation token removes all for the tenant."""
    # Create tenant and select it
    client.post(
        "/tenants/add",
        data={"name": "Test Publisher", "slug": "test-publisher-bulk-delete"},
        follow_redirects=False,
    )

    client.post("/tenants/select", data={"tenant_id": 1}, follow_redirects=False)

    # Create several products
    products_data = [
        {
            "product_id": "bulk-delete-1",
            "name": "Product 1",
            "description": "First product to delete",
            "delivery_type": "guaranteed",
            "is_fixed_price": "true",
            "cpm": "25.00",
        },
        {
            "product_id": "bulk-delete-2",
            "name": "Product 2",
            "description": "Second product to delete",
            "delivery_type": "non_guaranteed",
            "is_fixed_price": "false",
        },
        {
            "product_id": "bulk-delete-3",
            "name": "Product 3",
            "description": "Third product to delete",
            "delivery_type": "guaranteed",
            "is_fixed_price": "true",
            "cpm": "30.00",
        },
    ]

    for product_data in products_data:
        client.post("/tenant/1/products/add", data=product_data, follow_redirects=False)

    # Verify products exist
    response = client.get("/tenant/1/products")
    assert response.status_code == 200

    content = response.text
    assert "bulk-delete-1" in content
    assert "bulk-delete-2" in content
    assert "bulk-delete-3" in content

    # Get bulk delete confirmation page
    response = client.get("/tenant/1/products/bulk-delete")
    assert response.status_code == 200

    content = response.text
    assert "Bulk Delete Products" in content
    assert "3 products" in content  # Should show correct count

    # Perform bulk delete with confirmation
    response = client.post(
        "/tenant/1/products/bulk-delete",
        data={"confirmation": "DELETE"},
        follow_redirects=False,
    )

    # Should redirect with success message
    assert response.status_code == 302
    location = response.headers["location"]
    assert (
        "Successfully deleted 3 products" in location
        or "Successfully%20deleted%203%20products" in location
    )

    # Verify all products are deleted
    response = client.get("/tenant/1/products")
    assert response.status_code == 200

    content = response.text
    assert "bulk-delete-1" not in content
    assert "bulk-delete-2" not in content
    assert "bulk-delete-3" not in content
    assert "Product 1" not in content
    assert "Product 2" not in content
    assert "Product 3" not in content


def test_bulk_delete_without_confirmation_returns_error(client):
    """Test bulk delete without proper confirmation returns error."""
    # Create tenant and select it
    client.post(
        "/tenants/add",
        data={"name": "Test Publisher", "slug": "test-publisher-no-confirm"},
        follow_redirects=False,
    )

    client.post("/tenants/select", data={"tenant_id": 1}, follow_redirects=False)

    # Create a product
    client.post(
        "/tenant/1/products/add",
        data={
            "product_id": "no-confirm-test",
            "name": "Product to keep",
            "description": "This should not be deleted",
            "delivery_type": "guaranteed",
            "is_fixed_price": "true",
            "cpm": "25.00",
        },
        follow_redirects=False,
    )

    # Try bulk delete without confirmation
    response = client.post(
        "/tenant/1/products/bulk-delete", data={"confirmation": "WRONG"}
    )

    # Should return error
    assert response.status_code == 400

    # Should show error message
    content = response.text
    assert (
        "Please type 'DELETE' to confirm" in content
        or "Please type DELETE to confirm" in content
        or "Please type &#39;DELETE&#39; to confirm" in content
    )

    # Verify product still exists
    response = client.get("/tenant/1/products")
    assert response.status_code == 200

    content = response.text
    assert "no-confirm-test" in content
    assert "Product to keep" in content


def test_bulk_delete_empty_confirmation_returns_error(client):
    """Test bulk delete with empty confirmation returns error."""
    # Create tenant and select it
    client.post(
        "/tenants/add",
        data={"name": "Test Publisher", "slug": "test-publisher-empty-confirm"},
        follow_redirects=False,
    )

    client.post("/tenants/select", data={"tenant_id": 1}, follow_redirects=False)

    # Create a product
    client.post(
        "/tenant/1/products/add",
        data={
            "product_id": "empty-confirm-test",
            "name": "Product to keep",
            "description": "This should not be deleted",
            "delivery_type": "guaranteed",
            "is_fixed_price": "true",
            "cpm": "25.00",
        },
        follow_redirects=False,
    )

    # Try bulk delete with empty confirmation
    response = client.post("/tenant/1/products/bulk-delete", data={"confirmation": ""})

    # Should return error
    assert response.status_code == 400

    # Should show error message
    content = response.text
    assert (
        "Please type 'DELETE' to confirm" in content
        or "Please type DELETE to confirm" in content
        or "Please type &#39;DELETE&#39; to confirm" in content
    )

    # Verify product still exists
    response = client.get("/tenant/1/products")
    assert response.status_code == 200

    content = response.text
    assert "empty-confirm-test" in content


def test_bulk_delete_no_products_shows_zero_count(client):
    """Test bulk delete page shows zero count when no products exist."""
    # Create tenant and select it
    client.post(
        "/tenants/add",
        data={"name": "Test Publisher", "slug": "test-publisher-zero"},
        follow_redirects=False,
    )

    client.post("/tenants/select", data={"tenant_id": 1}, follow_redirects=False)

    # Get bulk delete confirmation page (no products created)
    response = client.get("/tenant/1/products/bulk-delete")
    assert response.status_code == 200

    content = response.text
    assert "Bulk Delete Products" in content
    assert "0 products" in content  # Should show zero count


def test_bulk_delete_tenant_access_validation(client):
    """Test that bulk delete only works for the active tenant."""
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
    client.post("/tenants/select", data={"tenant_id": 1}, follow_redirects=False)

    # Create product for first tenant
    client.post(
        "/tenant/1/products/add",
        data={
            "product_id": "tenant-1-product",
            "name": "Tenant 1 Product",
            "description": "Product for tenant 1",
            "delivery_type": "guaranteed",
            "is_fixed_price": "true",
            "cpm": "25.00",
        },
        follow_redirects=False,
    )

    # Try to access bulk delete for second tenant (should fail)
    response = client.get("/tenant/2/products/bulk-delete")
    assert response.status_code == 400

    # Should show tenant mismatch error
    content = response.text
    assert "Tenant mismatch" in content
    assert "Please select tenant" in content
