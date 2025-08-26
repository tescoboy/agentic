"""Tests for environment configuration."""

import os
from unittest.mock import patch

from app.config import Settings


def test_missing_ai_key_warning():
    """Test that missing AI key returns helpful warning message."""
    with patch.dict(os.environ, {}, clear=True):
        settings = Settings()
        warning = settings.missing_ai_key_warning()

        assert "WARNING" in warning
        assert "GEMINI_API_KEY" in warning
        assert "not set" in warning


def test_ai_key_configured():
    """Test that AI key configuration is detected correctly."""
    with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}, clear=True):
        settings = Settings()
        assert settings.is_ai_configured() is True
        assert settings.missing_ai_key_warning() == ""


def test_ai_key_not_configured():
    """Test that missing AI key is detected correctly."""
    with patch.dict(os.environ, {}, clear=True):
        settings = Settings()
        assert settings.is_ai_configured() is False
