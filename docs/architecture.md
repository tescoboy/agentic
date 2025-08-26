# Architecture Overview

## File Size Rule

**Maximum 150 lines per file** (except HTML templates and tests).

This constraint ensures:
- Maintainable, readable code
- Clear separation of concerns
- Easy handover between developers
- Modular design patterns

## Module Structure

```
app/
├── main.py          # FastAPI app, routes, health endpoint
├── config.py        # Environment configuration and settings
├── deps.py          # Shared dependencies (DB, settings)
├── templates/       # Jinja2 HTML templates
└── [future modules]
    ├── models/      # SQLModel data models (Phase 2)
    ├── routes/      # FastAPI route handlers (Phase 3+)
    ├── services/    # Business logic (Phase 5+)
    └── agents/      # Agent implementations (Phase 5+)

tests/
├── test_health.py      # Health endpoint tests
├── test_environment.py # Configuration tests
└── [future test files]

docs/
├── setup.md           # Installation and running guide
├── architecture.md    # This file
├── api.md            # API documentation (Phase 3+)
├── agents.md         # Agent system docs (Phase 5+)
└── csv_template.md   # CSV import schema (Phase 4+)

reference/
├── README.md         # Reference repo guidelines
├── salesagent/       # Sales agent patterns (read-only)
└── adcp/            # AdCP protocol patterns (read-only)
```

## Module Purposes

