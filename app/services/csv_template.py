"""CSV template generation service for Product model.

Based on AdCP Product specification from:
- reference/adcp/docs/media-buy/media-products.md
- reference/salesagent/src/core/schemas.py (lines 150-210)
"""

import csv
from io import StringIO
from typing import List


def get_product_csv_headers() -> List[str]:
    """Get CSV headers for Product model export.

    Headers are based on AdCP Product specification fields that are suitable for CSV export.
    Complex nested objects (formats, price_guidance, implementation_config) are excluded
    as they require JSON serialization and are not suitable for direct CSV export.

    Returns:
        List of CSV header strings
    """
    return [
        "product_id",  # Required: Unique product identifier
        "name",  # Required: Product name
        "description",  # Required: Product description
        "delivery_type",  # Required: "guaranteed" or "non_guaranteed"
        "is_fixed_price",  # Required: true/false
        "cpm",  # Optional: Cost per mille (required if is_fixed_price=true)
        "is_custom",  # Optional: Whether this is a custom product
        "expires_at",  # Optional: Product expiration date (ISO format)
        "policy_compliance",  # Optional: Policy compliance information
        "targeted_ages",  # Optional: "children", "teens", or "adults"
        "verified_minimum_age",  # Optional: Minimum age requirement
    ]


def generate_csv_template() -> str:
    """Generate a CSV template with headers and example row.

    Returns:
        CSV string with headers and one example row
    """
    headers = get_product_csv_headers()

    # Create example row with sample data
    example_row = [
        "example_product_001",  # product_id
        "Example Product",  # name
        "This is an example product description",  # description
        "guaranteed",  # delivery_type
        "true",  # is_fixed_price
        "25.50",  # cpm
        "false",  # is_custom
        "",  # expires_at (empty for non-custom)
        "Family-friendly content",  # policy_compliance
        "adults",  # targeted_ages
        "18",  # verified_minimum_age
    ]

    # Create CSV string
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerow(example_row)

    return output.getvalue()
