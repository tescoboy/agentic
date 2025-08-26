"""Agent settings model for per-tenant AI configuration."""

from typing import Optional

from sqlmodel import Field, SQLModel


class AgentSettings(SQLModel, table=True):
    """Agent settings model for per-tenant AI configuration."""

    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(
        ..., foreign_key="tenant.id", description="Tenant this setting belongs to"
    )
    prompt_override: Optional[str] = Field(
        default=None, description="Custom prompt override for AI agents"
    )
    model_name: str = Field(
        default="gemini-1.5-pro", description="AI model to use for this tenant"
    )
    timeout_ms: int = Field(
        default=30000, description="Timeout in milliseconds for AI calls"
    )

    model_config = {"arbitrary_types_allowed": True}
