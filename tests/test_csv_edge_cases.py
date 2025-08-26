"""Tests for CSV import edge cases and validation."""

import pytest
from unittest.mock import patch, MagicMock
from fastapi import UploadFile
from io import BytesIO

from app.routes.products.csv import bulk_upload_products


class TestCSVEdgeCases:
    """Test CSV import edge cases and validation."""

    @pytest.mark.asyncio
    async def test_missing_required_headers(self):
        """Test CSV with missing required headers returns 400 with list of missing columns."""
        # Create CSV content with missing required headers
        csv_content = "name,description\nProduct 1,Test product"
        csv_file = UploadFile(
            filename="test.csv",
            file=BytesIO(csv_content.encode()),
            content_type="text/csv",
        )

        # Mock request and dependencies
        mock_request = MagicMock()
        mock_tenant_repo = MagicMock()
        mock_product_repo = MagicMock()

        # Mock tenant
        mock_tenant = MagicMock(id=1, name="Test Publisher")
        mock_tenant_repo.get_by_id.return_value = mock_tenant

        # Call function
        with pytest.raises(Exception) as exc_info:
            await bulk_upload_products(
                request=mock_request,
                tenant_id=1,
                file=csv_file,
                tenant_repo=mock_tenant_repo,
                product_repo=mock_product_repo,
            )

        # Verify error message contains missing headers
        error_message = str(exc_info.value)
        assert "product_id" in error_message.lower()
        assert "missing" in error_message.lower()

    @pytest.mark.asyncio
    async def test_extra_unknown_headers(self):
        """Test CSV with extra unknown headers returns 400 listing extras."""
        # Create CSV content with extra unknown headers
        csv_content = "product_id,name,description,unknown_column,another_unknown\nprod_1,Product 1,Test product,value1,value2"
        csv_file = UploadFile(
            filename="test.csv",
            file=BytesIO(csv_content.encode()),
            content_type="text/csv",
        )

        # Mock request and dependencies
        mock_request = MagicMock()
        mock_tenant_repo = MagicMock()
        mock_product_repo = MagicMock()

        # Mock tenant
        mock_tenant = MagicMock(id=1, name="Test Publisher")
        mock_tenant_repo.get_by_id.return_value = mock_tenant

        # Call function
        with pytest.raises(Exception) as exc_info:
            await bulk_upload_products(
                request=mock_request,
                tenant_id=1,
                file=csv_file,
                tenant_repo=mock_tenant_repo,
                product_repo=mock_product_repo,
            )

        # Verify error message contains unknown headers
        error_message = str(exc_info.value)
        assert "unknown_column" in error_message.lower()
        assert "another_unknown" in error_message.lower()
        assert "unknown" in error_message.lower()

    @pytest.mark.asyncio
    async def test_empty_csv_file(self):
        """Test empty CSV file returns 400 with guidance."""
        # Create empty CSV content
        csv_content = ""
        csv_file = UploadFile(
            filename="test.csv",
            file=BytesIO(csv_content.encode()),
            content_type="text/csv",
        )

        # Mock request and dependencies
        mock_request = MagicMock()
        mock_tenant_repo = MagicMock()
        mock_product_repo = MagicMock()

        # Mock tenant
        mock_tenant = MagicMock(id=1, name="Test Publisher")
        mock_tenant_repo.get_by_id.return_value = mock_tenant

        # Call function
        with pytest.raises(Exception) as exc_info:
            await bulk_upload_products(
                request=mock_request,
                tenant_id=1,
                file=csv_file,
                tenant_repo=mock_tenant_repo,
                product_repo=mock_product_repo,
            )

        # Verify error message contains guidance
        error_message = str(exc_info.value)
        assert "empty" in error_message.lower() or "no data" in error_message.lower()

    @pytest.mark.asyncio
    async def test_csv_with_only_headers(self):
        """Test CSV with only headers (no data rows) returns 400."""
        # Create CSV content with only headers
        csv_content = "product_id,name,description"
        csv_file = UploadFile(
            filename="test.csv",
            file=BytesIO(csv_content.encode()),
            content_type="text/csv",
        )

        # Mock request and dependencies
        mock_request = MagicMock()
        mock_tenant_repo = MagicMock()
        mock_product_repo = MagicMock()

        # Mock tenant
        mock_tenant = MagicMock(id=1, name="Test Publisher")
        mock_tenant_repo.get_by_id.return_value = mock_tenant

        # Call function
        with pytest.raises(Exception) as exc_info:
            await bulk_upload_products(
                request=mock_request,
                tenant_id=1,
                file=csv_file,
                tenant_repo=mock_tenant_repo,
                product_repo=mock_product_repo,
            )

        # Verify error message
        error_message = str(exc_info.value)
        assert "no data" in error_message.lower() or "empty" in error_message.lower()

    @pytest.mark.asyncio
    async def test_mixed_valid_and_invalid_rows_no_partial_inserts(self):
        """Test CSV with mixed valid and invalid rows returns 400 and no partial inserts."""
        # Create CSV content with mixed valid and invalid rows
        csv_content = """product_id,name,description
prod_1,Product 1,Valid product
prod_2,,Invalid product with missing name
prod_3,Product 3,Another valid product
,Invalid product with missing ID,Test description"""
        csv_file = UploadFile(
            filename="test.csv",
            file=BytesIO(csv_content.encode()),
            content_type="text/csv",
        )

        # Mock request and dependencies
        mock_request = MagicMock()
        mock_tenant_repo = MagicMock()
        mock_product_repo = MagicMock()

        # Mock tenant
        mock_tenant = MagicMock(id=1, name="Test Publisher")
        mock_tenant_repo.get_by_id.return_value = mock_tenant

        # Call function
        with pytest.raises(Exception) as exc_info:
            await bulk_upload_products(
                request=mock_request,
                tenant_id=1,
                file=csv_file,
                tenant_repo=mock_tenant_repo,
                product_repo=mock_product_repo,
            )

        # Verify error message contains validation errors
        error_message = str(exc_info.value)
        assert (
            "validation" in error_message.lower() or "invalid" in error_message.lower()
        )

        # Verify no products were created (no partial inserts)
        mock_product_repo.bulk_create.assert_not_called()

    @pytest.mark.asyncio
    async def test_csv_with_duplicate_product_ids(self):
        """Test CSV with duplicate product IDs returns 400."""
        # Create CSV content with duplicate product IDs
        csv_content = """product_id,name,description
prod_1,Product 1,First product
prod_2,Product 2,Second product
prod_1,Product 3,Duplicate product ID
prod_4,Product 4,Fourth product"""
        csv_file = UploadFile(
            filename="test.csv",
            file=BytesIO(csv_content.encode()),
            content_type="text/csv",
        )

        # Mock request and dependencies
        mock_request = MagicMock()
        mock_tenant_repo = MagicMock()
        mock_product_repo = MagicMock()

        # Mock tenant
        mock_tenant = MagicMock(id=1, name="Test Publisher")
        mock_tenant_repo.get_by_id.return_value = mock_tenant

        # Call function
        with pytest.raises(Exception) as exc_info:
            await bulk_upload_products(
                request=mock_request,
                tenant_id=1,
                file=csv_file,
                tenant_repo=mock_tenant_repo,
                product_repo=mock_product_repo,
            )

        # Verify error message contains duplicate information
        error_message = str(exc_info.value)
        assert "duplicate" in error_message.lower() or "prod_1" in error_message

    @pytest.mark.asyncio
    async def test_csv_with_malformed_data(self):
        """Test CSV with malformed data (wrong data types) returns 400."""
        # Create CSV content with malformed data
        csv_content = """product_id,name,description,price
prod_1,Product 1,Test product,invalid_price
prod_2,Product 2,Another product,not_a_number"""
        csv_file = UploadFile(
            filename="test.csv",
            file=BytesIO(csv_content.encode()),
            content_type="text/csv",
        )

        # Mock request and dependencies
        mock_request = MagicMock()
        mock_tenant_repo = MagicMock()
        mock_product_repo = MagicMock()

        # Mock tenant
        mock_tenant = MagicMock(id=1, name="Test Publisher")
        mock_tenant_repo.get_by_id.return_value = mock_tenant

        # Call function
        with pytest.raises(Exception) as exc_info:
            await bulk_upload_products(
                request=mock_request,
                tenant_id=1,
                file=csv_file,
                tenant_repo=mock_tenant_repo,
                product_repo=mock_product_repo,
            )

        # Verify error message contains validation information
        error_message = str(exc_info.value)
        assert (
            "validation" in error_message.lower() or "invalid" in error_message.lower()
        )

    @pytest.mark.asyncio
    async def test_csv_with_too_many_rows(self):
        """Test CSV with too many rows returns 400."""
        # Create CSV content with too many rows (assuming limit is 1000)
        csv_content = "product_id,name,description\n"
        for i in range(1001):
            csv_content += f"prod_{i},Product {i},Description {i}\n"

        csv_file = UploadFile(
            filename="test.csv",
            file=BytesIO(csv_content.encode()),
            content_type="text/csv",
        )

        # Mock request and dependencies
        mock_request = MagicMock()
        mock_tenant_repo = MagicMock()
        mock_product_repo = MagicMock()

        # Mock tenant
        mock_tenant = MagicMock(id=1, name="Test Publisher")
        mock_tenant_repo.get_by_id.return_value = mock_tenant

        # Call function
        with pytest.raises(Exception) as exc_info:
            await bulk_upload_products(
                request=mock_request,
                tenant_id=1,
                file=csv_file,
                tenant_repo=mock_tenant_repo,
                product_repo=mock_product_repo,
            )

        # Verify error message contains limit information
        error_message = str(exc_info.value)
        assert "limit" in error_message.lower() or "too many" in error_message.lower()

    @pytest.mark.asyncio
    async def test_csv_with_special_characters(self):
        """Test CSV with special characters in data is handled correctly."""
        # Create CSV content with special characters
        csv_content = "product_id,name,description\n"
        csv_content += (
            'prod_1,"Product with ""quotes""",Description with single quotes\n'
        )
        csv_content += (
            "prod_2,Product with emojis rocket,Description with special chars: & < >"
        )
        csv_file = UploadFile(
            filename="test.csv",
            file=BytesIO(csv_content.encode()),
            content_type="text/csv",
        )

        # Mock request and dependencies
        mock_request = MagicMock()
        mock_tenant_repo = MagicMock()
        mock_product_repo = MagicMock()

        # Mock tenant
        mock_tenant = MagicMock(id=1, name="Test Publisher")
        mock_tenant_repo.get_by_id.return_value = mock_tenant

        # Mock successful product creation
        mock_product_repo.bulk_create.return_value = 2

        # Call function
        result = await bulk_upload_products(
            request=mock_request,
            tenant_id=1,
            file=csv_file,
            tenant_repo=mock_tenant_repo,
            product_repo=mock_product_repo,
        )

        # Verify products were created successfully
        assert "2 products imported successfully" in result.body.decode()
        mock_product_repo.bulk_create.assert_called_once()
