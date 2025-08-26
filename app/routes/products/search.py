"""Product search and listing routes."""

from typing import Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from ...repositories.products import ProductRepository
from ...repositories.tenants import TenantRepository
from ...utils.pagination import clamp_pagination
from .shared import _validate_tenant_access, get_product_repo, get_tenant_repo

templates = Jinja2Templates(directory="app/templates")

router = APIRouter()


@router.get("/tenant/{tenant_id}/products", response_class=HTMLResponse)
async def list_products(
    request: Request,
    tenant_id: int,
    q: Optional[str] = None,
    sort: str = "name",
    order: str = "asc",
    page: int = 1,
    size: int = 20,
    product_repo: ProductRepository = Depends(get_product_repo),
    tenant_repo: TenantRepository = Depends(get_tenant_repo),
):
    """List products for a tenant with search, sort, and pagination."""
    # Validate tenant access
    tenant = _validate_tenant_access(tenant_id, request, tenant_repo)

    # Clamp pagination parameters
    page, size = clamp_pagination(page, size)

    # Get products with search and pagination
    products, total = product_repo.search_by_tenant(
        tenant_id=tenant_id, query=q, sort=sort, order=order, page=page, size=size
    )

    # Calculate pagination info
    total_pages = (total + size - 1) // size if total > 0 else 1

    return templates.TemplateResponse(
        "products/index.html",
        {
            "request": request,
            "tenant": tenant,
            "products": products,
            "total": total,
            "page": page,
            "size": size,
            "total_pages": total_pages,
            "query": q,
            "sort": sort,
            "order": order,
            "config": request.app.state.settings,
        },
    )
