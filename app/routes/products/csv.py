"""Product CSV operations routes."""

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates

from ...repositories.products import ProductRepository
from ...repositories.tenants import TenantRepository
from ...services.csv_import import parse_csv_content
from ...services.csv_template import generate_csv_template
from .shared import _validate_tenant_access, get_product_repo, get_tenant_repo

templates = Jinja2Templates(directory="app/templates")

router = APIRouter()


@router.get("/tenant/{tenant_id}/products/template.csv")
async def download_csv_template(
    tenant_id: int, tenant_repo: TenantRepository = Depends(get_tenant_repo)
):
    """Download CSV template for product import."""
    # Validate tenant exists
    tenant = tenant_repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    csv_content = generate_csv_template()

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=products_template_{tenant.slug}.csv"
        },
    )


@router.post("/tenant/{tenant_id}/products/bulk-upload", response_class=HTMLResponse)
async def bulk_upload_products(
    request: Request,
    tenant_id: int,
    file: UploadFile = File(...),
    product_repo: ProductRepository = Depends(get_product_repo),
    tenant_repo: TenantRepository = Depends(get_tenant_repo),
):
    """Bulk upload products from CSV."""
    # Validate tenant access
    tenant = _validate_tenant_access(tenant_id, request, tenant_repo)

    # Validate file
    if not file.filename.endswith(".csv"):
        # Get products list to provide template context
        products, total = product_repo.search_by_tenant(
            tenant_id=tenant_id, page=1, size=20
        )

        return templates.TemplateResponse(
            "products/index.html",
            {
                "request": request,
                "tenant": tenant,
                "products": products,
                "total": total,
                "page": 1,
                "size": 20,
                "total_pages": 1,
                "query": None,
                "sort": "name",
                "order": "asc",
                "error": "Please upload a CSV file",
                "config": request.app.state.settings,
            },
            status_code=400,
        )

    try:
        # Read CSV content
        csv_content = await file.read()
        csv_content_str = csv_content.decode("utf-8")

        # Parse and validate CSV
        products, errors = parse_csv_content(csv_content_str, tenant_id)

        if errors:
            # Return error details
            error_messages = [
                f"Row {e.row_number}: {e.field} - {e.message}" for e in errors
            ]
            # Get products list to provide template context
            products, total = product_repo.search_by_tenant(
                tenant_id=tenant_id, page=1, size=20
            )

            return templates.TemplateResponse(
                "products/index.html",
                {
                    "request": request,
                    "tenant": tenant,
                    "products": products,
                    "total": total,
                    "page": 1,
                    "size": 20,
                    "total_pages": 1,
                    "query": None,
                    "sort": "name",
                    "order": "asc",
                    "error": "CSV import failed",
                    "error_details": error_messages,
                    "config": request.app.state.settings,
                },
                status_code=400,
            )

        # Import products
        if products:
            product_repo.bulk_create(products)

        return RedirectResponse(
            url=f"/tenant/{tenant_id}/products?message=Successfully imported {len(products)} products",
            status_code=302,
        )

    except Exception as e:
        # Get products list to provide template context
        products, total = product_repo.search_by_tenant(
            tenant_id=tenant_id, page=1, size=20
        )

        return templates.TemplateResponse(
            "products/index.html",
            {
                "request": request,
                "tenant": tenant,
                "products": products,
                "total": total,
                "page": 1,
                "size": 20,
                "total_pages": 1,
                "query": None,
                "sort": "name",
                "order": "asc",
                "error": f"Error processing CSV: {str(e)}",
                "config": request.app.state.settings,
            },
            status_code=400,
        )