- **main.py**: FastAPI application entry point, core routes
- **config.py**: Environment variable management, settings validation
- **deps.py**: Dependency injection for database, settings, services
- **db.py**: Database engine and session management
- **models/**: SQLModel data models for all entities
- **repositories/**: Repository layer for database operations
- **templates/**: Jinja2 HTML templates with Bootstrap 5 styling
- **tests/**: Unit and integration tests with pytest
- **docs/**: Project documentation and guides
- **reference/**: Read-only copies of reference repositories

## Entities

- **Tenant**: Multi-tenancy support with unique slug and timestamps
- **AgentSettings**: Per-tenant AI configuration (prompt override, model, timeout)
- **ExternalAgent**: MCP endpoint configuration with capabilities and enabled flag
- **Product**: AdCP-compliant product model with nested JSON storage for complex objects

## Tenant Context

The application uses cookie-based tenant context for multi-tenancy:

- **Cookie name**: `active_tenant_id` (30-day expiration, httponly, samesite=lax)
- **Middleware**: Automatically loads active tenant and all tenants for navbar
- **API endpoint**: `GET /tenants/current` returns JSON of active tenant or 404 with helpful error
- **Switching**: `POST /tenants/select` with `tenant_id` form parameter sets cookie and redirects

## Persistence

The application uses a file-backed SQLite database for data persistence:

- **Location**: `./data/adcp_demo.sqlite3`
- **Configuration**: Set via `DATABASE_URL` environment variable
- **PRAGMA Settings**: Optimized for performance and safety:
  - `journal_mode=WAL`: Write-Ahead Logging for concurrent access
  - `synchronous=NORMAL`: Balanced performance and safety
  - `foreign_keys=ON`: Enforce referential integrity
  - `cache_size=10000`: Optimize memory usage
  - `temp_store=MEMORY`: Use memory for temporary storage
- **Initialization**: Tables are created automatically on startup if they don't exist

## Products

Product management follows the AdCP Product specification:

- **Model**: Based on AdCP Product schema with JSON storage for complex objects
- **CRUD Operations**: Full create, read, update, delete functionality per tenant
- **Search & Pagination**: Server-side search across name/description with pagination
- **CSV Import/Export**: Bulk operations with strict validation and error reporting
- **Validation**: AdCP-compliant field validation with row-level error reporting
- **Bulk Operations**: Template download, bulk upload, and bulk delete with confirmation

### CSV Template

The CSV template aligns with AdCP Product fields:
- Required: product_id, name, description, delivery_type, is_fixed_price
- Optional: cpm, is_custom, expires_at, policy_compliance, targeted_ages, verified_minimum_age
- Validation: Strict header matching, type checking, and constraint validation
- Error Handling: No partial imports - all rows must be valid
- **Data Safety**: Data persists across server restarts and application updates

## Development Philosophy

### Single Service Architecture
- **Why**: Lower complexity, faster iteration, easier handover
- **Benefits**: Simplified deployment, unified logging, shared dependencies
- **Trade-offs**: Monolithic structure, but modular internal organization

### Vibe Coding Approach
- **Focus**: Rapid prototyping and iteration
- **Constraints**: 150-line file limit forces modular design
- **Quality**: Automated testing and linting ensure maintainability

### No Dummy Data
- **Principle**: All data must be real and actionable
- **Sources**: User CSV uploads, live external agent calls
- **Errors**: Clear, actionable error messages for missing data

## Technology Stack

- **Backend**: FastAPI with async/await patterns
- **Frontend**: Bootstrap 5 + Font Awesome + HTMX
- **Database**: SQLite with SQLModel ORM
- **Testing**: pytest with httpx AsyncClient
- **Quality**: ruff (linting), black (formatting), mypy (type checking)
- **AI**: Abstraction layer supporting Gemini and Claude

## Development Workflow

1. **Incremental Development**: Each phase builds on previous
2. **Test-First**: Tests written before implementation
3. **Quality Gates**: Lint, format, type-check before commit
4. **Documentation**: Docs updated with each phase
5. **Reference Integration**: Copy patterns from reference repos as needed

## Future Phases

- **Phase 2**: Data models and database layer
- **Phase 3**: Tenant admin and switcher
- **Phase 4**: Product CRUD and CSV bulk import
- **Phase 5**: Sales agent service with AI abstraction
- **Phase 6**: Orchestrator service with async fan-out
- **Phase 7**: Buyer UI with brief input and results
  - **Phase 8**: MCP endpoint and external agent registry
  - **Phase 9**: Test expansion and comprehensive documentation

## Buyer UI

The buyer interface provides a user-friendly way to submit briefs and view orchestrated results:

- **Routes**: `app/routes/buyer.py` - Form handling and orchestration integration
- **Template**: `app/templates/buyer/index.html` - Bootstrap-responsive UI
- **No Authentication**: Public access without tenant context requirements
- **Agent Selection**: Checkbox lists for internal tenants and enabled external agents
- **Orchestrator Integration**: HTTP calls to `/orchestrate` endpoint via SERVICE_BASE_URL
- **Results Display**: Per-agent cards showing products, reasons, and error states

### Form Features

- **Brief Input**: Required textarea with placeholder guidance
- **Agent Selection**: Default all-selected state with individual toggles
- **Advanced Options**: Collapsible section for timeout override
- **Validation**: Client and server-side validation for brief and agent selection
- **Responsive Design**: Bootstrap utilities for mobile portrait compatibility

### Results Display

- **Per-Agent Cards**: Individual cards for each agent with clear identification
- **Success States**: Product lists with names, reasons, and optional scores
- **Error States**: Inline error badges and messages without blocking other results
- **Mixed Results**: Graceful handling of partial successes and failures
- **Context Information**: Context ID and agent count for debugging

### Data Sources

- **Internal Tenants**: All tenants from tenant repository
- **External Agents**: Only enabled agents from external agent repository
- **Product Details**: Minimal display focusing on name and description
- **No Fabrication**: All data must be real with no dummy fallbacks

### Error Handling

- **Form Validation**: Clear messages for empty brief and no agent selection
- **Orchestrator Errors**: Structured error display from orchestration service
- **HTTP Errors**: Timeout and connection error handling
- **Partial Failures**: Individual agent errors shown inline
- **User Feedback**: Actionable error messages with guidance

## MCP Exposure

The MCP (Model Context Protocol) endpoints expose internal sales agents as AdCP-compliant HTTP services:

- **Routes**: `app/routes/mcp.py` - MCP endpoints with AdCP contract implementation
- **Service Integration**: Calls `sales_agent.evaluate_brief` from Phase 5, not AI directly
- **AdCP Compliance**: Strict request/response validation with structured error handling
- **Orchestrator Integration**: Internal loopback calls via HTTP using SERVICE_BASE_URL
- **External Access**: Third-party agents can call the same endpoints

### MCP Endpoints

- **GET /mcp/**: Service information and capabilities
- **POST /mcp/agents/{tenant_slug}/rank**: Product ranking with AdCP contract

### AdCP Contract

- **Request Format**: `{"brief": "text", "context_id": "uuid"}` (context_id optional)
- **Success Response**: `{"items": [{"product_id": "id", "reason": "text", "score": 0.0}]}`
- **Error Response**: `{"error": {"type": "error_type", "message": "text", "status": 400}}`
- **Validation**: Tenant existence, brief presence, product availability
- **Error Mapping**: AI exceptions mapped to appropriate HTTP status codes

### Error Handling

- **404**: Unknown tenant slug
- **400**: Missing or empty brief
- **422**: No products found for tenant
- **500**: AI configuration error (missing API key)
- **408**: AI request timeout
- **502**: AI request error
- **500**: Unexpected internal error

### UI Integration

- **Agent Settings Page**: Displays exact endpoint URL for each tenant
- **URL Format**: `${SERVICE_BASE_URL}/mcp/agents/{tenant_slug}/rank`
- **Documentation**: Request/response format examples in UI
- **Developer Support**: Path-only URL for same-host development

### Configuration

- **ADCP_VERSION**: Environment variable for version string (default: "adcp-demo-0.1")
- **SERVICE_BASE_URL**: Base URL for internal loopback calls
- **Git Integration**: Automatic commit hash inclusion for traceability
- **CORS Support**: Optional permissive CORS when DEBUG=1
