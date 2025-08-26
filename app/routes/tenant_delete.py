"""Tenant deletion routes."""

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from ..deps import get_db_session
from ..repositories.tenants import TenantRepository

templates = Jinja2Templates(directory="app/templates")

router = APIRouter()


def get_tenant_repo(session: Session = Depends(get_db_session)) -> TenantRepository:
    """Get tenant repository."""
    return TenantRepository(session)


@router.get("/tenants/{tenant_id}/delete", response_class=HTMLResponse)
async def confirm_delete_tenant(
    request: Request, tenant_id: int, repo: TenantRepository = Depends(get_tenant_repo)
):
    """Show delete confirmation."""
    tenant = repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    return templates.TemplateResponse(
        "tenants/confirm_delete.html", {"request": request, "tenant": tenant}
    )


@router.post("/tenants/{tenant_id}/delete", response_class=HTMLResponse)
async def delete_tenant(
    request: Request,
    tenant_id: int,
    confirmation: str = Form(...),
    repo: TenantRepository = Depends(get_tenant_repo),
):
    """Delete a tenant."""
    if confirmation != "DELETE":
        return templates.TemplateResponse(
            "tenants/confirm_delete.html",
            {
                "request": request,
                "tenant": repo.get_by_id(tenant_id),
                "error": "Please type 'DELETE' to confirm deletion.",
            },
            status_code=400,
        )

    success = repo.delete(tenant_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tenant not found")

    return RedirectResponse(url="/tenants", status_code=302)
