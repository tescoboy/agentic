"""Orchestrator routes for fanning out buyer briefs to multiple agents."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..services.orchestrator import orchestrate
from ..repositories.tenants import TenantRepository, get_tenant_repo
from ..repositories.external_agents import (
    ExternalAgentRepository,
    get_external_agent_repo,
)


router = APIRouter()


class OrchestrateRequest(BaseModel):
    """Request model for orchestration endpoint."""

    brief: str
    internal_tenant_slugs: Optional[List[str]] = None
    external_urls: Optional[List[str]] = None
    timeout_ms: Optional[int] = None


class OrchestrateResponse(BaseModel):
    """Response model for orchestration endpoint."""

    results: List[dict]
    context_id: str
    total_agents: int
    timeout_ms: int


@router.post("/orchestrate", response_model=OrchestrateResponse)
async def orchestrate_brief(
    request: OrchestrateRequest,
    tenant_repo: TenantRepository = Depends(get_tenant_repo),
    external_agent_repo: ExternalAgentRepository = Depends(get_external_agent_repo),
):
    """
    Orchestrate a buyer brief across multiple agents using AdCP protocol.

    If internal_tenant_slugs or external_urls are omitted, defaults to all available agents.
    """
    # Validate brief
    if not request.brief or not request.brief.strip():
        raise HTTPException(status_code=400, detail="Brief must be non-empty")

    # Get internal tenant slugs (default to all if not specified)
    internal_slugs = request.internal_tenant_slugs
    if internal_slugs is None:
        tenants = tenant_repo.list_all()
        internal_slugs = [tenant.slug for tenant in tenants]

    # Get external URLs (default to all enabled if not specified)
    external_urls = request.external_urls
    if external_urls is None:
        external_agents = external_agent_repo.list_enabled()
        external_urls = [agent.base_url for agent in external_agents]

    # Validate that we have at least one agent
    if not internal_slugs and not external_urls:
        raise HTTPException(
            status_code=400,
            detail="No agents available. Please ensure at least one tenant exists or external agent is configured.",
        )

    try:
        # Call orchestrator service
        result = await orchestrate(
            brief=request.brief,
            internal_tenant_slugs=internal_slugs,
            external_urls=external_urls,
            timeout_ms=request.timeout_ms,
        )

        return OrchestrateResponse(**result)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Orchestration failed: {str(e)}")
