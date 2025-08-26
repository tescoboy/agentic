"""External agent repository for MCP endpoint management."""

from typing import List, Optional

from fastapi import Depends
from sqlmodel import Session, select

from ..models.external_agent import ExternalAgent
from ..deps import get_db_session


class ExternalAgentRepository:
    """Repository for ExternalAgent CRUD operations."""

    def __init__(self, session: Session):
        self.session = session

    def create(self, agent: ExternalAgent) -> ExternalAgent:
        """Create a new external agent."""
        self.session.add(agent)
        self.session.commit()
        self.session.refresh(agent)
        return agent

    def get_by_id(self, agent_id: int) -> Optional[ExternalAgent]:
        """Get external agent by ID."""
        statement = select(ExternalAgent).where(ExternalAgent.id == agent_id)
        return self.session.exec(statement).first()

    def list_all(self) -> List[ExternalAgent]:
        """List all external agents."""
        statement = select(ExternalAgent).order_by(ExternalAgent.name)
        return list(self.session.exec(statement))

    def list_enabled(self) -> List[ExternalAgent]:
        """List only enabled external agents."""
        statement = (
            select(ExternalAgent)
            .where(ExternalAgent.enabled == True)
            .order_by(ExternalAgent.name)
        )
        return list(self.session.exec(statement))

    def update(self, agent: ExternalAgent) -> ExternalAgent:
        """Update an external agent."""
        self.session.add(agent)
        self.session.commit()
        self.session.refresh(agent)
        return agent

    def delete(self, agent_id: int) -> bool:
        """Delete an external agent by ID."""
        agent = self.get_by_id(agent_id)
        if agent:
            self.session.delete(agent)
            self.session.commit()
            return True
        return False


def get_external_agent_repo(
    session: Session = Depends(get_db_session),
) -> ExternalAgentRepository:
    """Get external agent repository dependency."""
    return ExternalAgentRepository(session)
