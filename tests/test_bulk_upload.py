"""Tests for bulk upload functionality."""

from io import BytesIO


def test_valid_csv_creates_products(client):
    """Test valid CSV creates rows, count matches."""
    # Create tenant and select it
    client.post(
        "/tenants/add",
        data={"name": "Test Publisher", "slug": "test-publisher-bulk"},
        follow_redirects=False,
    )

    client.post("/tenants/select", data={"tenant_id": 1}, follow_redirects=False)

    # Create valid CSV content
    csv_content = """product_id,name,description,delivery_type,is_fixed_price,cpm,is_custom,expires_at,policy_compliance,targeted_ages,verified_minimum_age
bulk-test-1,Product 1,Description 1,guaranteed,true,25.50,false,,Family-friendly,adults,18
bulk-test-2,Product 2,Description 2,non_guaranteed,false,,false,,,teens,
bulk-test-3,Product 3,Description 3,guaranteed,true,30.00,true,2024-12-31T23:59:59Z,Content-safe,children,13"""

    # Upload CSV
    files = {"file": ("test.csv", BytesIO(csv_content.encode()), "text/csv")}
    response = client.post(
        "/tenant/1/products/bulk-upload", files=files, follow_redirects=False
    )

    # Should redirect with success message
    assert response.status_code == 302
    location = response.headers["location"]
    assert (
        "Successfully imported 3 products" in location
        or "Successfully%20imported%203%20products" in location
    )

    # Check products were created
    response = client.get("/tenant/1/products")
    assert response.status_code == 200

    content = response.text
    assert "bulk-test-1" in content
    assert "bulk-test-2" in content
    assert "bulk-test-3" in content
    assert "Product 1" in content
    assert "Product 2" in content
    assert "Product 3" in content


def test_csv_missing_required_column_returns_error(client):
    """Test CSV with missing required column returns 400 with list of missing columns."""
    # Create tenant and select it
    client.post(
        "/tenants/add",
        data={"name": "Test Publisher", "slug": "test-publisher-missing"},
        follow_redirects=False,
    )

    client.post("/tenants/select", data={"tenant_id": 1}, follow_redirects=False)

    # Create CSV with missing required column
    csv_content = """product_id,name,description,delivery_type,cpm,is_custom,expires_at,policy_compliance,targeted_ages,verified_minimum_age
test-1,Product 1,Description 1,guaranteed,25.50,false,,Family-friendly,adults,18"""

    # Upload CSV
    files = {"file": ("test.csv", BytesIO(csv_content.encode()), "text/csv")}
    response = client.post("/tenant/1/products/bulk-upload", files=files)

    # Should return error
    assert response.status_code == 400

    # Should show error message
    content = response.text
    assert "CSV import failed" in content
    assert "Missing required columns" in content
    assert "is_fixed_price" in content


def test_csv_bad_type_returns_row_errors(client):
    """Test CSV with bad type on a row returns 400 with row numbers called out."""
    # Create tenant and select it
    client.post(
        "/tenants/add",
        data={"name": "Test Publisher", "slug": "test-publisher-bad-type"},
        follow_redirects=False,
    )

    client.post("/tenants/select", data={"tenant_id": 1}, follow_redirects=False)

    # Create CSV with bad data types
    csv_content = """product_id,name,description,delivery_type,is_fixed_price,cpm,is_custom,expires_at,policy_compliance,targeted_ages,verified_minimum_age
test-1,Product 1,Description 1,guaranteed,true,not-a-number,false,,Family-friendly,adults,18
test-2,Product 2,Description 2,guaranteed,true,25.50,false,,Family-friendly,adults,not-a-number"""

    # Upload CSV
    files = {"file": ("test.csv", BytesIO(csv_content.encode()), "text/csv")}
    response = client.post("/tenant/1/products/bulk-upload", files=files)

    # Should return error
    assert response.status_code == 400

    # Should show error message
    content = response.text
    assert "CSV import failed" in content
    assert "Row 2" in content  # First data row is row 2 (row 1 is headers)
    assert "Row 3" in content  # Second data row is row 3


