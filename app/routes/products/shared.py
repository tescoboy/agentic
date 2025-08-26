"""Shared utilities for product routes."""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session

from ...deps import get_db_session
from ...models.tenant import Tenant
from ...repositories.products import ProductRepository
from ...repositories.tenants import TenantRepository
from ...utils.cookies import get_active_tenant_id

router = APIRouter()


def get_product_repo(session: Session = Depends(get_db_session)) -> ProductRepository:
    """Get product repository."""
    return ProductRepository(session)


def get_tenant_repo(session: Session = Depends(get_db_session)) -> TenantRepository:
    """Get tenant repository."""
    return TenantRepository(session)


def _validate_tenant_access(
    tenant_id: int, request: Request, tenant_repo: TenantRepository
) -> Tenant:
    """Validate that the tenant exists and user has access."""
    # Check if tenant exists
    tenant = tenant_repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Check if this is the active tenant
    active_tenant_id = get_active_tenant_id(request)
    if active_tenant_id != tenant_id:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Tenant mismatch",
                "message": f"Please select tenant '{tenant.name}' from the navbar to manage its products",
            },
        )

    return tenant
