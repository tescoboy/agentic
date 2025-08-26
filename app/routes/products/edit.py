"""Product edit and delete operations routes."""

from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from ...repositories.products import ProductRepository
from ...repositories.tenants import TenantRepository
from .shared import _validate_tenant_access, get_product_repo, get_tenant_repo

templates = Jinja2Templates(directory="app/templates")

router = APIRouter()


@router.get(
    "/tenant/{tenant_id}/products/{product_id}/edit", response_class=HTMLResponse
)
async def edit_product_form(
    request: Request,
    tenant_id: int,
    product_id: int,
    product_repo: ProductRepository = Depends(get_product_repo),
    tenant_repo: TenantRepository = Depends(get_tenant_repo),
):
    """Show edit product form."""
    # Validate tenant access
    tenant = _validate_tenant_access(tenant_id, request, tenant_repo)

    # Get product
    product = product_repo.get_by_id(product_id)
    if not product or product.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Product not found")

    return templates.TemplateResponse(
        "products/form.html",
        {"request": request, "tenant": tenant, "product": product, "action": "edit", "config": request.app.state.settings},
    )


@router.post(
    "/tenant/{tenant_id}/products/{product_id}/edit", response_class=HTMLResponse
)
async def update_product(
    request: Request,
    tenant_id: int,
    product_id: int,
    name: str = Form(...),
    description: str = Form(...),
    delivery_type: str = Form(...),
    is_fixed_price: str = Form(...),
    cpm: Optional[str] = Form(None),
    is_custom: str = Form("false"),
    policy_compliance: Optional[str] = Form(None),
    targeted_ages: Optional[str] = Form(None),
    verified_minimum_age: Optional[str] = Form(None),
    product_repo: ProductRepository = Depends(get_product_repo),
    tenant_repo: TenantRepository = Depends(get_tenant_repo),
):
    """Update a product."""
    # Validate tenant access
    tenant = _validate_tenant_access(tenant_id, request, tenant_repo)

    # Get product
    product = product_repo.get_by_id(product_id)
    if not product or product.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Product not found")

    # Parse form data
    is_fixed_price_bool = is_fixed_price.lower() == "true"
    is_custom_bool = is_custom.lower() == "true"
    cpm_float = float(cpm) if cpm else None
    verified_minimum_age_int = (
        int(verified_minimum_age) if verified_minimum_age else None
    )

    # Update product
    product.name = name
    product.description = description
    product.delivery_type = delivery_type
    product.is_fixed_price = is_fixed_price_bool
    product.cpm = cpm_float
    product.is_custom = is_custom_bool
    product.policy_compliance = policy_compliance
    product.targeted_ages = targeted_ages
    product.verified_minimum_age = verified_minimum_age_int

    try:
        product_repo.update(product)
        return RedirectResponse(url=f"/tenant/{tenant_id}/products", status_code=302)
    except Exception as e:
        return templates.TemplateResponse(
            "products/form.html",
            {
                "request": request,
                "tenant": tenant,
                "product": product,
                "action": "edit",
                "error": f"Error updating product: {str(e)}",
                "config": request.app.state.settings,
            },
            status_code=400,
        )


@router.post(
    "/tenant/{tenant_id}/products/{product_id}/delete", response_class=HTMLResponse
)
async def delete_product(
    request: Request,
    tenant_id: int,
    product_id: int,
    product_repo: ProductRepository = Depends(get_product_repo),
    tenant_repo: TenantRepository = Depends(get_tenant_repo),
):
    """Delete a product."""
    # Validate tenant access
    _validate_tenant_access(tenant_id, request, tenant_repo)

    # Get product
    product = product_repo.get_by_id(product_id)
    if not product or product.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Product not found")

    # Delete product
    product_repo.delete(product_id)
    return RedirectResponse(url=f"/tenant/{tenant_id}/products", status_code=302)
