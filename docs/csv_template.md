# CSV Template Documentation

This document describes the CSV template format for bulk importing products into the AdCP Demo Orchestrator.

## Template Download

Download the CSV template for a specific tenant:
```
GET /tenant/{tenant_id}/products/template.csv
```

The template will be downloaded as: `products_template_{tenant_slug}.csv`

## CSV Format

### Required Columns

| Column | Type | Required | Description | Example |
|--------|------|----------|-------------|---------|
| `product_id` | String | Yes | Unique product identifier | `banner_001` |
| `name` | String | Yes | Product display name | `Sports Banner Ad` |
| `description` | String | Yes | Product description | `High-visibility banner for sports websites` |

### Optional Columns

| Column | Type | Required | Description | Example |
|--------|------|----------|-------------|---------|
| `price` | Decimal | No | Product price (if applicable) | `10.50` |
| `cpm` | Decimal | No | Cost per mille | `2.75` |
| `formats` | String | No | Ad formats (comma-separated) | `banner,video` |
| `tags` | String | No | Product tags (comma-separated) | `sports,young-adults` |

## Example CSV

```csv
product_id,name,description,price,cpm,formats,tags
banner_001,Sports Banner Ad,High-visibility banner for sports websites,10.50,2.75,banner,sports
video_001,Sports Video Ad,Video advertisement for sports content,25.00,5.00,video,sports
native_001,Sports Native Ad,Native advertisement for sports content,15.00,3.50,native,sports
```

## Import Process

### 1. Prepare Your CSV File

1. **Use the template**: Download the template for your tenant
2. **Fill in data**: Add your product information
3. **Validate format**: Ensure all required columns are present
4. **Check data**: Verify product IDs are unique within your tenant

### 2. Upload via Web Interface

1. Navigate to: `/tenant/{tenant_id}/products`
2. Click "Bulk Upload" button
3. Select your CSV file
4. Click "Upload"

### 3. Review Results

- **Success**: Products are imported and listed
- **Errors**: Validation errors are displayed with row numbers

## Validation Rules

### Product ID
- **Required**: Must be provided
- **Format**: String, no spaces
- **Uniqueness**: Must be unique within the tenant
- **Length**: Maximum 100 characters
- **Characters**: Alphanumeric, hyphens, underscores only

### Name
- **Required**: Must be provided
- **Length**: 1-200 characters
- **Content**: Cannot be empty or whitespace-only

### Description
- **Required**: Must be provided
- **Length**: 1-1000 characters
- **Content**: Cannot be empty or whitespace-only

### Price (Optional)
- **Format**: Decimal number
- **Range**: 0.01 to 999999.99
- **Precision**: Up to 2 decimal places

### CPM (Optional)
- **Format**: Decimal number
- **Range**: 0.01 to 999999.99
- **Precision**: Up to 2 decimal places

### Formats (Optional)
- **Format**: Comma-separated values
- **Valid values**: banner, video, native, display, social
- **Case**: Case-insensitive

### Tags (Optional)
- **Format**: Comma-separated values
- **Length**: Each tag 1-50 characters
- **Count**: Maximum 10 tags per product

## Common Import Errors

### Missing Required Columns

**Error**: `Missing required columns: product_id, name`

**Solution**: Ensure all required columns are present in your CSV file.

**Example**:
```csv
# ❌ Missing product_id
name,description
Sports Banner,High-visibility banner

# ✅ Correct
product_id,name,description
banner_001,Sports Banner,High-visibility banner
```

### Empty Required Fields

**Error**: `Row 2: name - Field cannot be empty`

**Solution**: Fill in all required fields.

**Example**:
```csv
# ❌ Empty name field
product_id,name,description
banner_001,,High-visibility banner

# ✅ Correct
product_id,name,description
banner_001,Sports Banner,High-visibility banner
```

### Duplicate Product IDs

**Error**: `Duplicate product_id found: banner_001`

**Solution**: Ensure each product ID is unique within your tenant.

**Example**:
```csv
# ❌ Duplicate product_id
product_id,name,description
banner_001,Sports Banner,High-visibility banner
banner_001,Video Ad,Video advertisement

# ✅ Correct
product_id,name,description
banner_001,Sports Banner,High-visibility banner
video_001,Video Ad,Video advertisement
```

### Invalid Price Format

**Error**: `Row 3: price - Invalid decimal format`

**Solution**: Use proper decimal format.

**Example**:
```csv
# ❌ Invalid price format
product_id,name,description,price
banner_001,Sports Banner,High-visibility banner,invalid_price

# ✅ Correct
product_id,name,description,price
banner_001,Sports Banner,High-visibility banner,10.50
```

### Invalid Product ID Format

**Error**: `Row 2: product_id - Invalid format`

**Solution**: Use only alphanumeric characters, hyphens, and underscores.

**Example**:
```csv
# ❌ Invalid product_id format
product_id,name,description
banner@001,Sports Banner,High-visibility banner

# ✅ Correct
product_id,name,description
banner_001,Sports Banner,High-visibility banner
```

### Too Many Rows

**Error**: `CSV file exceeds maximum limit of 1000 rows`

**Solution**: Split large files into smaller chunks.

### Unknown Columns

**Error**: `Unknown columns: extra_column, another_column`

**Solution**: Remove or rename unknown columns to match the template.

**Example**:
```csv
# ❌ Unknown columns
product_id,name,description,extra_column,another_column
banner_001,Sports Banner,High-visibility banner,value1,value2

# ✅ Correct
product_id,name,description
banner_001,Sports Banner,High-visibility banner
```

## Best Practices

### 1. Use Descriptive Product IDs
```csv
# ✅ Good
product_id,name,description
sports_banner_001,Sports Banner Ad,High-visibility banner for sports websites

# ❌ Avoid
product_id,name,description
prod1,Banner,Ad
```

### 2. Write Clear Descriptions
```csv
# ✅ Good
product_id,name,description
sports_banner_001,Sports Banner Ad,High-visibility banner advertisement optimized for sports websites with targeting for sports enthusiasts aged 18-35

# ❌ Avoid
product_id,name,description
banner_001,Banner,Ad for sports
```

### 3. Use Consistent Naming
```csv
# ✅ Consistent
product_id,name,description
sports_banner_001,Sports Banner Ad,High-visibility banner for sports websites
sports_video_001,Sports Video Ad,Video advertisement for sports content
sports_native_001,Sports Native Ad,Native advertisement for sports content

# ❌ Inconsistent
product_id,name,description
banner_001,Sports Banner Ad,High-visibility banner for sports websites
video_ad_002,Video Advertisement,Video advertisement for sports content
native_003,Native Ad,Native advertisement for sports content
```

### 4. Validate Before Upload
- Check for duplicate product IDs
- Ensure all required fields are filled
- Verify price/CPM formats
- Test with a small sample first

## Troubleshooting

### File Encoding Issues
If you encounter encoding problems:
1. Save your CSV file as UTF-8
2. Avoid special characters in product names
3. Use standard ASCII characters for product IDs

### Large File Uploads
For files with many products:
1. Split into smaller files (max 1000 rows)
2. Upload in batches
3. Verify each batch before proceeding

### Data Validation
Before uploading:
1. Review all product information
2. Check for typos and formatting errors
3. Ensure product IDs follow naming conventions
4. Validate price and CPM values

## Support

If you encounter issues with CSV import:

1. **Check the error message** for specific details
2. **Review the validation rules** above
3. **Download a fresh template** and compare with your file
4. **Test with a single row** to isolate the issue
5. **Contact support** with the specific error message and a sample of your data