def test_csv_invalid_delivery_type_returns_error(client):
    """Test CSV with invalid delivery_type returns error."""
    # Create tenant and select it
    client.post(
        "/tenants/add",
        data={"name": "Test Publisher", "slug": "test-publisher-invalid-delivery"},
        follow_redirects=False,
    )

    client.post("/tenants/select", data={"tenant_id": 1}, follow_redirects=False)

    # Create CSV with invalid delivery_type
    csv_content = """product_id,name,description,delivery_type,is_fixed_price,cpm,is_custom,expires_at,policy_compliance,targeted_ages,verified_minimum_age
test-1,Product 1,Description 1,invalid_type,true,25.50,false,,Family-friendly,adults,18"""

    # Upload CSV
    files = {"file": ("test.csv", BytesIO(csv_content.encode()), "text/csv")}
    response = client.post("/tenant/1/products/bulk-upload", files=files)

    # Should return error
    assert response.status_code == 400

    # Should show error message
    content = response.text
    assert "CSV import failed" in content
    assert "delivery_type" in content
    assert "guaranteed" in content or "non_guaranteed" in content


def test_csv_missing_cpm_for_fixed_price_returns_error(client):
    """Test CSV with missing CPM for fixed price products returns error."""
    # Create tenant and select it
    client.post(
        "/tenants/add",
        data={"name": "Test Publisher", "slug": "test-publisher-missing-cpm"},
        follow_redirects=False,
    )

    client.post("/tenants/select", data={"tenant_id": 1}, follow_redirects=False)

    # Create CSV with missing CPM for fixed price
    csv_content = """product_id,name,description,delivery_type,is_fixed_price,cpm,is_custom,expires_at,policy_compliance,targeted_ages,verified_minimum_age
test-1,Product 1,Description 1,guaranteed,true,,false,,Family-friendly,adults,18"""

    # Upload CSV
    files = {"file": ("test.csv", BytesIO(csv_content.encode()), "text/csv")}
    response = client.post("/tenant/1/products/bulk-upload", files=files)

    # Should return error
    assert response.status_code == 400

    # Should show error message
    content = response.text
    assert "CSV import failed" in content
    assert "cpm" in content
    assert "Required when is_fixed_price is true" in content


def test_csv_no_partial_inserts_on_error(client):
    """Test that no partial inserts occur when any row fails."""
    # Create tenant and select it
    client.post(
        "/tenants/add",
        data={"name": "Test Publisher", "slug": "test-publisher-no-partial"},
        follow_redirects=False,
    )

    client.post("/tenants/select", data={"tenant_id": 1}, follow_redirects=False)

    # Create CSV with one valid row and one invalid row
    csv_content = """product_id,name,description,delivery_type,is_fixed_price,cpm,is_custom,expires_at,policy_compliance,targeted_ages,verified_minimum_age
valid-1,Valid Product,Valid description,guaranteed,true,25.50,false,,Family-friendly,adults,18
invalid-1,Invalid Product,Invalid description,guaranteed,true,,false,,Family-friendly,adults,18"""

    # Upload CSV
    files = {"file": ("test.csv", BytesIO(csv_content.encode()), "text/csv")}
    response = client.post("/tenant/1/products/bulk-upload", files=files)

    # Should return error
    assert response.status_code == 400

    # Check that no products were created (no partial inserts)
    response = client.get("/tenant/1/products")
    assert response.status_code == 200

    content = response.text
    assert "valid-1" not in content
    assert "Valid Product" not in content


def test_csv_upload_wrong_file_type_returns_error(client):
    """Test uploading non-CSV file returns error."""
    # Create tenant and select it
    client.post(
        "/tenants/add",
        data={"name": "Test Publisher", "slug": "test-publisher-wrong-file"},
        follow_redirects=False,
    )

    client.post("/tenants/select", data={"tenant_id": 1}, follow_redirects=False)

    # Upload non-CSV file
    files = {"file": ("test.txt", BytesIO(b"not a csv file"), "text/plain")}
    response = client.post("/tenant/1/products/bulk-upload", files=files)

    # Should return error
    assert response.status_code == 400

    # Should show error message
    content = response.text
    assert "Please upload a CSV file" in content
