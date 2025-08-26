"""Preflight check routes for system readiness."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from ..services.preflight import run_checks, get_overall_status, get_status_summary

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/preflight")
async def get_preflight_checks():
    """Get preflight checks as JSON."""
    checks = run_checks()
    overall_status = get_overall_status(checks)
    summary = get_status_summary(checks)

    return {"overall_status": overall_status, "summary": summary, "checks": checks}


@router.get("/preflight/ui", response_class=HTMLResponse)
async def get_preflight_ui(request: Request):
    """Get preflight checks as HTML page."""
    checks = run_checks()
    overall_status = get_overall_status(checks)
    summary = get_status_summary(checks)

    return templates.TemplateResponse(
        "preflight/index.html",
        {
            "request": request,
            "overall_status": overall_status,
            "summary": summary,
            "checks": checks,
            "config": request.app.state.settings,
        },
    )
