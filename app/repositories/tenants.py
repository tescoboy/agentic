"""Tenant repository for CRUD operations."""

from typing import List, Optional

from fastapi import Depends
from sqlmodel import Session, select

from ..models.tenant import Tenant
from ..deps import get_db_session


class TenantRepository:
    """Repository for Tenant CRUD operations."""

    def __init__(self, session: Session):
        self.session = session

    def create(self, tenant: Tenant) -> Tenant:
        """Create a new tenant."""
        self.session.add(tenant)
        self.session.commit()
        self.session.refresh(tenant)
        return tenant

    def get_by_id(self, tenant_id: int) -> Optional[Tenant]:
        """Get tenant by ID."""
        statement = select(Tenant).where(Tenant.id == tenant_id)
        return self.session.exec(statement).first()

    def get_by_slug(self, slug: str) -> Optional[Tenant]:
        """Get tenant by slug."""
        statement = select(Tenant).where(Tenant.slug == slug)
        return self.session.exec(statement).first()

    def list_all(self) -> List[Tenant]:
        """List all tenants."""
        statement = select(Tenant).order_by(Tenant.name)
        return list(self.session.exec(statement))

    def update(self, tenant: Tenant) -> Tenant:
        """Update a tenant."""
        from datetime import datetime

        tenant.updated_at = datetime.utcnow()
        self.session.add(tenant)
        self.session.commit()
        self.session.refresh(tenant)
        return tenant

    def delete(self, tenant_id: int) -> bool:
        """Delete a tenant by ID."""
        tenant = self.get_by_id(tenant_id)
        if tenant:
            self.session.delete(tenant)
            self.session.commit()
            return True
        return False


def get_tenant_repo(session: Session = Depends(get_db_session)) -> TenantRepository:
    """Get tenant repository dependency."""
    return TenantRepository(session)
