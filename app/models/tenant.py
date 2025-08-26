"""Tenant model for multi-tenancy support."""

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Tenant(SQLModel, table=True):
    """Tenant model for multi-tenancy support."""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(..., description="Human-readable tenant name")
    slug: str = Field(
        ..., unique=True, index=True, description="URL-safe tenant identifier"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )

    model_config = {"arbitrary_types_allowed": True}
