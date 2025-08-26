"""Tenant management routes."""

from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from ..deps import get_db_session
from ..models.tenant import Tenant
from ..repositories.tenants import TenantRepository

templates = Jinja2Templates(directory="app/templates")

router = APIRouter()


def get_tenant_repo(session: Session = Depends(get_db_session)) -> TenantRepository:
    """Get tenant repository."""
    return TenantRepository(session)


def _validate_slug_uniqueness(
    slug: str, repo: TenantRepository, exclude_id: Optional[int] = None
) -> Optional[str]:
    """Validate slug uniqueness and return error message if invalid."""
    existing = repo.get_by_slug(slug)
    if existing and (exclude_id is None or existing.id != exclude_id):
        return f"Slug '{slug}' is already taken. Please choose a different one."
    return None


def _render_form_with_error(
    request: Request, tenant, action: str, error: str
) -> HTMLResponse:
    """Render form template with error message."""
    return templates.TemplateResponse(
        "tenants/form.html",
        {"request": request, "tenant": tenant, "action": action, "error": error},
        status_code=400,
    )


@router.get("/tenants", response_class=HTMLResponse)
async def list_tenants(
    request: Request, repo: TenantRepository = Depends(get_tenant_repo)
):
    """List all tenants."""
    tenants = repo.list_all()
    return templates.TemplateResponse(
        "tenants/index.html",
        {
            "request": request,
            "tenants": tenants,
            "title": "Tenants - AdCP Demo Orchestrator",
            "config": request.app.state.settings,
        },
    )


@router.get("/tenants/add", response_class=HTMLResponse)
async def add_tenant_form(request: Request):
    """Show add tenant form."""
    return templates.TemplateResponse(
        "tenants/form.html", {"request": request, "tenant": None, "action": "add", "config": request.app.state.settings}
    )


@router.post("/tenants/add", response_class=HTMLResponse)
async def create_tenant(
    request: Request,
    name: str = Form(...),
    slug: str = Form(...),
    repo: TenantRepository = Depends(get_tenant_repo),
):
    """Create a new tenant."""
    # Validate slug uniqueness
    error = _validate_slug_uniqueness(slug, repo)
    if error:
        return _render_form_with_error(
            request, {"name": name, "slug": slug}, "add", error
        )

    # Create tenant
    tenant = Tenant(name=name, slug=slug)
    try:
        repo.create(tenant)
        return RedirectResponse(url="/tenants", status_code=302)
    except Exception as e:
        return _render_form_with_error(
            request,
            {"name": name, "slug": slug},
            "add",
            f"Error creating tenant: {str(e)}",
        )


@router.get("/tenants/{tenant_id}/edit", response_class=HTMLResponse)
async def edit_tenant_form(
    request: Request, tenant_id: int, repo: TenantRepository = Depends(get_tenant_repo)
):
    """Show edit tenant form."""
    tenant = repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    return templates.TemplateResponse(
        "tenants/form.html", {"request": request, "tenant": tenant, "action": "edit", "config": request.app.state.settings}
    )


@router.post("/tenants/{tenant_id}/edit", response_class=HTMLResponse)
async def update_tenant(
    request: Request,
    tenant_id: int,
    name: str = Form(...),
    slug: str = Form(...),
    repo: TenantRepository = Depends(get_tenant_repo),
):
    """Update a tenant."""
    tenant = repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Check slug uniqueness (excluding current tenant)
    error = _validate_slug_uniqueness(slug, repo, exclude_id=tenant_id)
    if error:
        return _render_form_with_error(request, tenant, "edit", error)

    # Update tenant
    tenant.name = name
    tenant.slug = slug
    try:
        repo.update(tenant)
        return RedirectResponse(url="/tenants", status_code=302)
    except Exception as e:
        return _render_form_with_error(
            request, tenant, "edit", f"Error updating tenant: {str(e)}"
        )
