"""Gemini AI provider implementation."""

import asyncio
import json
from typing import Any, Dict, List

import google.generativeai as genai

from .errors import AIConfigError, AIRequestError, AITimeoutError
from .provider import AIProvider
from ..config import settings


class GeminiProvider(AIProvider):
    """Gemini AI provider for product ranking."""

    def __init__(self):
        """Initialize Gemini provider."""
        if not settings.gemini_api_key:
            raise AIConfigError(
                "GEMINI_API_KEY not set. "
                "Set GEMINI_API_KEY in your .env file to use AI features."
            )

        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel("gemini-1.5-pro")

    async def rank_products(
        self,
        brief: str,
        prompt: str,
        products: List[Dict[str, Any]],
        model_name: str,
        timeout_ms: int,
    ) -> List[Dict[str, Any]]:
        """
        Rank products against a buyer brief using Gemini AI.

        Args:
            brief: Buyer's brief/requirements
            prompt: AI prompt to use for ranking
            products: List of product dictionaries with AdCP Product fields
            model_name: AI model to use (ignored, uses gemini-1.5-pro)
            timeout_ms: Request timeout in milliseconds

        Returns:
            List of ranked products with reasons and optional scores:
            [{"product_id": "<id>", "reason": "<text>", "score": <float|None>}]

        Raises:
            AIConfigError: If provider is not properly configured
            AIRequestError: If provider returns non-2xx or invalid response
            AITimeoutError: If request times out
        """
        try:
            # Prepare the prompt with products
            products_json = json.dumps(products, indent=2)

            full_prompt = f"""
{prompt}

BUYER BRIEF:
{brief}

AVAILABLE PRODUCTS:
{products_json}

TASK:
Rank the products from most relevant to least relevant for the buyer brief.
For each product, provide:
1. A clear reason why it matches (or doesn't match) the brief
2. An optional confidence score (0.0 to 1.0)

Return ONLY a JSON array of ranked products with this exact structure:
[
    {{
        "product_id": "product_123",
        "reason": "This product matches the brief because...",
        "score": 0.85
    }},
    {{
        "product_id": "product_456", 
        "reason": "This product partially matches because...",
        "score": 0.65
    }}
]

IMPORTANT:
- Include ALL products in the response
- Order from most relevant to least relevant
- Use the exact product_id values from the input
- Provide clear, specific reasons
- Scores are optional (can be null)
- Return ONLY valid JSON, no other text
"""

            # Run the AI request with timeout
            response = await asyncio.wait_for(
                self._generate_content(full_prompt), timeout=timeout_ms / 1000.0
            )

            # Parse the response
            try:
                # Clean the response - remove markdown code blocks if present
                cleaned_response = response.strip()
                if cleaned_response.startswith('```json'):
                    cleaned_response = cleaned_response[7:]  # Remove ```json
                if cleaned_response.startswith('```'):
                    cleaned_response = cleaned_response[3:]  # Remove ```
                if cleaned_response.endswith('```'):
                    cleaned_response = cleaned_response[:-3]  # Remove trailing ```
                cleaned_response = cleaned_response.strip()
                
                ranked_products = json.loads(cleaned_response)
                if not isinstance(ranked_products, list):
                    raise AIRequestError("AI response is not a list")

                # Validate each product has required fields
                for product in ranked_products:
                    if not isinstance(product, dict):
                        raise AIRequestError("Product in response is not a dictionary")
                    if "product_id" not in product:
                        raise AIRequestError("Product missing product_id field")
                    if "reason" not in product:
                        raise AIRequestError("Product missing reason field")

                return ranked_products

            except json.JSONDecodeError as e:
                raise AIRequestError(f"Failed to parse AI response as JSON: {e}")

        except asyncio.TimeoutError:
            raise AITimeoutError(f"AI request timed out after {timeout_ms}ms")
        except Exception as e:
            if "API_KEY" in str(e):
                raise AIConfigError(f"Gemini API key error: {e}")
            elif "timeout" in str(e).lower():
                raise AITimeoutError(f"AI request timed out: {e}")
            else:
                raise AIRequestError(f"AI request failed: {e}")

    async def _generate_content(self, prompt: str) -> str:
        """Generate content from Gemini with proper error handling."""
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            if "API_KEY" in str(e):
                raise AIConfigError(f"Gemini API key error: {e}")
            elif "quota" in str(e).lower() or "rate" in str(e).lower():
                raise AIRequestError(f"Gemini rate limit/quota exceeded: {e}")
            else:
                raise AIRequestError(f"Gemini API error: {e}")
