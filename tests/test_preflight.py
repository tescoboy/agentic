"""Tests for preflight checks."""

import pytest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

from app.services.preflight import (
    check_database_file,
    check_database_tables,
    check_reference_repositories,
    check_default_prompt_file,
    check_api_key,
    check_tenants,
    run_checks,
    get_overall_status,
    get_status_summary,
)


class TestPreflightChecks:
    """Test preflight check functions."""

    def test_check_database_file_exists_and_writable(self):
        """Test database file check when file exists and is writable."""
        with patch("app.services.preflight.settings") as mock_settings:
            mock_settings.database_url = "sqlite:///./test.db"

            with patch("pathlib.Path.exists", return_value=True):
                with patch("os.access", return_value=True):
                    result = check_database_file()

                    assert result["status"] == "ok"
                    assert "accessible and writable" in result["message"]

    def test_check_database_file_not_writable(self):
        """Test database file check when file exists but not writable."""
        with patch("app.services.preflight.settings") as mock_settings:
            mock_settings.database_url = "sqlite:///./test.db"

            with patch("pathlib.Path.exists", return_value=True):
                with patch("os.access", return_value=False):
                    result = check_database_file()

                    assert result["status"] == "fail"
                    assert "not writable" in result["message"]

    def test_check_database_file_not_exists_but_directory_writable(self):
        """Test database file check when file doesn't exist but directory is writable."""
        with patch("app.services.preflight.settings") as mock_settings:
            mock_settings.database_url = "sqlite:///./test.db"

            with patch("pathlib.Path.exists", return_value=False):
                with patch("os.access", return_value=True):
                    result = check_database_file()

                    assert result["status"] == "warn"
                    assert (
                        "does not exist but directory is writable" in result["message"]
                    )

    def test_check_database_tables_all_exist(self):
        """Test database tables check when all tables exist."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn

        # Mock successful table checks
        mock_conn.execute.return_value.fetchone.return_value = ["table_name"]

        with patch("app.db.get_engine", return_value=mock_engine):
            result = check_database_tables()

            assert result["status"] == "ok"
            assert "All required database tables exist" in result["message"]

    def test_check_database_tables_missing_tables(self):
        """Test database tables check when some tables are missing."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn

        # Mock missing tables
        mock_conn.execute.return_value.fetchone.side_effect = [
            None,
            ["tenants"],
            None,
            ["products"],
        ]

        with patch("app.db.get_engine", return_value=mock_engine):
            result = check_database_tables()

            assert result["status"] == "fail"
            assert "Missing database tables" in result["message"]
            assert "agent_settings" in result["message"]

    def test_check_reference_repositories_all_exist(self):
        """Test reference repositories check when all exist."""
        with patch("pathlib.Path.exists", return_value=True):
            result = check_reference_repositories()

            assert result["status"] == "ok"
            assert "All reference repositories are present" in result["message"]

    def test_check_reference_repositories_missing(self):
        """Test reference repositories check when some are missing."""
        with patch("pathlib.Path.exists", side_effect=[True, False]):
            result = check_reference_repositories()

            assert result["status"] == "warn"
            assert "Missing reference repositories" in result["message"]
            assert "AdCP reference repository" in result["message"]

    def test_check_default_prompt_file_exists_and_readable(self):
        """Test default prompt file check when file exists and is readable."""
        mock_path = MagicMock()
        mock_path.exists.return_value = True

        with patch("pathlib.Path", return_value=mock_path):
            with patch("os.access", return_value=True):
                with patch("builtins.open", mock_open(read_data="prompt content")):
                    result = check_default_prompt_file()

                    assert result["status"] == "ok"
                    assert "readable and has content" in result["message"]

    def test_check_default_prompt_file_not_exists(self):
        """Test default prompt file check when file doesn't exist."""
        mock_path = MagicMock()
        mock_path.exists.return_value = False

        with patch("pathlib.Path", return_value=mock_path):
            result = check_default_prompt_file()

            assert result["status"] == "ok"
            assert "readable and has content" in result["message"]

    def test_check_api_key_present(self):
        """Test API key check when key is present."""
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test_key"}):
            result = check_api_key()

            assert result["status"] == "ok"
            assert "configured" in result["message"]

    def test_check_api_key_missing(self):
        """Test API key check when key is missing."""
        with patch.dict("os.environ", {}, clear=True):
            result = check_api_key()

            assert result["status"] == "warn"
            assert "not set" in result["message"]

    def test_check_api_key_empty(self):
        """Test API key check when key is empty."""
        with patch.dict("os.environ", {"GEMINI_API_KEY": ""}):
            result = check_api_key()

            assert result["status"] == "warn"
            assert "not set" in result["message"]

    def test_check_tenants_exist(self):
        """Test tenants check when tenants exist."""
        mock_session = MagicMock()
        mock_repo = MagicMock()
        mock_repo.list_all.return_value = [MagicMock(), MagicMock()]

        with patch("app.db.get_session", return_value=mock_session):
            with patch(
                "app.repositories.tenants.TenantRepository", return_value=mock_repo
            ):
                result = check_tenants()

                assert result["status"] == "ok"
                assert "2 tenant(s) found" in result["message"]

    def test_check_tenants_none_exist(self):
        """Test tenants check when no tenants exist."""
        mock_session = MagicMock()
        mock_repo = MagicMock()
        mock_repo.list_all.return_value = []

        with patch("app.db.get_session", return_value=mock_session):
            with patch(
                "app.repositories.tenants.TenantRepository", return_value=mock_repo
            ):
                result = check_tenants()

                assert result["status"] == "warn"
                assert "No tenants found" in result["message"]

    def test_run_checks_returns_all_checks(self):
        """Test that run_checks returns all expected checks."""
        with patch(
            "app.services.preflight.check_database_file",
            return_value={"status": "ok", "message": "test"},
        ):
            with patch(
                "app.services.preflight.check_database_tables",
                return_value={"status": "ok", "message": "test"},
            ):
                with patch(
                    "app.services.preflight.check_reference_repositories",
                    return_value={"status": "ok", "message": "test"},
                ):
                    with patch(
                        "app.services.preflight.check_default_prompt_file",
                        return_value={"status": "ok", "message": "test"},
                    ):
                        with patch(
                            "app.services.preflight.check_api_key",
                            return_value={"status": "ok", "message": "test"},
                        ):
                            with patch(
                                "app.services.preflight.check_tenants",
                                return_value={"status": "ok", "message": "test"},
                            ):
                                result = run_checks()

                                expected_keys = [
                                    "database_file",
                                    "database_tables",
                                    "reference_repositories",
                                    "default_prompt_file",
                                    "api_key",
                                    "tenants",
                                ]
                                assert all(key in result for key in expected_keys)

    def test_get_overall_status_all_ok(self):
        """Test overall status when all checks are ok."""
        checks = {"check1": {"status": "ok"}, "check2": {"status": "ok"}}

        result = get_overall_status(checks)
        assert result == "ok"

    def test_get_overall_status_with_warnings(self):
        """Test overall status when some checks have warnings."""
        checks = {"check1": {"status": "ok"}, "check2": {"status": "warn"}}

        result = get_overall_status(checks)
        assert result == "warn"

    def test_get_overall_status_with_failures(self):
        """Test overall status when some checks fail."""
        checks = {"check1": {"status": "ok"}, "check2": {"status": "fail"}}

        result = get_overall_status(checks)
        assert result == "fail"

    def test_get_status_summary(self):
        """Test status summary counting."""
        checks = {
            "check1": {"status": "ok"},
            "check2": {"status": "warn"},
            "check3": {"status": "fail"},
            "check4": {"status": "ok"},
        }

        result = get_status_summary(checks)
        assert result == {"ok": 2, "warn": 1, "fail": 1}
