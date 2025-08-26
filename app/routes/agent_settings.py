"""Agent settings routes for managing AI configuration."""

from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from ..deps import get_db_session
from ..models.agent_settings import AgentSettings
from ..repositories.agent_settings import AgentSettingsRepository
from ..repositories.tenants import TenantRepository
from ..services.sales_agent import load_default_prompt
from ..utils.cookies import get_active_tenant_id
from ..config import settings

templates = Jinja2Templates(directory="app/templates")

router = APIRouter()


def get_agent_settings_repo(
    session: Session = Depends(get_db_session),
) -> AgentSettingsRepository:
    """Get agent settings repository."""
    return AgentSettingsRepository(session)


def get_tenant_repo(session: Session = Depends(get_db_session)) -> TenantRepository:
    """Get tenant repository."""
    return TenantRepository(session)


def _validate_tenant_access(
    tenant_id: int, request: Request, tenant_repo: TenantRepository
) -> None:
    """Validate that the tenant exists and user has access."""
    # Check if tenant exists
    tenant = tenant_repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Check if this is the active tenant
    active_tenant_id = get_active_tenant_id(request)
    if active_tenant_id != tenant_id:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Tenant mismatch",
                "message": f"Please select tenant '{tenant.name}' from the navbar to manage its agent settings",
            },
        )


@router.get("/tenant/{tenant_id}/agent", response_class=HTMLResponse)
async def show_agent_settings(
    request: Request,
    tenant_id: int,
    agent_settings_repo: AgentSettingsRepository = Depends(get_agent_settings_repo),
    tenant_repo: TenantRepository = Depends(get_tenant_repo),
):
    """Show agent settings and effective prompt."""
    # Validate tenant access
    _validate_tenant_access(tenant_id, request, tenant_repo)

    # Get tenant
    tenant = tenant_repo.get_by_id(tenant_id)

    # Get current settings
    agent_settings = agent_settings_repo.get_by_tenant(tenant_id)

    # Load effective prompt
    try:
        if agent_settings and agent_settings.prompt_override:
            effective_prompt = agent_settings.prompt_override
            using_default = False
        else:
            effective_prompt = load_default_prompt()
            using_default = True
    except Exception as e:
        effective_prompt = f"Error loading prompt: {str(e)}"
        using_default = False

    return templates.TemplateResponse(
        "agent/index.html",
        {
            "request": request,
            "tenant": tenant,
            "agent_settings": agent_settings,
            "effective_prompt": effective_prompt,
            "using_default": using_default,
            "config": request.app.state.settings,
        },
    )


@router.post("/tenant/{tenant_id}/agent", response_class=HTMLResponse)
async def update_agent_settings(
    request: Request,
    tenant_id: int,
    prompt_override: Optional[str] = Form(None),
    model_name: str = Form("gemini-1.5-pro"),
    timeout_ms: int = Form(30000),
    agent_settings_repo: AgentSettingsRepository = Depends(get_agent_settings_repo),
    tenant_repo: TenantRepository = Depends(get_tenant_repo),
):
    """Update agent settings."""
    # Validate tenant access
    _validate_tenant_access(tenant_id, request, tenant_repo)

    # Validate inputs
    errors = []

    # Validate prompt_override length
    if prompt_override:
        prompt_override = prompt_override.strip()
        if len(prompt_override) > 10000:
            errors.append(
                f"Prompt override too long: {len(prompt_override)} characters (max 10,000)"
            )

    # Validate timeout
    if timeout_ms < 1000 or timeout_ms > 120000:
        errors.append("Timeout must be between 1,000 and 120,000 milliseconds")

    # Validate model name
    valid_models = [
        "gemini-1.5-pro",
        "gemini-1.5-flash",
        "claude-3-sonnet",
        "claude-3-haiku",
    ]
    if model_name not in valid_models:
        errors.append(f"Invalid model name. Must be one of: {', '.join(valid_models)}")

    if errors:
        # Get tenant for error display
        tenant = tenant_repo.get_by_id(tenant_id)
        agent_settings = agent_settings_repo.get_by_tenant(tenant_id)

        try:
            if agent_settings and agent_settings.prompt_override:
                effective_prompt = agent_settings.prompt_override
                using_default = False
            else:
                effective_prompt = load_default_prompt()
                using_default = True
        except Exception as e:
            effective_prompt = f"Error loading prompt: {str(e)}"
            using_default = False

        return templates.TemplateResponse(
            "agent/index.html",
            {
                "request": request,
                "tenant": tenant,
                "agent_settings": agent_settings,
                "effective_prompt": effective_prompt,
                "using_default": using_default,
                "errors": errors,
                "form_data": {
                    "prompt_override": prompt_override,
                    "model_name": model_name,
                    "timeout_ms": timeout_ms,
                },
                "config": request.app.state.settings,
            },
            status_code=400,
        )

    # Update or create settings
    agent_settings_repo.upsert_for_tenant(
        tenant_id,
        prompt_override=prompt_override if prompt_override else None,
        model_name=model_name,
        timeout_ms=timeout_ms,
    )

    return RedirectResponse(
        url=f"/tenant/{tenant_id}/agent?message=Agent settings updated successfully",
        status_code=302,
    )
