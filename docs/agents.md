# Internal MCP Endpoints

This document describes the internal MCP (Model Context Protocol) endpoints that expose AdCP-compliant interfaces for sales agents.

## Overview

The MCP endpoints provide HTTP interfaces for internal sales agents, allowing the orchestrator and third parties to call each tenant's sales agent using the AdCP contract.

## Endpoints

### GET /mcp/

Returns service information and capabilities.

**Response:**
```json
{
  "service": "AdCP Demo Orchestrator",
  "adcp_version": "adcp-demo-0.1",
  "commit_hash": "abc123",
  "capabilities": ["ranking"]
}
```

### POST /mcp/agents/{tenant_slug}/rank

Ranks products for a specific tenant using AdCP contract.

**Request:**
```json
{
  "brief": "Sports advertising campaign for young adults",
  "context_id": "ctx-123"
}
```

**Success Response:**
```json
{
  "items": [
    {
      "product_id": "prod_1",
      "reason": "Perfect match for sports advertising",
      "score": 0.95
    },
    {
      "product_id": "prod_2",
      "reason": "Good demographic fit",
      "score": 0.85
    }
  ]
}
```

**Error Response:**
```json
{
  "error": {
    "type": "ai_config_error",
    "message": "Missing API key",
    "status": 500
  }
}
```

## Error Types

| Type | HTTP Status | Description |
|------|-------------|-------------|
| `invalid_request` | 400 | Invalid request (missing brief, empty brief) |
| `invalid_request` | 404 | Tenant not found |
| `invalid_request` | 422 | No products found for tenant |
| `ai_config_error` | 500 | AI configuration error (missing API key) |
| `timeout` | 408 | AI request timeout |
| `ai_request_error` | 502 | AI request error |
| `internal` | 500 | Unexpected internal error |

## Validation

### Request Validation

- **tenant_slug**: Must exist in the system
- **brief**: Required and non-empty string
- **context_id**: Optional UUID for request tracing

### Response Validation

- **items**: Array of ranked products
- **product_id**: Required string identifier
- **reason**: Required string explanation
- **score**: Optional float between 0.0 and 1.0

## Integration

### Orchestrator Integration

The orchestrator calls internal MCP endpoints via HTTP loopback:

```
POST http://localhost:8000/mcp/agents/{tenant_slug}/rank
```

### External Agent Integration

Third-party agents can call MCP endpoints using the same AdCP contract:

```
POST https://your-domain.com/mcp/agents/{tenant_slug}/rank
```

## Examples

### Successful Ranking Request

```bash
curl -X POST "http://localhost:8000/mcp/agents/publisher-a/rank" \
  -H "Content-Type: application/json" \
  -d '{
    "brief": "Sports advertising campaign for young adults",
    "context_id": "ctx-123"
  }'
```

### Error Handling

```bash
curl -X POST "http://localhost:8000/mcp/agents/unknown-tenant/rank" \
  -H "Content-Type: application/json" \
  -d '{
    "brief": "Test brief"
  }'
```

Response:
```json
{
  "error": {
    "type": "invalid_request",
    "message": "Tenant 'unknown-tenant' not found",
    "status": 404
  }
}
```

## Configuration

### Environment Variables

- `ADCP_VERSION`: AdCP version string (default: "adcp-demo-0.1")
- `SERVICE_BASE_URL`: Base URL for internal loopback calls (default: "http://localhost:8000")

### Git Integration

The service automatically includes the current git commit hash for traceability. If git is not available, it returns "unknown".

## Security

- No authentication required (demo mode)
- CORS enabled only when DEBUG=1
- Input validation prevents injection attacks
- Error messages do not expose sensitive information

## Performance

- Concurrent request handling with configurable limits
- Circuit breaker protection for failing agents
- Timeout handling for AI requests
- Efficient product loading and caching
