# API Documentation

This document describes the API endpoints available in the AdCP Demo Orchestrator.

## Base URL
All endpoints are relative to: `http://localhost:8000`

## Route Index

### Health & Status
- `GET /health` - Service health check

### Tenant Management
- `GET /tenants` - List all tenants
- `GET /tenants/current` - Get current tenant context
- `POST /tenants/select` - Select tenant context
- `POST /tenants` - Create new tenant

### Product Management
- `GET /tenant/{id}/products` - List products for tenant
- `POST /tenant/{id}/products` - Create new product
- `GET /tenant/{id}/products/{product_id}` - Get product details
- `PUT /tenant/{id}/products/{product_id}` - Update product
- `DELETE /tenant/{id}/products/{product_id}` - Delete product
- `GET /tenant/{id}/products/template.csv` - Download CSV template
- `POST /tenant/{id}/products/bulk-upload` - Bulk upload products from CSV

### Agent Settings
- `GET /tenant/{id}/agent` - View agent settings
- `POST /tenant/{id}/agent` - Update agent settings

### External Agents
- `GET /external-agents` - List external agents
- `GET /external-agents/add` - Add external agent form
- `POST /external-agents/add` - Create external agent
- `GET /external-agents/{id}/edit` - Edit external agent form
- `POST /external-agents/{id}/edit` - Update external agent
- `POST /external-agents/{id}/delete` - Delete external agent

### Buyer Interface
- `GET /buyer` - Buyer interface
- `POST /buyer` - Submit buyer brief

### Orchestrator
- `POST /orchestrate` - Orchestrate brief across agents

### MCP Endpoints
- `GET /mcp/` - MCP service information
- `POST /mcp/agents/{tenant_slug}/rank` - Rank products for tenant

## Detailed Endpoint Documentation

### Health Check

**GET /health**

Returns service health status.

**Response:**
```json
{
  "status": "ok",
  "service": "adcp-demo-orchestrator",
  "version": "0.1.0"
}
```

### Tenant Management

**GET /tenants**

Returns list of all tenants.

**Response:**
```json
[
  {
    "id": 1,
    "name": "Publisher A",
    "slug": "publisher-a"
  }
]
```

**POST /tenants/select**

Select tenant context for session.

**Request:**
```json
{
  "tenant_id": 1
}
```

**Response:**
```json
{
  "success": true,
  "tenant": {
    "id": 1,
    "name": "Publisher A",
    "slug": "publisher-a"
  }
}
```

### Product Management

**GET /tenant/{id}/products**

List products for a tenant with pagination.

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `size` (int): Page size (default: 20)
- `query` (string): Search query
- `sort` (string): Sort field (name, created_at)
- `order` (string): Sort order (asc, desc)

**Response:**
```json
{
  "products": [
    {
      "id": 1,
      "product_id": "prod_1",
      "name": "Banner Ad",
      "description": "High-visibility banner advertisement",
      "tenant_id": 1
    }
  ],
  "total": 1,
  "page": 1,
  "size": 20,
  "total_pages": 1
}
```

**POST /tenant/{id}/products**

Create a new product.

**Request:**
```json
{
  "product_id": "prod_1",
  "name": "Banner Ad",
  "description": "High-visibility banner advertisement"
}
```

**Response:**
```json
{
  "id": 1,
  "product_id": "prod_1",
  "name": "Banner Ad",
  "description": "High-visibility banner advertisement",
  "tenant_id": 1
}
```

### Agent Settings

**GET /tenant/{id}/agent**

Get agent settings for a tenant.

**Response:**
```json
{
  "tenant_id": 1,
  "model_name": "gemini-1.5-pro",
  "timeout_ms": 30000,
  "prompt_override": "Custom prompt for this tenant"
}
```

**POST /tenant/{id}/agent**

Update agent settings.

**Request:**
```json
{
  "model_name": "gemini-1.5-pro",
  "timeout_ms": 30000,
  "prompt_override": "Custom prompt for this tenant"
}
```

### External Agents

**GET /external-agents**

List all external agents.

**Response:**
```json
[
  {
    "id": 1,
    "name": "External Agent A",
    "url": "https://external-agent.com/rank",
    "enabled": true
  }
]
```

**POST /external-agents/add**

Create external agent.

**Request:**
```json
{
  "name": "External Agent A",
  "url": "https://external-agent.com/rank",
  "enabled": true
}
```

### Buyer Interface

**GET /buyer**

Returns buyer interface HTML.

**POST /buyer**

Submit buyer brief for orchestration.

**Request:**
```json
{
  "brief": "Sports advertising campaign for young adults",
  "internal_tenant_slugs": ["publisher-a", "publisher-b"],
  "external_urls": ["https://external-agent.com/rank"],
  "timeout_ms": 5000
}
```

