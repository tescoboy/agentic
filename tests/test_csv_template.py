"""Tests for CSV template functionality."""

from app.services.csv_template import generate_csv_template, get_product_csv_headers


def test_csv_template_headers_match_product_model():
    """Test that CSV headers match Product model exportable fields."""
    headers = get_product_csv_headers()

    # Check required fields are present
    required_fields = [
        "product_id",
        "name",
        "description",
        "delivery_type",
        "is_fixed_price",
    ]
    for field in required_fields:
        assert field in headers, f"Required field '{field}' missing from CSV headers"

    # Check optional fields are present
    optional_fields = [
        "cpm",
        "is_custom",
        "expires_at",
        "policy_compliance",
        "targeted_ages",
        "verified_minimum_age",
    ]
    for field in optional_fields:
        assert field in headers, f"Optional field '{field}' missing from CSV headers"

    # Check no unexpected fields
    expected_fields = required_fields + optional_fields
    for field in headers:
        assert field in expected_fields, f"Unexpected field '{field}' in CSV headers"


def test_csv_template_generation():
    """Test that CSV template generates correctly formatted content."""
    csv_content = generate_csv_template()

    # Should contain headers
    assert "product_id,name,description,delivery_type,is_fixed_price" in csv_content

    # Should contain example row
    assert "example_product_001" in csv_content
    assert "Example Product" in csv_content
    assert "guaranteed" in csv_content
    assert "true" in csv_content
    assert "25.50" in csv_content

    # Should be valid CSV format (comma-separated)
    lines = csv_content.strip().split("\n")
    assert len(lines) >= 2, "CSV should have at least header and one data row"

    # Check header line has correct number of fields
    header_fields = lines[0].split(",")
    assert len(header_fields) == 11, f"Expected 11 fields, got {len(header_fields)}"

    # Check data line has same number of fields
    data_fields = lines[1].split(",")
    assert len(data_fields) == 11, f"Expected 11 fields, got {len(data_fields)}"


def test_csv_template_download_endpoint(client):
    """Test GET template.csv returns headers that match Product model exportable fields."""
    # Create tenant
    client.post(
        "/tenants/add",
        data={"name": "Test Publisher", "slug": "test-publisher-template"},
        follow_redirects=False,
    )

    # Download template
    response = client.get("/tenant/1/products/template.csv")
    assert response.status_code == 200

    # Check content type
    assert "text/csv" in response.headers["content-type"]

    # Check content disposition
    assert "attachment" in response.headers["content-disposition"]
    assert (
        "products_template_test-publisher-template.csv"
        in response.headers["content-disposition"]
    )

    # Check content
    csv_content = response.text
    assert "product_id,name,description,delivery_type,is_fixed_price" in csv_content

    # Should contain example data
    assert "example_product_001" in csv_content
    assert "Example Product" in csv_content


def test_csv_template_download_tenant_not_found(client):
    """Test template download fails for non-existent tenant."""
    response = client.get("/tenant/999/products/template.csv")
    assert response.status_code == 404
