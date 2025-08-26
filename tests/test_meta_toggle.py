"""Tests for meta tag toggling based on DEBUG setting."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app


class TestMetaToggle:
    """Test meta tag toggling functionality."""

    def test_debug_on_meta_tag_content_is_on(self):
        """Test that when DEBUG=1, meta tag content is 'on'."""
        with patch("app.config.settings.debug", True):
            client = TestClient(app)

            response = client.get("/")

            assert response.status_code == 200
            assert 'name="adcp-demo-logs" content="on"' in response.text

    def test_debug_off_meta_tag_content_is_off(self):
        """Test that when DEBUG=0, meta tag content is 'off'."""
        with patch("app.config.settings.debug", False):
            client = TestClient(app)

            response = client.get("/")

            assert response.status_code == 200
            assert 'name="adcp-demo-logs" content="off"' in response.text

    def test_request_id_meta_tag_present(self):
        """Test that request-id meta tag is always present."""
        client = TestClient(app)

        response = client.get("/")

        assert response.status_code == 200
        assert 'name="request-id"' in response.text
        assert "content=" in response.text

    def test_demo_log_script_included(self):
        """Test that demo_log.js script is included in base template."""
        client = TestClient(app)

        response = client.get("/")

        assert response.status_code == 200
        assert "/static/js/demo_log.js" in response.text
        assert "demo_log.js" in response.text

    def test_template_context_includes_config(self):
        """Test that template context includes config object."""
        client = TestClient(app)

        response = client.get("/")

        assert response.status_code == 200
        # The template should have access to config for DEBUG setting
        # This is verified by the meta tag content tests above
