"""Cookie utilities for tenant context management."""

from typing import Optional

from fastapi import Request, Response


def set_active_tenant_cookie(response: Response, tenant_id: int) -> None:
    """Set the active tenant cookie."""
    response.set_cookie(
        key="active_tenant_id",
        value=str(tenant_id),
        max_age=30 * 24 * 60 * 60,  # 30 days
        httponly=True,
        samesite="lax",
    )


def get_active_tenant_id(request: Request) -> Optional[int]:
    """Get the active tenant ID from cookie."""
    tenant_id = request.cookies.get("active_tenant_id")
    if tenant_id:
        try:
            return int(tenant_id)
        except (ValueError, TypeError):
            return None
    return None


def clear_active_tenant_cookie(response: Response) -> None:
    """Clear the active tenant cookie."""
    response.delete_cookie(key="active_tenant_id")
