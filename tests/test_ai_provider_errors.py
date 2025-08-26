"""Tests for AI provider error handling."""

import pytest
from unittest.mock import patch, MagicMock

from app.ai.errors import AIConfigError, AIRequestError, AITimeoutError
from app.ai.gemini import GeminiProvider
from app.config import settings


def test_gemini_provider_missing_api_key():
    """Test Gemini provider raises AIConfigError when API key is missing."""
    with patch("app.config.settings.gemini_api_key", None):
        with pytest.raises(AIConfigError) as exc_info:
            GeminiProvider()

        assert "GEMINI_API_KEY not set" in str(exc_info.value)


def test_gemini_provider_timeout_error():
    """Test Gemini provider raises AITimeoutError on timeout."""
    with patch("app.config.settings.gemini_api_key", "fake-api-key"):
        provider = GeminiProvider()

    with patch("asyncio.get_event_loop") as mock_loop:
        mock_loop.return_value.run_until_complete.side_effect = TimeoutError(
            "Request timed out"
        )

        with pytest.raises(AITimeoutError) as exc_info:
            provider.rank_products(
                brief="Test brief",
                prompt="Test prompt",
                products=[{"product_id": "test", "name": "Test"}],
                model_name="gemini-1.5-pro",
                timeout_ms=5000,
            )

        assert "timed out" in str(exc_info.value)


def test_gemini_provider_invalid_json_response():
    """Test Gemini provider raises AIRequestError on invalid JSON response."""
    with patch("app.config.settings.gemini_api_key", "fake-api-key"):
        provider = GeminiProvider()

    with patch("asyncio.get_event_loop") as mock_loop:
        mock_loop.return_value.run_until_complete.return_value = "Invalid JSON"

        with pytest.raises(AIRequestError) as exc_info:
            provider.rank_products(
                brief="Test brief",
                prompt="Test prompt",
                products=[{"product_id": "test", "name": "Test"}],
                model_name="gemini-1.5-pro",
                timeout_ms=5000,
            )

        assert "Failed to parse AI response as JSON" in str(exc_info.value)


def test_gemini_provider_non_list_response():
    """Test Gemini provider raises AIRequestError when response is not a list."""
    with patch("app.config.settings.gemini_api_key", "fake-api-key"):
        provider = GeminiProvider()

    with patch("asyncio.get_event_loop") as mock_loop:
        mock_loop.return_value.run_until_complete.return_value = '{"not": "a list"}'

        with pytest.raises(AIRequestError) as exc_info:
            provider.rank_products(
                brief="Test brief",
                prompt="Test prompt",
                products=[{"product_id": "test", "name": "Test"}],
                model_name="gemini-1.5-pro",
                timeout_ms=5000,
            )

        assert "AI response is not a list" in str(exc_info.value)


def test_gemini_provider_missing_product_id():
    """Test Gemini provider raises AIRequestError when product missing product_id."""
    with patch("app.config.settings.gemini_api_key", "fake-api-key"):
        provider = GeminiProvider()

    with patch("asyncio.get_event_loop") as mock_loop:
        mock_loop.return_value.run_until_complete.return_value = '[{"reason": "test"}]'

        with pytest.raises(AIRequestError) as exc_info:
            provider.rank_products(
                brief="Test brief",
                prompt="Test prompt",
                products=[{"product_id": "test", "name": "Test"}],
                model_name="gemini-1.5-pro",
                timeout_ms=5000,
            )

        assert "Product missing product_id field" in str(exc_info.value)


def test_gemini_provider_missing_reason():
    """Test Gemini provider raises AIRequestError when product missing reason."""
    with patch("app.config.settings.gemini_api_key", "fake-api-key"):
        provider = GeminiProvider()

    with patch("asyncio.get_event_loop") as mock_loop:
        mock_loop.return_value.run_until_complete.return_value = (
            '[{"product_id": "test"}]'
        )

        with pytest.raises(AIRequestError) as exc_info:
            provider.rank_products(
                brief="Test brief",
                prompt="Test prompt",
                products=[{"product_id": "test", "name": "Test"}],
                model_name="gemini-1.5-pro",
                timeout_ms=5000,
            )

        assert "Product missing reason field" in str(exc_info.value)


def test_gemini_provider_successful_response():
    """Test Gemini provider returns valid response."""
    with patch("app.config.settings.gemini_api_key", "fake-api-key"):
        provider = GeminiProvider()

    valid_response = """[
        {"product_id": "test1", "reason": "Matches brief", "score": 0.8},
        {"product_id": "test2", "reason": "Partial match", "score": 0.6}
    ]"""

    with patch("asyncio.get_event_loop") as mock_loop:
        mock_loop.return_value.run_until_complete.return_value = valid_response

        result = provider.rank_products(
            brief="Test brief",
            prompt="Test prompt",
            products=[{"product_id": "test1"}, {"product_id": "test2"}],
            model_name="gemini-1.5-pro",
            timeout_ms=5000,
        )

        assert len(result) == 2
        assert result[0]["product_id"] == "test1"
        assert result[0]["reason"] == "Matches brief"
        assert result[0]["score"] == 0.8
        assert result[1]["product_id"] == "test2"
        assert result[1]["reason"] == "Partial match"
        assert result[1]["score"] == 0.6


def test_gemini_provider_api_error():
    """Test Gemini provider raises AIRequestError on API errors."""
    with patch("app.config.settings.gemini_api_key", "fake-api-key"):
        provider = GeminiProvider()

    with patch("asyncio.get_event_loop") as mock_loop:
        mock_loop.return_value.run_until_complete.side_effect = Exception("API Error")

        with pytest.raises(AIRequestError) as exc_info:
            provider.rank_products(
                brief="Test brief",
                prompt="Test prompt",
                products=[{"product_id": "test", "name": "Test"}],
                model_name="gemini-1.5-pro",
                timeout_ms=5000,
            )

        assert "AI request failed" in str(exc_info.value)
