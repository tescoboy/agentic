"""Buyer UI routes for brief input, agent selection, and results display."""

import httpx
from typing import List

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from ..config import settings
from ..repositories.tenants import TenantRepository, get_tenant_repo
from ..repositories.external_agents import (
    ExternalAgentRepository,
    get_external_agent_repo,
)


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/buyer", response_class=HTMLResponse)
async def show_buyer_page(
    request: Request,
    tenant_repo: TenantRepository = Depends(get_tenant_repo),
    external_agent_repo: ExternalAgentRepository = Depends(get_external_agent_repo),
):
    """Show buyer page with brief input and agent selection."""
    # Get all tenants and enabled external agents
    tenants = tenant_repo.list_all()
    external_agents = external_agent_repo.list_enabled()

    return templates.TemplateResponse(
        "buyer/index.html",
        {
            "request": request,
            "tenants": tenants,
            "external_agents": external_agents,
            "results": None,
            "error": None,
            "config": request.app.state.settings,
        },
    )


@router.post("/buyer", response_class=HTMLResponse)
async def submit_buyer_brief(
    request: Request,
    brief: str = Form(...),
    internal_tenants: List[str] = Form(default=[]),
    external_agents: List[str] = Form(default=[]),
    timeout_ms: int = Form(default=None),
    tenant_repo: TenantRepository = Depends(get_tenant_repo),
    external_agent_repo: ExternalAgentRepository = Depends(get_external_agent_repo),
):
    """Submit buyer brief and orchestrate across selected agents."""
    # Validate brief
    if not brief or not brief.strip():
        tenants = tenant_repo.list_all()
        external_agents_list = external_agent_repo.list_enabled()
        return templates.TemplateResponse(
            "buyer/index.html",
            {
                "request": request,
                "tenants": tenants,
                "external_agents": external_agents_list,
                "results": None,
                "error": "Brief is required",
                "config": request.app.state.settings,
            },
        )

    # Validate at least one agent selected
    if not internal_tenants and not external_agents:
        tenants = tenant_repo.list_all()
        external_agents_list = external_agent_repo.list_enabled()
        return templates.TemplateResponse(
            "buyer/index.html",
            {
                "request": request,
                "tenants": tenants,
                "external_agents": external_agents_list,
                "results": None,
                "error": "Please select at least one agent",
                "config": request.app.state.settings,
            },
        )

    # Build orchestrator request
    orchestrator_request = {
        "brief": brief.strip(),
        "internal_tenant_slugs": internal_tenants if internal_tenants else None,
        "external_urls": external_agents if external_agents else None,
    }

    # Add timeout if provided
    if timeout_ms is not None and timeout_ms > 0:
        orchestrator_request["timeout_ms"] = timeout_ms

    try:
        # Call orchestrator via HTTP
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.service_base_url}/orchestrate",
                json=orchestrator_request,
                timeout=30.0,  # 30 second timeout for the entire orchestration
            )

            if response.status_code == 200:
                results = response.json()
                # Get fresh data for template
                tenants = tenant_repo.list_all()
                external_agents_list = external_agent_repo.list_enabled()

                return templates.TemplateResponse(
                    "buyer/index.html",
                    {
                        "request": request,
                        "tenants": tenants,
                        "external_agents": external_agents_list,
                        "orchestrator_results": results,
                        "error": None,
                        "submitted_brief": brief.strip(),
                        "selected_internal": internal_tenants,
                        "selected_external": external_agents,
                        "config": request.app.state.settings,
                    },
                )
            else:
                # Handle orchestrator errors
                error_detail = response.json().get("detail", "Orchestration failed")
                tenants = tenant_repo.list_all()
                external_agents_list = external_agent_repo.list_enabled()

                return templates.TemplateResponse(
                    "buyer/index.html",
                    {
                        "request": request,
                        "tenants": tenants,
                        "external_agents": external_agents_list,
                        "results": None,
                        "error": f"Orchestration error: {error_detail}",
                        "config": request.app.state.settings,
                    },
                )

    except httpx.TimeoutException:
        tenants = tenant_repo.list_all()
        external_agents_list = external_agent_repo.list_enabled()
        return templates.TemplateResponse(
            "buyer/index.html",
            {
                "request": request,
                "tenants": tenants,
                "external_agents": external_agents_list,
                "results": None,
                "error": "Orchestration timed out. Please try again.",
                "config": request.app.state.settings,
            },
        )
    except Exception as e:
        tenants = tenant_repo.list_all()
        external_agents_list = external_agent_repo.list_enabled()
        return templates.TemplateResponse(
            "buyer/index.html",
            {
                "request": request,
                "tenants": tenants,
                "external_agents": external_agents_list,
                "results": None,
                "error": f"Unexpected error: {str(e)}",
                "config": request.app.state.settings,
            },
        )
