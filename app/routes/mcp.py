"""MCP endpoints for internal sales agents with AdCP contract.

Source files used for AdCP contract alignment:
- reference/adcp/src/schemas.py (request/response shapes)
- reference/salesagent/src/core/schemas.py (product ranking format)
"""

import os
import subprocess
from typing import Dict, Any, List

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlmodel import Session

from ..config import settings
from ..services.sales_agent import evaluate_brief
from ..repositories.tenants import TenantRepository, get_tenant_repo
from ..repositories.products import ProductRepository
from ..repositories.agent_settings import AgentSettingsRepository
from ..deps import get_db_session


router = APIRouter()


class AdCPRankingRequest(BaseModel):
    """AdCP ranking request model."""

    brief: str
    context_id: str = None


class AdCPRankingResponse(BaseModel):
    """AdCP ranking response model."""

    items: List[Dict[str, Any]]


class AdCPErrorResponse(BaseModel):
    """AdCP error response model."""

    error: Dict[str, Any]


def get_product_repo(session: Session = Depends(get_db_session)) -> ProductRepository:
    """Get product repository dependency."""
    return ProductRepository(session)


def get_agent_settings_repo(
    session: Session = Depends(get_db_session),
) -> AgentSettingsRepository:
    """Get agent settings repository dependency."""
    return AgentSettingsRepository(session)


def get_git_commit_hash() -> str:
    """Get current git commit hash for traceability."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    return "unknown"


@router.get("/mcp/")
async def get_mcp_info():
    """Get MCP service information and capabilities."""
    adcp_version = os.getenv("ADCP_VERSION", "adcp-demo-0.1")
    commit_hash = get_git_commit_hash()

    return {
        "service": "AdCP Demo Orchestrator",
        "adcp_version": adcp_version,
        "commit_hash": commit_hash,
        "capabilities": ["ranking"],
    }


@router.post("/mcp/agents/{tenant_slug}/rank")
async def rank_products(
    tenant_slug: str,
    request: AdCPRankingRequest,
    tenant_repo: TenantRepository = Depends(get_tenant_repo),
    product_repo: ProductRepository = Depends(get_product_repo),
    agent_settings_repo: AgentSettingsRepository = Depends(get_agent_settings_repo),
):
    """
    Rank products for a tenant using AdCP contract.

    Validates tenant exists, brief is provided, and tenant has products.
    Calls sales_agent.evaluate_brief and returns AdCP-compliant response.
    """
    # Validate tenant exists
    tenant = tenant_repo.get_by_slug(tenant_slug)
    if not tenant:
        return JSONResponse(
            status_code=404,
            content={
                "error": {
                    "type": "invalid_request",
                    "message": f"Tenant '{tenant_slug}' not found",
                    "status": 404,
                }
            },
        )

    # Validate brief is present and non-empty
    if not request.brief or not request.brief.strip():
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "type": "invalid_request",
                    "message": "Brief is required and must be non-empty",
                    "status": 400,
                }
            },
        )

    # Check if tenant has products
    products = product_repo.list_by_tenant(tenant.id)
    if not products:
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "type": "invalid_request",
                    "message": f"No products found for tenant '{tenant_slug}'. Please add products before using AI evaluation.",
                    "status": 422,
                }
            },
        )

    try:
        # Call sales agent service
        results = await evaluate_brief(
            tenant_id=tenant.id,
            brief=request.brief.strip(),
            agent_settings_repo=agent_settings_repo,
            product_repo=product_repo,
            tenant_repo=tenant_repo,
        )

        # Return AdCP-compliant response
        return {"items": results}

    except Exception as e:
        # Map exceptions to AdCP error responses
        error_type = "internal"
        status_code = 500

        # Check for specific AI exceptions
        if "AIConfigError" in str(type(e)) or "missing" in str(e).lower():
            error_type = "ai_config_error"
            status_code = 500
        elif "AITimeoutError" in str(type(e)) or "timeout" in str(e).lower():
            error_type = "timeout"
            status_code = 408
        elif "AIRequestError" in str(type(e)) or "request" in str(e).lower():
            error_type = "ai_request_error"
            status_code = 502

        return JSONResponse(
            status_code=status_code,
            content={
                "error": {"type": error_type, "message": str(e), "status": status_code}
            },
        )
