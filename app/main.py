"""Main FastAPI application for AdCP Demo Orchestrator."""

import time
import uuid
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from .db import get_session, init_db
from .repositories.tenants import TenantRepository
from .routes import tenant_context, tenant_delete, tenants
from .routes.products import router as products_router
from .routes.agent_settings import router as agent_settings_router
from .routes.orchestrator import router as orchestrator_router
from .routes.external_agents import router as external_agents_router
from .routes.buyer import router as buyer_router
from .routes.mcp import router as mcp_router
from .routes.preflight import router as preflight_router
from .utils.cookies import get_active_tenant_id
from .utils.logging import configure_default_logging, get_logger
from .config import settings

# Configure logging
configure_default_logging(level="INFO" if not settings.debug else "DEBUG")

# Create FastAPI app
app = FastAPI(
    title="AdCP Demo Orchestrator",
    description="Demo-ready AdCP orchestration that lets a buyer brief fan out to publisher sales agents",
    version="0.1.0",
)

# Store settings in app state for template access
app.state.settings = settings

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Set up Jinja2 templates
templates = Jinja2Templates(directory="app/templates")

# Include routers
app.include_router(tenants.router)
app.include_router(tenant_context.router)
app.include_router(tenant_delete.router)
app.include_router(products_router)
app.include_router(agent_settings_router)
app.include_router(orchestrator_router)
app.include_router(external_agents_router)
app.include_router(buyer_router)
app.include_router(mcp_router)
app.include_router(preflight_router)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    init_db()


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """Add request ID to all requests."""
    # Generate request ID
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    # Add to response headers
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id

    return response


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Log request start and end with duration."""
    start_time = time.time()
    request_id = getattr(request.state, "request_id", "unknown")
    logger = get_logger("http", request_id)

    # Log request start
    logger.info(f"Request started: {request.method} {request.url.path}")

    response = await call_next(request)

    # Calculate duration
    duration_ms = int((time.time() - start_time) * 1000)

    # Log request end
    logger.info(
        f"Request completed: {request.method} {request.url.path} - {response.status_code} ({duration_ms}ms)"
    )

    return response


@app.middleware("http")
async def tenant_context_middleware(request: Request, call_next):
    """Add tenant context to request state."""
    # Get active tenant from cookie
    tenant_id = get_active_tenant_id(request)
    active_tenant = None
    tenants_list = []

    try:
        if tenant_id:
            # Load active tenant
            with get_session() as session:
                repo = TenantRepository(session)
                active_tenant = repo.get_by_id(tenant_id)

        # Load all tenants for navbar
        with get_session() as session:
            repo = TenantRepository(session)
            tenants_list = repo.list_all()
    except Exception as e:
        # If database is not ready, continue without tenant context
        request_id = getattr(request.state, "request_id", "unknown")
        logger = get_logger("middleware", request_id)
        logger.warning(f"Database error in tenant context middleware: {e}")

    # Add to request state
    request.state.active_tenant = active_tenant
    request.state.tenants = tenants_list

    response = await call_next(request)
    return response


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "adcp-demo-orchestrator", "version": "0.1.0"}


@app.get("/")
async def root(request: Request):
    """Root endpoint serving the main application."""
    return templates.TemplateResponse(
        "base.html",
        {
            "request": request,
            "title": "AdCP Demo Orchestrator",
            "active_tenant": getattr(request.state, "active_tenant", None),
            "tenants": getattr(request.state, "tenants", []),
            "config": settings,
        },
    )
