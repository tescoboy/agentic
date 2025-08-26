"""AI provider abstraction interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class AIProvider(ABC):
    """Abstract base class for AI providers."""

    @abstractmethod
    async def rank_products(
        self,
        brief: str,
        prompt: str,
        products: List[Dict[str, Any]],
        model_name: str,
        timeout_ms: int,
    ) -> List[Dict[str, Any]]:
        """
        Rank products against a buyer brief using AI.

        Args:
            brief: Buyer's brief/requirements
            prompt: AI prompt to use for ranking
            products: List of product dictionaries with AdCP Product fields
            model_name: AI model to use
            timeout_ms: Request timeout in milliseconds

        Returns:
            List of ranked products with reasons and optional scores:
            [{"product_id": "<id>", "reason": "<text>", "score": <float|None>}]

        Raises:
            AIConfigError: If provider is not properly configured
            AIRequestError: If provider returns non-2xx or invalid response
            AITimeoutError: If request times out
        """
        pass


# Provider registry
_providers: Dict[str, AIProvider] = {}


def register_provider(name: str, provider: AIProvider) -> None:
    """Register an AI provider."""
    _providers[name] = provider


def get_provider(name: str) -> AIProvider:
    """Get an AI provider by name."""
    if name not in _providers:
        raise AIConfigError(
            f"AI provider '{name}' not found. Available: {list(_providers.keys())}"
        )
    return _providers[name]


def get_default_provider() -> AIProvider:
    """Get the default AI provider (Gemini)."""
    return get_provider("gemini")
