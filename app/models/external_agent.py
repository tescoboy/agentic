"""External agent model for MCP endpoint configuration."""

import json
from datetime import datetime
from typing import Any, Dict, Optional

from sqlmodel import Field, SQLModel


class ExternalAgent(SQLModel, table=True):
    """External agent model for MCP endpoint configuration."""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(..., description="Human-readable agent name")
    base_url: str = Field(..., description="MCP endpoint URL")
    enabled: bool = Field(default=True, description="Whether this agent is active")
    capabilities: str = Field(
        default="{}", description="JSON string of agent capabilities"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )

    def get_capabilities(self) -> Dict[str, Any]:
        """Get capabilities as a dictionary."""
        try:
            return json.loads(self.capabilities)
        except (json.JSONDecodeError, TypeError):
            return {}

    def set_capabilities(self, capabilities: Dict[str, Any]) -> None:
        """Set capabilities from a dictionary."""
        self.capabilities = json.dumps(capabilities)

    model_config = {"arbitrary_types_allowed": True}
