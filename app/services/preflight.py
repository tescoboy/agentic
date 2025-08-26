"""Preflight checks for system readiness and configuration."""

import os
import sqlite3
from pathlib import Path
from typing import Dict, Any

from ..config import settings


def check_database_file() -> Dict[str, Any]:
    """Check if database file is reachable and writable."""
    try:
        # Extract SQLite path from DATABASE_URL
        db_url = settings.database_url
        if db_url.startswith("sqlite:///"):
            db_path = db_url.replace("sqlite:///", "")
            if db_path.startswith("./"):
                db_path = db_path[2:]  # Remove ./ prefix

        db_file = Path(db_path)

        # Check if file exists and is writable
        if db_file.exists():
            if os.access(db_file, os.R_OK | os.W_OK):
                return {
                    "status": "ok",
                    "message": f"Database file {db_path} is accessible and writable",
                }
            else:
                return {
                    "status": "fail",
                    "message": f"Database file {db_path} exists but is not writable",
                }
        else:
            # Check if directory is writable for file creation
            db_dir = db_file.parent
            if os.access(db_dir, os.W_OK):
                return {
                    "status": "warn",
                    "message": f"Database file {db_path} does not exist but directory is writable",
                }
            else:
                return {
                    "status": "fail",
                    "message": f"Database directory {db_dir} is not writable",
                }
    except Exception as e:
        return {"status": "fail", "message": f"Database check failed: {str(e)}"}


def check_database_tables() -> Dict[str, Any]:
    """Check if required database tables exist."""
    try:
        from ..db import get_engine
        from sqlalchemy import text

        engine = get_engine()

        with engine.connect() as conn:
            # Check for core tables
            tables = ["tenant", "product", "agentsettings", "externalagent"]
            missing_tables = []

            for table in tables:
                result = conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table' AND name=:table_name"),
                    {"table_name": table}
                )
                if not result.fetchone():
                    missing_tables.append(table)

            if not missing_tables:
                return {"status": "ok", "message": "All required database tables exist"}
            else:
                return {
                    "status": "fail",
                    "message": f"Missing database tables: {', '.join(missing_tables)}",
                }
    except Exception as e:
        return {"status": "fail", "message": f"Database tables check failed: {str(e)}"}


def check_reference_repositories() -> Dict[str, Any]:
    """Check if reference repositories exist."""
    reference_paths = [
        ("/reference/salesagent", "Sales Agent reference repository"),
        ("/reference/adcp", "AdCP reference repository"),
    ]

    missing_refs = []
    for ref_path, ref_name in reference_paths:
        if not Path(ref_path).exists():
            missing_refs.append(ref_name)

    if not missing_refs:
        return {"status": "ok", "message": "All reference repositories are present"}
    else:
        return {
            "status": "warn",
            "message": f"Missing reference repositories: {', '.join(missing_refs)}. Clone them for full functionality.",
        }


def check_default_prompt_file() -> Dict[str, Any]:
    """Check if default sales prompt file is readable."""
    prompt_path = Path("app/resources/default_sales_prompt.txt")

    if not prompt_path.exists():
        return {
            "status": "fail",
            "message": "Default sales prompt file not found at app/resources/default_sales_prompt.txt",
        }

    if not os.access(prompt_path, os.R_OK):
        return {
            "status": "fail",
            "message": "Default sales prompt file exists but is not readable",
        }

    # Check if file has content
    try:
        with open(prompt_path, "r") as f:
            content = f.read().strip()
            if not content:
                return {
                    "status": "fail",
                    "message": "Default sales prompt file is empty",
                }
    except Exception as e:
        return {
            "status": "fail",
            "message": f"Error reading default sales prompt file: {str(e)}",
        }

    return {
        "status": "ok",
        "message": "Default sales prompt file is readable and has content",
    }


def check_api_key() -> Dict[str, Any]:
    """Check if GEMINI_API_KEY is present."""
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return {
            "status": "warn",
            "message": "GEMINI_API_KEY not set. AI ranking will fail.",
        }

    if len(api_key.strip()) == 0:
        return {
            "status": "warn",
            "message": "GEMINI_API_KEY is empty. AI ranking will fail.",
        }

    return {"status": "ok", "message": "GEMINI_API_KEY is configured"}


def check_tenants() -> Dict[str, Any]:
    """Check if at least one tenant exists."""
    try:
        from ..db import get_session
        from ..repositories.tenants import TenantRepository

        with get_session() as session:
            repo = TenantRepository(session)
            tenants = repo.list_all()

            if tenants:
                return {"status": "ok", "message": f"{len(tenants)} tenant(s) found"}
            else:
                return {
                    "status": "warn",
                    "message": "No tenants found. Create at least one tenant to use the system.",
                }
    except Exception as e:
        return {"status": "fail", "message": f"Tenant check failed: {str(e)}"}


def run_checks() -> Dict[str, Dict[str, Any]]:
    """Run all preflight checks and return results."""
    checks = {
        "database_file": check_database_file(),
        "database_tables": check_database_tables(),
        "reference_repositories": check_reference_repositories(),
        "default_prompt_file": check_default_prompt_file(),
        "api_key": check_api_key(),
        "tenants": check_tenants(),
    }

    return checks


def get_overall_status(checks: Dict[str, Dict[str, Any]]) -> str:
    """Determine overall status from individual checks."""
    if any(check["status"] == "fail" for check in checks.values()):
        return "fail"
    elif any(check["status"] == "warn" for check in checks.values()):
        return "warn"
    else:
        return "ok"


def get_status_summary(checks: Dict[str, Dict[str, Any]]) -> Dict[str, int]:
    """Get count of each status type."""
    summary = {"ok": 0, "warn": 0, "fail": 0}
    for check in checks.values():
        summary[check["status"]] += 1
    return summary
