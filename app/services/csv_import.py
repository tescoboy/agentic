"""CSV import service for Product model with validation and error reporting."""

import csv
from datetime import datetime
from io import StringIO
from typing import Dict, List, Tuple, Union

from ..models.product import Product
from .csv_template import get_product_csv_headers


class CSVImportError(Exception):
    """Exception raised when CSV import fails."""

    pass


class RowError:
    """Represents an error in a specific CSV row."""

    def __init__(self, row_number: int, field: str, message: str):
        self.row_number = row_number
        self.field = field
        self.message = message

    def to_dict(self) -> Dict[str, Union[int, str]]:
        """Convert to dictionary for JSON response."""
        return {"row": self.row_number, "field": self.field, "message": self.message}


def validate_csv_headers(headers: List[str]) -> List[str]:
    """Validate CSV headers against expected template.

    Args:
        headers: List of header strings from CSV

    Returns:
        List of missing or extra columns

    Raises:
        CSVImportError: If headers don't match template
    """
    expected_headers = get_product_csv_headers()
    missing_headers = set(expected_headers) - set(headers)
    extra_headers = set(headers) - set(expected_headers)

    errors = []
    if missing_headers:
        errors.append(f"Missing required columns: {', '.join(sorted(missing_headers))}")
    if extra_headers:
        errors.append(f"Unexpected columns: {', '.join(sorted(extra_headers))}")

    if errors:
        raise CSVImportError("; ".join(errors))

    return []


def validate_product_row(row: Dict[str, str], row_number: int) -> List[RowError]:
    """Validate a single product row and return any errors.

    Args:
        row: Dictionary of field values for the row
        row_number: 1-based row number for error reporting

    Returns:
        List of RowError objects (empty if no errors)
    """
    errors = []

    # Required fields
    if not row.get("product_id", "").strip():
        errors.append(
            RowError(row_number, "product_id", "Required field cannot be empty")
        )

    if not row.get("name", "").strip():
        errors.append(RowError(row_number, "name", "Required field cannot be empty"))

    if not row.get("description", "").strip():
        errors.append(
            RowError(row_number, "description", "Required field cannot be empty")
        )

    # Validate delivery_type
    delivery_type = row.get("delivery_type", "").strip().lower()
    if delivery_type not in ["guaranteed", "non_guaranteed"]:
        errors.append(
            RowError(
                row_number, "delivery_type", "Must be 'guaranteed' or 'non_guaranteed'"
            )
        )

    # Validate is_fixed_price
    is_fixed_price_str = row.get("is_fixed_price", "").strip().lower()
    if is_fixed_price_str not in ["true", "false"]:
        errors.append(
            RowError(row_number, "is_fixed_price", "Must be 'true' or 'false'")
        )

    # Validate cpm if is_fixed_price is true
    if is_fixed_price_str == "true":
        cpm_str = row.get("cpm", "").strip()
        if not cpm_str:
            errors.append(
                RowError(row_number, "cpm", "Required when is_fixed_price is true")
            )
        else:
            try:
                cpm = float(cpm_str)
                if cpm <= 0:
                    errors.append(RowError(row_number, "cpm", "Must be greater than 0"))
            except ValueError:
                errors.append(RowError(row_number, "cpm", "Must be a valid number"))

    # Validate is_custom
    is_custom_str = row.get("is_custom", "").strip().lower()
    if is_custom_str and is_custom_str not in ["true", "false"]:
        errors.append(RowError(row_number, "is_custom", "Must be 'true' or 'false'"))

    # Validate expires_at if provided
    expires_at_str = row.get("expires_at", "").strip()
    if expires_at_str:
        try:
            datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
        except ValueError:
            errors.append(
                RowError(row_number, "expires_at", "Must be a valid ISO datetime")
            )

    # Validate targeted_ages if provided
    targeted_ages = row.get("targeted_ages", "").strip().lower()
    if targeted_ages and targeted_ages not in ["children", "teens", "adults"]:
        errors.append(
            RowError(
                row_number, "targeted_ages", "Must be 'children', 'teens', or 'adults'"
            )
        )

    # Validate verified_minimum_age if provided
    min_age_str = row.get("verified_minimum_age", "").strip()
    if min_age_str:
        try:
            min_age = int(min_age_str)
            if min_age < 0:
                errors.append(
                    RowError(row_number, "verified_minimum_age", "Must be 0 or greater")
                )
        except ValueError:
            errors.append(
                RowError(row_number, "verified_minimum_age", "Must be a valid integer")
            )

    return errors


def parse_product_row(row: Dict[str, str]) -> Product:
    """Parse a validated CSV row into a Product object.

    Args:
        row: Dictionary of field values for the row

    Returns:
        Product object (tenant_id must be set separately)
    """
    # Parse boolean fields
    is_fixed_price = row.get("is_fixed_price", "").strip().lower() == "true"
    is_custom = row.get("is_custom", "").strip().lower() == "true"

    # Parse numeric fields
    cpm = None
    if row.get("cpm", "").strip():
        cpm = float(row["cpm"])

    verified_minimum_age = None
    if row.get("verified_minimum_age", "").strip():
        verified_minimum_age = int(row["verified_minimum_age"])

    # Parse datetime field
    expires_at = None
    if row.get("expires_at", "").strip():
        expires_at = datetime.fromisoformat(row["expires_at"].replace("Z", "+00:00"))

    return Product(
        product_id=row["product_id"].strip(),
        name=row["name"].strip(),
        description=row["description"].strip(),
        delivery_type=row["delivery_type"].strip().lower(),
        is_fixed_price=is_fixed_price,
        cpm=cpm,
        is_custom=is_custom,
        expires_at=expires_at,
        policy_compliance=row.get("policy_compliance", "").strip() or None,
        targeted_ages=row.get("targeted_ages", "").strip().lower() or None,
        verified_minimum_age=verified_minimum_age,
    )


def parse_csv_content(
    csv_content: str, tenant_id: int
) -> Tuple[List[Product], List[RowError]]:
    """Parse CSV content and validate all rows.

    Args:
        csv_content: CSV file content as string
        tenant_id: Tenant ID to assign to all products

    Returns:
        Tuple of (valid_products, errors)

    Note:
        If any row has errors, no products are returned (no partial imports)
    """
    errors = []
    products = []

    try:
        # Parse CSV
        csv_file = StringIO(csv_content)
        reader = csv.DictReader(csv_file)

        # Validate headers
        try:
            validate_csv_headers(reader.fieldnames or [])
        except CSVImportError as e:
            return [], [RowError(0, "headers", str(e))]

        # Process each row
        for row_number, row in enumerate(reader, start=2):  # Start at 2 (1 is headers)
            # Validate row
            row_errors = validate_product_row(row, row_number)
            if row_errors:
                errors.extend(row_errors)
                continue

            # Parse row
            try:
                product = parse_product_row(row)
                product.tenant_id = tenant_id
                products.append(product)
            except Exception as e:
                errors.append(
                    RowError(row_number, "general", f"Failed to parse row: {str(e)}")
                )

        # If any errors, return no products (no partial imports)
        if errors:
            return [], errors

        return products, []

    except Exception as e:
        return [], [RowError(0, "general", f"Failed to parse CSV: {str(e)}")]
