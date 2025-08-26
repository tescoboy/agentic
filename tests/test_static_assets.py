"""Tests for static assets serving."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


class TestStaticAssets:
    """Test static file serving."""

    def test_demo_log_js_returns_200(self):
        """Test that demo_log.js returns 200 with correct content type."""
        client = TestClient(app)

        response = client.get("/static/js/demo_log.js")

        assert response.status_code == 200
        assert "javascript" in response.headers["content-type"]
        assert "AdCP Demo Console Logger" in response.text

    def test_demo_log_js_contains_expected_functions(self):
        """Test that demo_log.js contains expected functionality."""
        client = TestClient(app)

        response = client.get("/static/js/demo_log.js")

        assert response.status_code == 200
        js_content = response.text

        # Check for key functions and variables
        assert "LOG_PREFIX" in js_content
        assert "REQUEST_ID_META" in js_content
        assert "LOGS_ENABLED_META" in js_content
        assert "FORM_LOG_ATTR" in js_content
        assert "getMetaContent" in js_content
        assert "isLoggingEnabled" in js_content
        assert "logPageLoad" in js_content
        assert "setupFormLogging" in js_content

    def test_static_files_not_found_returns_404(self):
        """Test that non-existent static files return 404."""
        client = TestClient(app)

        response = client.get("/static/js/nonexistent.js")

        assert response.status_code == 404

    def test_static_directory_structure(self):
        """Test that static directory structure is correct."""
        import os
        import pathlib

        static_dir = pathlib.Path("app/static")
        js_dir = static_dir / "js"
        demo_log_file = js_dir / "demo_log.js"

        assert static_dir.exists()
        assert js_dir.exists()
        assert demo_log_file.exists()
        assert demo_log_file.is_file()
