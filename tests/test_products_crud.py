"""Tests for product CRUD operations."""


def test_create_product_via_post(client):
    """Test create product via POST then list shows it."""
    # First create a tenant
    client.post(
        "/tenants/add",
        data={"name": "Test Publisher", "slug": "test-publisher-crud"},
        follow_redirects=False,
    )

    # Select the tenant
    client.post("/tenants/select", data={"tenant_id": 1}, follow_redirects=False)

    # Create product
    response = client.post(
        "/tenant/1/products/add",
        data={
            "product_id": "test-product-001",
            "name": "Test Product",
            "description": "A test product for CRUD testing",
            "delivery_type": "guaranteed",
            "is_fixed_price": "true",
            "cpm": "25.50",
            "is_custom": "false",
            "policy_compliance": "Family-friendly content",
            "targeted_ages": "adults",
            "verified_minimum_age": "18",
        },
        follow_redirects=False,
    )

    # Should redirect to products list
    assert response.status_code == 302
    assert response.headers["location"] == "/tenant/1/products"

    # Get products list
    response = client.get("/tenant/1/products")
    assert response.status_code == 200

    # Should show the created product
    content = response.text
    assert "test-product-001" in content
    assert "Test Product" in content
    assert "A test product for CRUD testing" in content
    assert "guaranteed" in content
    assert "$25.50" in content


def test_edit_product_via_post(client):
    """Test edit product via POST then list reflects changes."""
    # First create a tenant and product
    client.post(
        "/tenants/add",
        data={"name": "Test Publisher", "slug": "test-publisher-edit"},
        follow_redirects=False,
    )

    client.post("/tenants/select", data={"tenant_id": 1}, follow_redirects=False)

    client.post(
        "/tenant/1/products/add",
        data={
            "product_id": "test-product-edit",
            "name": "Original Name",
            "description": "Original description",
            "delivery_type": "guaranteed",
            "is_fixed_price": "true",
            "cpm": "10.00",
        },
        follow_redirects=False,
    )

    # Get the edit form
    response = client.get("/tenant/1/products/1/edit")
    assert response.status_code == 200

    # Edit the product
    response = client.post(
        "/tenant/1/products/1/edit",
        data={
            "name": "Updated Name",
            "description": "Updated description",
            "delivery_type": "non_guaranteed",
            "is_fixed_price": "false",
            "cpm": "",
            "is_custom": "false",
            "policy_compliance": "",
            "targeted_ages": "",
            "verified_minimum_age": "",
        },
        follow_redirects=False,
    )

    # Should redirect to products list
    assert response.status_code == 302

    # Get products list
    response = client.get("/tenant/1/products")
    assert response.status_code == 200

    # Should show updated values
    content = response.text
    assert "Updated Name" in content
    assert "Updated description" in content
    assert "non_guaranteed" in content
    assert "Original Name" not in content


def test_delete_product_via_post(client):
    """Test delete product via POST then list no longer shows it."""
    # First create a tenant and product
    client.post(
        "/tenants/add",
        data={"name": "Test Publisher", "slug": "test-publisher-delete"},
        follow_redirects=False,
    )

    client.post("/tenants/select", data={"tenant_id": 1}, follow_redirects=False)

    client.post(
        "/tenant/1/products/add",
        data={
            "product_id": "test-product-delete",
            "name": "To Delete",
            "description": "This will be deleted",
            "delivery_type": "guaranteed",
            "is_fixed_price": "true",
            "cpm": "15.00",
        },
        follow_redirects=False,
    )

    # Delete the product
    response = client.post("/tenant/1/products/1/delete", follow_redirects=False)

    # Should redirect to products list
    assert response.status_code == 302

    # Get products list
    response = client.get("/tenant/1/products")
    assert response.status_code == 200

    # Should not show the deleted product
    content = response.text
    assert "To Delete" not in content
    assert "test-product-delete" not in content


def test_duplicate_product_id_validation(client):
    """Test that duplicate product IDs are rejected."""
    # First create a tenant
    client.post(
        "/tenants/add",
        data={"name": "Test Publisher", "slug": "test-publisher-duplicate"},
        follow_redirects=False,
    )

    client.post("/tenants/select", data={"tenant_id": 1}, follow_redirects=False)

    # Create first product
    response = client.post(
        "/tenant/1/products/add",
        data={
            "product_id": "duplicate-id",
            "name": "First Product",
            "description": "First product description",
            "delivery_type": "guaranteed",
            "is_fixed_price": "true",
            "cpm": "20.00",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302

    # Try to create second product with same product_id
    response = client.post(
        "/tenant/1/products/add",
        data={
            "product_id": "duplicate-id",
            "name": "Second Product",
            "description": "Second product description",
            "delivery_type": "guaranteed",
            "is_fixed_price": "true",
            "cpm": "25.00",
        },
        follow_redirects=False,
    )

    # Should return error (not redirect)
    assert response.status_code == 400

    # Should show error message
    content = response.text
    assert "already exists" in content


def test_tenant_access_validation(client):
    """Test that users can only access products for the active tenant."""
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
            "cpm": "30.00",
        },
        follow_redirects=False,
    )

    # Try to access products for second tenant (should fail)
    response = client.get("/tenant/2/products")
    assert response.status_code == 400

    # Should show tenant mismatch error
    content = response.text
    assert "Tenant mismatch" in content
    assert "Please select tenant" in content
