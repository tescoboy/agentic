"""Product creation operations routes."""

from typing import Optional

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from ...models.product import Product
from ...repositories.products import ProductRepository
from ...repositories.tenants import TenantRepository
from .shared import _validate_tenant_access, get_product_repo, get_tenant_repo

templates = Jinja2Templates(directory="app/templates")

router = APIRouter()


@router.get("/tenant/{tenant_id}/products/add", response_class=HTMLResponse)
async def add_product_form(
    request: Request,
    tenant_id: int,
    tenant_repo: TenantRepository = Depends(get_tenant_repo),
):
    """Show add product form."""
    # Validate tenant access
    tenant = _validate_tenant_access(tenant_id, request, tenant_repo)

    return templates.TemplateResponse(
        "products/form.html",
        {"request": request, "tenant": tenant, "product": None, "action": "add", "config": request.app.state.settings},
    )


@router.post("/tenant/{tenant_id}/products/add", response_class=HTMLResponse)
async def create_product(
    request: Request,
    tenant_id: int,
    product_id: str = Form(...),
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
    """Create a new product."""
    # Validate tenant access
    tenant = _validate_tenant_access(tenant_id, request, tenant_repo)

    # Check if product_id already exists
    existing = product_repo.get_by_product_id(product_id)
    if existing:
        # Parse form data for error display
        is_fixed_price_bool = is_fixed_price.lower() == "true"
        is_custom_bool = is_custom.lower() == "true"
        cpm_float = float(cpm) if cpm else None
        verified_minimum_age_int = (
            int(verified_minimum_age) if verified_minimum_age else None
        )

        return templates.TemplateResponse(
            "products/form.html",
            {
                "request": request,
                "tenant": tenant,
                "product": {
                    "product_id": product_id,
                    "name": name,
                    "description": description,
                    "delivery_type": delivery_type,
                    "is_fixed_price": is_fixed_price_bool,
                    "cpm": cpm_float,
                    "is_custom": is_custom_bool,
                    "policy_compliance": policy_compliance,
                    "targeted_ages": targeted_ages,
                    "verified_minimum_age": verified_minimum_age_int,
                },
                "action": "add",
                "error": f"Product ID '{product_id}' already exists",
                "config": request.app.state.settings,
            },
            status_code=400,
        )

    # Parse form data
    is_fixed_price_bool = is_fixed_price.lower() == "true"
    is_custom_bool = is_custom.lower() == "true"
    cpm_float = float(cpm) if cpm else None
    verified_minimum_age_int = (
        int(verified_minimum_age) if verified_minimum_age else None
    )

    # Create product
    product = Product(
        tenant_id=tenant_id,
        product_id=product_id,
        name=name,
        description=description,
        delivery_type=delivery_type,
        is_fixed_price=is_fixed_price_bool,
        cpm=cpm_float,
        is_custom=is_custom_bool,
        policy_compliance=policy_compliance,
        targeted_ages=targeted_ages,
        verified_minimum_age=verified_minimum_age_int,
    )

    try:
        product_repo.create(product)
        return RedirectResponse(url=f"/tenant/{tenant_id}/products", status_code=302)
    except Exception as e:
        return templates.TemplateResponse(
            "products/form.html",
            {
                "request": request,
                "tenant": tenant,
                "product": product,
                "action": "add",
                "error": f"Error creating product: {str(e)}",
                "config": request.app.state.settings,
            },
            status_code=400,
        )
