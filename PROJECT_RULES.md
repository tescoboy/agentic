# AdCP Orchestrator - Project Rules & Best Practices

## North Star
Build a demo-ready AdCP orchestrator showing publishers creating products and buyers sending briefs to orchestrated sales agents that return relevant products with reasons.

## Architecture Stack
- **Backend**: Single FastAPI service with clear modules (no microservices)
- **Frontend**: Bootstrap 5, Font Awesome, HTMX
- **Database**: SQLite with SQLModel ORM (auto-create tables, no migrations for demo)
- **HTTP Client**: Async httpx with timeouts + circuit breakers
- **AI Provider**: Abstraction layer (Gemini default, configurable to Claude)
- **Testing**: pytest + httpx AsyncClient
- **Code Quality**: ruff, black, mypy
- **Configuration**: dotenv for environment variables

## File Structure Rules
```
/src
  /components          # Reusable UI components
  /styles             # CSS files only
    styles.css
    custom-bootstrap.css
  /services           # Business logic & API calls
    api.js
    supabase.js
  /utils              # Helper functions
    formatDate.js
  /templates          # Jinja2 templates
  /models             # SQLModel models
  /routes             # FastAPI route handlers
  /agents             # Agent implementations
  /tests              # Test files
/docs                 # Documentation
  setup.md
  architecture.md
  api.md
  agents.md
  csv_template.md
```

## Critical Constraints (Never Ever)
- **No dummy data** - Use user-provided CSV uploads and live external agent calls only
- **No inline CSS** - All styles in CSS files or Bootstrap classes
- **No giant files** - Maximum 150 lines per file (except HTML templates and tests)
- **No hacks, ugly loops, or hardcoded fallbacks** - Clean, maintainable code only
- **No seeded data** - If tenant has no products, return clear actionable error

## Code Quality Standards

### JavaScript Best Practices
- Use `addEventListener()` instead of inline event handlers
- Functions must be small, modular, and reusable (single responsibility)
- Console logging required for debugging API calls and errors
- Proper error handling for all async operations
- Debounce expensive functions (search, API calls)

### CSS & Styling Rules
- **Bootstrap 5 mandatory** for all styling
- No inline CSS allowed
- Use Bootstrap grid system for layouts
- Use Bootstrap components instead of custom elements
- Use Bootstrap utility classes for spacing and colors
- Custom styles only in `custom-bootstrap.css`

### HTML Structure
- Clean, semantic HTML using Bootstrap grid and components
- Responsive adaptation using Bootstrap (mobile portrait must display clean tables and cards)
- Lazy load images with `loading="lazy"` attribute

### Python/FastAPI Standards
- Async/await patterns for all I/O operations
- Pure async with httpx inside request cycle (no Celery)
- Per-agent timeouts with small concurrency limits
- Proper error handling with try/catch blocks
- Type hints required
- Small, focused functions
- Clear separation of concerns

## Core Features

### Tenant Management
- Simple tenant switcher (no authentication)
- Navbar switcher for multi-tenancy

### Product Management
- CRUD operations for products
- CSV bulk upload with strict schema validation
- Downloadable CSV template matching AdCP product spec
- Reject bad rows with line numbers and reasons
- Searchable, sortable, paginated product view

### Agent System
- Publisher prompt override per agent
- Support for internal and external agents
- Manually configured external agent registry (no auto-discovery)
- Buyer can unselect agents before submit
- 3rd party MCP endpoint integration
- Expose own agents via MCP endpoint per tenant

### Orchestration Flow
1. Buyer submits brief (request-response, no WebSocket/SSE)
2. Orchestrator fans out to all selected agents (async with timeouts)
3. Per-agent timeouts with structured error capture
4. Agents return relevant products with rationale
5. Preserve each agent's native ranking (no global re-ranking)
6. Optional sort by confidence score if available
7. Display per-agent groups with inline error handling

## Documentation Requirements
- `/docs/setup.md` - Installation and running instructions
- `/docs/architecture.md` - Module overview and file size rules
- `/docs/api.md` - API endpoint documentation
- `/docs/agents.md` - Internal/external agent flows
- `/docs/csv_template.md` - Sample CSV and schema

## Reference Repositories
- https://github.com/adcontextprotocol/salesagent (read-only, copy specific files/functions, cite source paths in comments)
- https://github.com/adcontextprotocol/adcp (read-only, copy specific files/functions, cite source paths in comments)
- Never treat as dependencies, never push to them

## Development Workflow
- Start server processes in background by default
- Keep solutions simple - rethink if approach becomes complicated
- Maintain clean, logical file structure
- No duplicate code - reuse functions and utility methods
- All files must be under 150 lines (except HTML templates and tests)
- Incremental testing per phase - each phase lands its own tests and must pass before moving on

## Testing Requirements
- pytest for backend testing
- httpx AsyncClient for API testing
- Comprehensive error handling tests
- Integration tests for agent orchestration

## Performance Considerations
- Async operations for all I/O
- Circuit breakers for external API calls
- Timeout handling for all HTTP requests
- Lazy loading for images
- Debounced search functionality

