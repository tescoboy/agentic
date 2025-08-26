"""Tenant context management routes."""

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlmodel import Session

from ..deps import get_db_session
from ..repositories.tenants import TenantRepository
from ..utils.cookies import get_active_tenant_id, set_active_tenant_cookie

router = APIRouter()


def get_tenant_repo(session: Session = Depends(get_db_session)) -> TenantRepository:
    """Get tenant repository."""
    return TenantRepository(session)


@router.post("/tenants/select")
async def select_tenant(
    request: Request,
    tenant_id: int = Form(...),
    repo: TenantRepository = Depends(get_tenant_repo),
):
    """Select an active tenant."""
    # Verify tenant exists
    tenant = repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Create redirect response
    redirect_response = RedirectResponse(url="/", status_code=302)

    # Set cookie on the redirect response
    set_active_tenant_cookie(redirect_response, tenant_id)

    return redirect_response


@router.get("/tenants/current")
async def get_current_tenant(
    request: Request, repo: TenantRepository = Depends(get_tenant_repo)
):
    """Get the currently active tenant."""
    tenant_id = get_active_tenant_id(request)

    if not tenant_id:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "No active tenant selected",
                "message": "Please select a tenant from the dropdown in the navbar",
            },
        )

    tenant = repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "Active tenant not found",
                "message": "The selected tenant no longer exists",
            },
        )

    return {
        "id": tenant.id,
        "name": tenant.name,
        "slug": tenant.slug,
        "created_at": tenant.created_at.isoformat(),
        "updated_at": tenant.updated_at.isoformat(),
    }
