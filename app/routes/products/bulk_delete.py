"""Product bulk delete operations routes."""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from ...repositories.products import ProductRepository
from ...repositories.tenants import TenantRepository
from .shared import _validate_tenant_access, get_product_repo, get_tenant_repo

templates = Jinja2Templates(directory="app/templates")

router = APIRouter()


@router.get("/tenant/{tenant_id}/products/bulk-delete", response_class=HTMLResponse)
async def bulk_delete_confirm(
    request: Request,
    tenant_id: int,
    tenant_repo: TenantRepository = Depends(get_tenant_repo),
    product_repo: ProductRepository = Depends(get_product_repo),
):
    """Show bulk delete confirmation page."""
    # Validate tenant access
    tenant = _validate_tenant_access(tenant_id, request, tenant_repo)

    # Get product count
    products, total = product_repo.search_by_tenant(tenant_id=tenant_id, page=1, size=1)

    return templates.TemplateResponse(
        "products/bulk_delete_confirm.html",
        {"request": request, "tenant": tenant, "product_count": total, "config": request.app.state.settings},
    )


@router.post("/tenant/{tenant_id}/products/bulk-delete", response_class=HTMLResponse)
async def bulk_delete_products(
    request: Request,
    tenant_id: int,
    confirmation: str = Form(...),
    product_repo: ProductRepository = Depends(get_product_repo),
    tenant_repo: TenantRepository = Depends(get_tenant_repo),
):
    """Bulk delete all products for a tenant."""
    # Validate tenant access
    tenant = _validate_tenant_access(tenant_id, request, tenant_repo)

    # Validate confirmation
    if confirmation != "DELETE":
        # Get product count for template
        products, total = product_repo.search_by_tenant(
            tenant_id=tenant_id, page=1, size=1
        )

        return templates.TemplateResponse(
            "products/bulk_delete_confirm.html",
            {
                "request": request,
                "tenant": tenant,
                "product_count": total,
                "error": "Please type 'DELETE' to confirm",
                "config": request.app.state.settings,
            },
            status_code=400,
        )

    # Delete all products
    deleted_count = product_repo.delete_all_by_tenant(tenant_id)

    return RedirectResponse(
        url=f"/tenant/{tenant_id}/products?message=Successfully deleted {deleted_count} products",
        status_code=302,
    )
