"""Agent settings repository for tenant-specific AI configuration."""

from typing import Optional

from sqlmodel import Session, select

from ..models.agent_settings import AgentSettings


class AgentSettingsRepository:
    """Repository for AgentSettings operations."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_tenant(self, tenant_id: int) -> Optional[AgentSettings]:
        """Get agent settings for a tenant."""
        statement = select(AgentSettings).where(AgentSettings.tenant_id == tenant_id)
        return self.session.exec(statement).first()

    def upsert_for_tenant(self, tenant_id: int, **kwargs) -> AgentSettings:
        """Create or update agent settings for a tenant."""
        existing = self.get_by_tenant(tenant_id)

        if existing:
            # Update existing settings
            for key, value in kwargs.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            self.session.add(existing)
            self.session.commit()
            self.session.refresh(existing)
            return existing
        else:
            # Create new settings
            settings = AgentSettings(tenant_id=tenant_id, **kwargs)
            self.session.add(settings)
            self.session.commit()
            self.session.refresh(settings)
            return settings
