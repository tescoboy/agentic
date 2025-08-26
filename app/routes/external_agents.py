"""External agents CRUD routes for managing MCP endpoint configuration."""

from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from ..models.external_agent import ExternalAgent
from ..repositories.external_agents import (
    ExternalAgentRepository,
    get_external_agent_repo,
)
from ..db import get_session


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/external-agents", response_class=HTMLResponse)
async def list_external_agents(
    request: Request,
    external_agent_repo: ExternalAgentRepository = Depends(get_external_agent_repo),
):
    """List all external agents."""
    agents = external_agent_repo.list_all()
    return templates.TemplateResponse(
        "external_agents/index.html", {"request": request, "agents": agents, "config": request.app.state.settings}
    )


@router.get("/external-agents/add", response_class=HTMLResponse)
async def show_add_external_agent_form(request: Request):
    """Show form to add a new external agent."""
    return templates.TemplateResponse(
        "external_agents/form.html",
        {"request": request, "agent": None, "is_edit": False, "config": request.app.state.settings},
    )


@router.post("/external-agents/add", response_class=HTMLResponse)
async def add_external_agent(
    request: Request,
    name: str = Form(...),
    base_url: str = Form(...),
    enabled: bool = Form(True),
    external_agent_repo: ExternalAgentRepository = Depends(get_external_agent_repo),
):
    """Add a new external agent."""
    # Validate inputs
    if not name or not name.strip():
        return templates.TemplateResponse(
            "external_agents/form.html",
            {
                "request": request,
                "agent": None,
                "is_edit": False,
                "error": "Name is required",
                "config": request.app.state.settings,
            },
        )

    if not base_url or not base_url.strip():
        return templates.TemplateResponse(
            "external_agents/form.html",
            {
                "request": request,
                "agent": None,
                "is_edit": False,
                "error": "Base URL is required",
                "config": request.app.state.settings,
            },
        )

    # Create agent
    agent = ExternalAgent(name=name.strip(), base_url=base_url.strip(), enabled=enabled)

    try:
        external_agent_repo.create(agent)
        return RedirectResponse(
            url="/external-agents?message=External agent added successfully",
            status_code=302,
        )
    except Exception as e:
        return templates.TemplateResponse(
            "external_agents/form.html",
            {
                "request": request,
                "agent": None,
                "is_edit": False,
                "error": f"Failed to create agent: {str(e)}",
                "config": request.app.state.settings,
            },
        )


@router.get("/external-agents/{agent_id}/edit", response_class=HTMLResponse)
async def show_edit_external_agent_form(
    request: Request,
    agent_id: int,
    external_agent_repo: ExternalAgentRepository = Depends(get_external_agent_repo),
):
    """Show form to edit an external agent."""
    agent = external_agent_repo.get_by_id(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="External agent not found")

    return templates.TemplateResponse(
        "external_agents/form.html",
        {"request": request, "agent": agent, "is_edit": True, "config": request.app.state.settings},
    )


@router.post("/external-agents/{agent_id}/edit", response_class=HTMLResponse)
async def edit_external_agent(
    request: Request,
    agent_id: int,
    name: str = Form(...),
    base_url: str = Form(...),
    enabled: bool = Form(True),
    external_agent_repo: ExternalAgentRepository = Depends(get_external_agent_repo),
):
    """Edit an external agent."""
    agent = external_agent_repo.get_by_id(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="External agent not found")

    # Validate inputs
    if not name or not name.strip():
        return templates.TemplateResponse(
            "external_agents/form.html",
            {
                "request": request,
                "agent": agent,
                "is_edit": True,
                "error": "Name is required",
                "config": request.app.state.settings,
            },
        )

    if not base_url or not base_url.strip():
        return templates.TemplateResponse(
            "external_agents/form.html",
            {
                "request": request,
                "agent": agent,
                "is_edit": True,
                "error": "Base URL is required",
                "config": request.app.state.settings,
            },
        )

    # Update agent
    agent.name = name.strip()
    agent.base_url = base_url.strip()
    agent.enabled = enabled

    try:
        external_agent_repo.update(agent)
        return RedirectResponse(
            url="/external-agents?message=External agent updated successfully",
            status_code=302,
        )
    except Exception as e:
        return templates.TemplateResponse(
            "external_agents/form.html",
            {
                "request": request,
                "agent": agent,
                "is_edit": True,
                "error": f"Failed to update agent: {str(e)}",
                "config": request.app.state.settings,
            },
        )


@router.post("/external-agents/{agent_id}/delete", response_class=HTMLResponse)
async def delete_external_agent(
    request: Request,
    agent_id: int,
    external_agent_repo: ExternalAgentRepository = Depends(get_external_agent_repo),
):
    """Delete an external agent."""
    success = external_agent_repo.delete(agent_id)
    if not success:
        raise HTTPException(status_code=404, detail="External agent not found")

    return RedirectResponse(
        url="/external-agents?message=External agent deleted successfully",
        status_code=302,
    )
