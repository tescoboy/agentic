"""Sales agent service for evaluating buyer briefs against products."""

import os
from typing import Any, Dict, List

from ..ai.errors import AIConfigError, AIRequestError, AITimeoutError
from ..ai.provider import get_default_provider, register_provider
from ..ai.gemini import GeminiProvider
from ..models.agent_settings import AgentSettings
from ..models.product import Product
from ..repositories.agent_settings import AgentSettingsRepository
from ..repositories.products import ProductRepository
from ..repositories.tenants import TenantRepository


def product_to_dict(product: Product) -> Dict[str, Any]:
    """
    Convert Product model to dictionary for AI provider.

    Includes only essential fields to save tokens while maintaining
    all information needed for ranking.
    """
    return {
        "id": product.id,
        "product_id": product.product_id,
        "name": product.name,
        "description": product.description,
        "delivery_type": product.delivery_type,
        "is_fixed_price": product.is_fixed_price,
        "cpm": product.cpm,
        "is_custom": product.is_custom,
        "policy_compliance": product.policy_compliance,
        "targeted_ages": product.targeted_ages,
        "verified_minimum_age": product.verified_minimum_age,
        "expires_at": product.expires_at.isoformat() if product.expires_at else None,
    }


def load_default_prompt() -> str:
    """Load the default sales agent prompt from file."""
    prompt_path = "app/resources/default_sales_prompt.txt"

    if not os.path.exists(prompt_path):
        raise AIConfigError(
            f"Default prompt file not found: {prompt_path}. "
            "Ensure /reference/salesagent is cloned and the prompt path is valid."
        )

    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception as e:
        raise AIConfigError(f"Failed to load default prompt: {e}")


async def evaluate_brief(
    tenant_id: int,
    brief: str,
    agent_settings_repo: AgentSettingsRepository,
    product_repo: ProductRepository,
    tenant_repo: TenantRepository,
) -> List[Dict[str, Any]]:
    """
    Evaluate a buyer brief against tenant's products using AI.

    Args:
        tenant_id: ID of the tenant
        brief: Buyer's brief/requirements
        agent_settings_repo: Repository for agent settings
        product_repo: Repository for products
        tenant_repo: Repository for tenants

    Returns:
        List of ranked products with reasons:
        [{"product_id": "<id>", "reason": "<text>", "score": <float|None>}]

    Raises:
        AIConfigError: If AI is not configured or no products exist
        AIRequestError: If AI request fails
        AITimeoutError: If AI request times out
    """
    # 1. Load AgentSettings for tenant
    agent_settings = agent_settings_repo.get_by_tenant(tenant_id)
    if not agent_settings:
        # Create default settings
        agent_settings = agent_settings_repo.upsert_for_tenant(
            tenant_id, model_name="gemini-1.5-pro", timeout_ms=30000
        )

    # 2. Load tenant's products
    products = product_repo.list_by_tenant(tenant_id)
    if not products:
        raise AIConfigError(
            f"No products found for tenant {tenant_id}. "
            "Please add products before using AI evaluation."
        )

    # 3. Choose prompt: tenant override or default
    if agent_settings.prompt_override:
        prompt = agent_settings.prompt_override
    else:
        prompt = load_default_prompt()

    # 4. Convert products to dict format
    product_dicts = [product_to_dict(p) for p in products]

    # 5. Get AI provider and call it
    try:
        provider = get_default_provider()
        ranked_products = await provider.rank_products(
            brief=brief,
            prompt=prompt,
            products=product_dicts,
            model_name=agent_settings.model_name,
            timeout_ms=agent_settings.timeout_ms,
        )

        return ranked_products

    except (AIConfigError, AIRequestError, AITimeoutError):
        # Re-raise AI-specific errors
        raise
    except Exception as e:
        # Convert other errors to AIRequestError
        raise AIRequestError(f"Unexpected error during AI evaluation: {e}")


# Initialize AI providers on module import
def _initialize_providers():
    """Initialize AI providers."""
    try:
        gemini_provider = GeminiProvider()
        register_provider("gemini", gemini_provider)
    except AIConfigError:
        # Gemini not configured, skip registration
        pass


_initialize_providers()
