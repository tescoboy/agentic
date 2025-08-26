"""Product model based on AdCP specification.

Source: reference/salesagent/src/core/schemas.py
Fields aligned with AdCP Product schema including nested structures stored as JSON.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlmodel import Field, SQLModel


class Product(SQLModel, table=True):
    """Product model based on AdCP specification.

    Source files used:
    - reference/salesagent/src/core/schemas.py (lines 150-210)

    Complex nested objects (Format, Asset, PriceGuidance) are stored as JSON strings
    to maintain schema compatibility while keeping the database structure simple.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(
        ..., foreign_key="tenant.id", description="Tenant this product belongs to"
    )

    # Core AdCP Product fields
    product_id: str = Field(..., unique=True, description="Unique product identifier")
    name: str = Field(..., description="Product name")
    description: str = Field(..., description="Product description")

    # Complex nested objects stored as JSON
    formats: str = Field(default="[]", description="JSON string of Format objects")
    delivery_type: str = Field(
        ..., description="Delivery type (guaranteed or non_guaranteed)"
    )
    is_fixed_price: bool = Field(
        ..., description="Whether this is a fixed price product"
    )

    # Pricing fields
    cpm: Optional[float] = Field(default=None, description="Cost per mille")
    price_guidance: Optional[str] = Field(
        default=None, description="JSON string of PriceGuidance object"
    )

    # Product metadata
    is_custom: bool = Field(
        default=False, description="Whether this is a custom product"
    )
    expires_at: Optional[datetime] = Field(
        default=None, description="Product expiration date"
    )

    # Implementation and compliance
    implementation_config: Optional[str] = Field(
        default=None, description="JSON string of ad server config"
    )
    policy_compliance: Optional[str] = Field(
        default=None, description="Policy compliance information"
    )

    # Audience targeting
    targeted_ages: Optional[str] = Field(
        default=None, description="Target age group (children, teens, or adults)"
    )
    verified_minimum_age: Optional[int] = Field(
        default=None, description="Minimum age requirement"
    )

    # Timestamps
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )

    def get_formats(self) -> List[Dict[str, Any]]:
        """Get formats as a list of dictionaries."""
        try:
            return json.loads(self.formats)
        except (json.JSONDecodeError, TypeError):
            return []

    def set_formats(self, formats: List[Dict[str, Any]]) -> None:
        """Set formats from a list of dictionaries."""
        self.formats = json.dumps(formats)

    def get_price_guidance(self) -> Optional[Dict[str, Any]]:
        """Get price guidance as a dictionary."""
        if not self.price_guidance:
            return None
        try:
            return json.loads(self.price_guidance)
        except (json.JSONDecodeError, TypeError):
            return None

    def set_price_guidance(self, price_guidance: Optional[Dict[str, Any]]) -> None:
        """Set price guidance from a dictionary."""
        self.price_guidance = json.dumps(price_guidance) if price_guidance else None

    def get_implementation_config(self) -> Optional[Dict[str, Any]]:
        """Get implementation config as a dictionary."""
        if not self.implementation_config:
            return None
        try:
            return json.loads(self.implementation_config)
        except (json.JSONDecodeError, TypeError):
            return None

    def set_implementation_config(self, config: Optional[Dict[str, Any]]) -> None:
        """Set implementation config from a dictionary."""
        self.implementation_config = json.dumps(config) if config else None

    model_config = {"arbitrary_types_allowed": True}
