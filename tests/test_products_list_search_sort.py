"""Tests for product list search, sort, and pagination functionality."""


def test_product_search_functionality(client):
    """Test search by term returns expected rows."""
    # Create tenant and select it
    client.post(
        "/tenants/add",
        data={"name": "Test Publisher", "slug": "test-publisher-search"},
        follow_redirects=False,
    )

    client.post("/tenants/select", data={"tenant_id": 1}, follow_redirects=False)

    # Create multiple products with different names
    products_data = [
        {
            "product_id": "search-test-1",
            "name": "Premium Display Ad",
            "description": "High-quality display advertising",
            "delivery_type": "guaranteed",
            "is_fixed_price": "true",
            "cpm": "25.00",
        },
        {
            "product_id": "search-test-2",
            "name": "Video Streaming Ad",
            "description": "Video advertising for streaming platforms",
            "delivery_type": "guaranteed",
            "is_fixed_price": "true",
            "cpm": "35.00",
        },
        {
            "product_id": "search-test-3",
            "name": "Mobile Banner Ad",
            "description": "Mobile banner advertising",
            "delivery_type": "non_guaranteed",
            "is_fixed_price": "false",
        },
    ]

    for product_data in products_data:
        client.post("/tenant/1/products/add", data=product_data, follow_redirects=False)

    # Search for "video" - should find Video Streaming Ad
    response = client.get("/tenant/1/products?q=video")
    assert response.status_code == 200

    content = response.text
    assert "Video Streaming Ad" in content
    assert "Premium Display Ad" not in content
    assert "Mobile Banner Ad" not in content

    # Search for "mobile" - should find Mobile Banner Ad
    response = client.get("/tenant/1/products?q=mobile")
    assert response.status_code == 200

    content = response.text
    assert "Mobile Banner Ad" in content
    assert "Premium Display Ad" not in content
    assert "Video Streaming Ad" not in content

    # Search for "advertising" - should find all (in descriptions)
    response = client.get("/tenant/1/products?q=advertising")
    assert response.status_code == 200

    content = response.text
    assert "Premium Display Ad" in content
    assert "Video Streaming Ad" in content
    assert "Mobile Banner Ad" in content


def test_product_sort_functionality(client):
    """Test sort by different fields works correctly."""
    # Create tenant and select it
    client.post(
        "/tenants/add",
        data={"name": "Test Publisher", "slug": "test-publisher-sort"},
        follow_redirects=False,
    )

    client.post("/tenants/select", data={"tenant_id": 1}, follow_redirects=False)

    # Create products with different names for sorting
    products_data = [
        {
            "product_id": "sort-z",
            "name": "Zebra Product",
            "description": "Last alphabetically",
            "delivery_type": "guaranteed",
            "is_fixed_price": "true",
            "cpm": "10.00",
        },
        {
            "product_id": "sort-a",
            "name": "Alpha Product",
            "description": "First alphabetically",
            "delivery_type": "guaranteed",
            "is_fixed_price": "true",
            "cpm": "20.00",
        },
        {
            "product_id": "sort-m",
            "name": "Middle Product",
            "description": "Middle alphabetically",
            "delivery_type": "non_guaranteed",
            "is_fixed_price": "false",
        },
    ]

    for product_data in products_data:
        client.post("/tenant/1/products/add", data=product_data, follow_redirects=False)

    # Sort by name ascending (default)
    response = client.get("/tenant/1/products?sort=name&order=asc")
    assert response.status_code == 200

    content = response.text
    # Check order: Alpha, Middle, Zebra
    alpha_pos = content.find("Alpha Product")
    middle_pos = content.find("Middle Product")
    zebra_pos = content.find("Zebra Product")

    assert alpha_pos < middle_pos < zebra_pos

    # Sort by name descending
    response = client.get("/tenant/1/products?sort=name&order=desc")
    assert response.status_code == 200

    content = response.text
    # Check order: Zebra, Middle, Alpha
    alpha_pos = content.find("Alpha Product")
    middle_pos = content.find("Middle Product")
    zebra_pos = content.find("Zebra Product")

    assert zebra_pos < middle_pos < alpha_pos

    # Sort by CPM ascending
    response = client.get("/tenant/1/products?sort=cpm&order=asc")
    assert response.status_code == 200

    content = response.text
    # Check order: $10.00, $20.00, then non-guaranteed (no CPM)
    assert "$10.00" in content
    assert "$20.00" in content


def test_product_pagination_functionality(client):
    """Test pagination returns correct counts per page."""
    # Create tenant and select it
    client.post(
        "/tenants/add",
        data={"name": "Test Publisher", "slug": "test-publisher-pagination"},
        follow_redirects=False,
    )

    client.post("/tenants/select", data={"tenant_id": 1}, follow_redirects=False)

    # Create 5 products
    for i in range(1, 6):
        client.post(
            "/tenant/1/products/add",
            data={
                "product_id": f"page-test-{i}",
                "name": f"Product {i}",
                "description": f"Product {i} description",
                "delivery_type": "guaranteed",
                "is_fixed_price": "true",
                "cpm": str(i * 10.0),
            },
            follow_redirects=False,
        )

    # Test page 1 with size 2
    response = client.get("/tenant/1/products?page=1&size=2")
    assert response.status_code == 200

    content = response.text
    # Should show "Showing 1 to 2 of 5 products"
    assert "Showing 1 to 2 of 5 products" in content

    # Should have Next button (but not Previous on first page)
    assert "Next" in content
    assert "Previous" not in content

    # Test page 2 with size 2
    response = client.get("/tenant/1/products?page=2&size=2")
    assert response.status_code == 200

    content = response.text
    # Should show "Showing 3 to 4 of 5 products"
    assert "Showing 3 to 4 of 5 products" in content

    # Test page 3 with size 2 (last page)
    response = client.get("/tenant/1/products?page=3&size=2")
    assert response.status_code == 200

    content = response.text
    # Should show "Showing 5 to 5 of 5 products"
    assert "Showing 5 to 5 of 5 products" in content

    # Should not have Next button on last page
    assert "Next" not in content


def test_product_sort_delivery_type(client):
    """Test sorting by delivery_type field."""
    # Create tenant and select it
    client.post(
        "/tenants/add",
        data={"name": "Test Publisher", "slug": "test-publisher-delivery-sort"},
        follow_redirects=False,
    )

    client.post("/tenants/select", data={"tenant_id": 1}, follow_redirects=False)

    # Create products with different delivery types
    products_data = [
        {
            "product_id": "delivery-non",
            "name": "Non-Guaranteed Product",
            "description": "Non-guaranteed delivery",
            "delivery_type": "non_guaranteed",
            "is_fixed_price": "false",
        },
        {
            "product_id": "delivery-guar",
            "name": "Guaranteed Product",
            "description": "Guaranteed delivery",
            "delivery_type": "guaranteed",
            "is_fixed_price": "true",
            "cpm": "25.00",
        },
    ]

    for product_data in products_data:
        client.post("/tenant/1/products/add", data=product_data, follow_redirects=False)

    # Sort by delivery_type ascending
    response = client.get("/tenant/1/products?sort=delivery_type&order=asc")
    assert response.status_code == 200

    content = response.text
    # Check order: guaranteed comes before non_guaranteed alphabetically
    guar_pos = content.find("Guaranteed Product")
    non_pos = content.find("Non-Guaranteed Product")

    assert guar_pos < non_pos