**Response:**
```html
<!-- HTML response with orchestration results -->
```

### Orchestrator

**POST /orchestrate**

Orchestrate brief across multiple agents.

**Request:**
```json
{
  "brief": "Sports advertising campaign for young adults",
  "internal_tenant_slugs": ["publisher-a", "publisher-b"],
  "external_urls": ["https://external-agent.com/rank"],
  "timeout_ms": 5000
}
```

**Response:**
```json
{
  "total_agents": 3,
  "context_id": "uuid-1234-5678",
  "results": [
    {
      "agent": {
        "type": "internal",
        "slug": "publisher-a"
      },
      "items": [
        {
          "product_id": "prod_1",
          "reason": "Perfect match for sports advertising",
          "score": 0.95
        }
      ],
      "error": null
    },
    {
      "agent": {
        "type": "external",
        "url": "https://external-agent.com/rank"
      },
      "items": [],
      "error": {
        "type": "timeout",
        "message": "Request timed out",
        "status": 408
      }
    }
  ]
}
```

## MCP Endpoints (AdCP Protocol)

### Service Information

**GET /mcp/**

Returns MCP service information and capabilities.

**Response:**
```json
{
  "service": "AdCP Demo Orchestrator",
  "adcp_version": "adcp-demo-0.1",
  "commit_hash": "abc123",
  "capabilities": ["ranking"]
}
```

### Product Ranking

**POST /mcp/agents/{tenant_slug}/rank**

Rank products for a specific tenant using AdCP protocol.

**Request:**
```json
{
  "brief": "Sports advertising campaign for young adults",
  "context_id": "uuid-1234-5678"
}
```

**Success Response (200):**
```json
{
  "items": [
    {
      "product_id": "prod_1",
      "reason": "Perfect match for sports advertising campaign",
      "score": 0.95
    },
    {
      "product_id": "prod_2",
      "reason": "Good video option for sports content",
      "score": 0.85
    }
  ]
}
```

**Error Response (4xx/5xx):**
```json
{
  "error": {
    "type": "ai_config_error",
    "message": "Missing API key for AI provider",
    "status": 500
  }
}
```

## Error Types

### AdCP Error Types
- `ai_config_error` - AI provider configuration error (500)
- `ai_request_error` - AI provider request error (502)
- `timeout` - Request timeout (408)
- `invalid_request` - Invalid request format (400)
- `invalid_response` - Invalid response format (422)
- `internal` - Unexpected internal error (500)

### HTTP Status Codes
- `200` - Success
- `400` - Bad Request (validation errors)
- `404` - Not Found (tenant not found)
- `408` - Request Timeout
- `415` - Unsupported Media Type
- `422` - Unprocessable Entity (no products)
- `500` - Internal Server Error
- `502` - Bad Gateway (AI provider error)

## Authentication

Currently, the API does not require authentication for demo purposes. In production, implement proper authentication and authorization.

## Rate Limiting

No rate limiting is currently implemented. For production use, consider implementing rate limiting to prevent abuse.

## CORS

CORS is disabled by default for server-to-server communication. When `DEBUG=1`, permissive CORS is enabled for browser testing.

## Examples

### Complete Orchestration Flow

1. **Create Tenant**
```bash
curl -X POST http://localhost:8000/tenants \
  -H "Content-Type: application/json" \
  -d '{"name": "Sports Publisher", "slug": "sports-publisher"}'
```

2. **Add Products**
```bash
curl -X POST http://localhost:8000/tenant/1/products \
  -H "Content-Type: application/json" \
  -d '{"product_id": "sports_banner", "name": "Sports Banner", "description": "Sports banner ad"}'
```

3. **Configure Agent Settings**
```bash
curl -X POST http://localhost:8000/tenant/1/agent \
  -H "Content-Type: application/json" \
  -d '{"model_name": "gemini-1.5-pro", "timeout_ms": 30000}'
```

4. **Orchestrate Brief**
```bash
curl -X POST http://localhost:8000/orchestrate \
  -H "Content-Type: application/json" \
  -d '{"brief": "Sports advertising for young adults", "internal_tenant_slugs": ["sports-publisher"]}'
```

### Direct MCP Call

```bash
curl -X POST http://localhost:8000/mcp/agents/sports-publisher/rank \
  -H "Content-Type: application/json" \
  -d '{"brief": "Sports advertising for young adults"}'
```

## Testing

Use the provided test suite to verify API functionality:

```bash
# Run all tests
pytest

# Run specific API tests
pytest tests/test_mcp_endpoint.py
pytest tests/test_orchestrator_internal.py
```

## Monitoring

Monitor API performance and errors:

- Check application logs for detailed error information
- Monitor response times for orchestration calls
- Track circuit breaker state for external agents
- Monitor AI provider response times and errors
