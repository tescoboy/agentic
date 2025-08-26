"""Orchestrator service for fanning out buyer briefs to multiple agents via AdCP."""

import asyncio
import time
import uuid
from typing import Any, Dict, List, Optional

import httpx

from ..config import settings


class CircuitBreaker:
    """Simple in-memory circuit breaker for agent failure tracking."""

    def __init__(self):
        self.failures: Dict[str, Dict[str, Any]] = {}

    def should_skip(self, agent_key: str) -> bool:
        """Check if agent should be skipped due to circuit breaker."""
        if agent_key not in self.failures:
            return False

        failure_info = self.failures[agent_key]
        if failure_info["count"] >= settings.cb_failure_threshold:
            # Check if still within TTL
            if time.time() - failure_info["last_failure"] < settings.cb_ttl_seconds:
                return True
            else:
                # TTL expired, reset
                del self.failures[agent_key]
        return False

    def record_failure(self, agent_key: str) -> None:
        """Record a failure for the agent."""
        now = time.time()
        if agent_key in self.failures:
            self.failures[agent_key]["count"] += 1
            self.failures[agent_key]["last_failure"] = now
        else:
            self.failures[agent_key] = {"count": 1, "last_failure": now}

    def record_success(self, agent_key: str) -> None:
        """Record a success, resetting failure count."""
        if agent_key in self.failures:
            del self.failures[agent_key]


# Global circuit breaker instance
circuit_breaker = CircuitBreaker()


def build_adcp_request(brief: str, context_id: Optional[str] = None) -> Dict[str, Any]:
    """Build AdCP-compliant request body for ranking."""
    request = {"brief": brief}
    if context_id:
        request["context_id"] = context_id
    return request


def validate_adcp_response(response_data: Dict[str, Any]) -> bool:
    """Validate agent response against AdCP contract."""
    # Check for both items and error (invalid)
    if "items" in response_data and "error" in response_data:
        return False

    # Check for error response
    if "error" in response_data:
        error = response_data["error"]
        required_error_fields = ["type", "message"]
        return all(field in error for field in required_error_fields)

    # Check for success response with items
    if "items" not in response_data:
        return False

    items = response_data["items"]
    if not isinstance(items, list):
        return False

    # Validate each item has required fields
    for item in items:
        if not isinstance(item, dict):
            return False
        if "product_id" not in item or "reason" not in item:
            return False
        if not isinstance(item["product_id"], str) or not isinstance(
            item["reason"], str
        ):
            return False

    return True


async def call_agent(
    agent_url: str, brief: str, timeout_ms: int, context_id: Optional[str] = None
) -> Dict[str, Any]:
    """Call a single agent with AdCP request."""
    start_time = time.time()

    try:
        async with httpx.AsyncClient() as client:
            request_body = build_adcp_request(brief, context_id)

            response = await client.post(
                agent_url,
                json=request_body,
                timeout=timeout_ms / 1000.0,
                headers={"Content-Type": "application/json"},
            )

            duration_ms = int((time.time() - start_time) * 1000)

            if response.status_code == 200:
                response_data = response.json()
                if validate_adcp_response(response_data):
                    # Check if it's an error response
                    if "error" in response_data:
                        return {
                            "success": False,
                            "error": response_data["error"],
                            "duration_ms": duration_ms,
                            "status_code": response.status_code,
                        }
                    else:
                        # Success response with items
                        return {
                            "success": True,
                            "data": response_data,
                            "duration_ms": duration_ms,
                            "status_code": response.status_code,
                        }
                else:
                    return {
                        "success": False,
                        "error": {
                            "type": "invalid_response",
                            "message": "Agent response does not match AdCP contract",
                            "status": response.status_code,
                        },
                        "duration_ms": duration_ms,
                        "status_code": response.status_code,
                    }
            else:
                return {
                    "success": False,
                    "error": {
                        "type": "http",
                        "message": f"HTTP {response.status_code}: {response.text}",
                        "status": response.status_code,
                    },
                    "duration_ms": duration_ms,
                    "status_code": response.status_code,
                }

    except httpx.TimeoutException:
        duration_ms = int((time.time() - start_time) * 1000)
        return {
            "success": False,
            "error": {
                "type": "timeout",
                "message": f"Request timed out after {timeout_ms}ms",
                "status": 408,
            },
            "duration_ms": duration_ms,
            "status_code": 408,
        }
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        return {
            "success": False,
            "error": {
                "type": "internal",
                "message": f"Unexpected error: {str(e)}",
                "status": 500,
            },
            "duration_ms": duration_ms,
            "status_code": 500,
        }


async def orchestrate(
    brief: str,
    internal_tenant_slugs: List[str],
    external_urls: List[str],
    timeout_ms: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Orchestrate buyer brief across multiple agents using AdCP protocol.

    Args:
        brief: Buyer brief text
        internal_tenant_slugs: List of internal tenant slugs to call
        external_urls: List of external agent URLs to call
        timeout_ms: Per-request timeout in milliseconds

    Returns:
        Aggregated results with per-agent responses and errors
    """
    if not brief or not brief.strip():
        raise ValueError("Brief must be non-empty")

    if not internal_tenant_slugs and not external_urls:
        raise ValueError("At least one agent (internal or external) must be specified")

    timeout_ms = timeout_ms or settings.orch_timeout_ms_default
    context_id = str(uuid.uuid4())  # For cross-request tracing

    # Build agent URLs
    agent_calls = []

    # Internal agents
    for slug in internal_tenant_slugs:
        agent_key = f"internal:{slug}"
        if circuit_breaker.should_skip(agent_key):
            agent_calls.append(
                {
                    "agent": {"type": "internal", "slug": slug},
                    "items": [],
                    "error": {
                        "type": "breaker",
                        "message": "Circuit breaker open - agent skipped",
                        "status": None,
                    },
                }
            )
        else:
            url = f"{settings.service_base_url}/mcp/agents/{slug}/rank"
            agent_calls.append(
                {
                    "url": url,
                    "agent": {"type": "internal", "slug": slug},
                    "agent_key": agent_key,
                }
            )

    # External agents
    for url in external_urls:
        agent_key = f"external:{url}"
        if circuit_breaker.should_skip(agent_key):
            agent_calls.append(
                {
                    "agent": {"type": "external", "url": url},
                    "items": [],
                    "error": {
                        "type": "breaker",
                        "message": "Circuit breaker open - agent skipped",
                        "status": None,
                    },
                }
            )
        else:
            agent_calls.append(
                {
                    "url": url,
                    "agent": {"type": "external", "url": url},
                    "agent_key": agent_key,
                }
            )

    # Execute calls concurrently
    semaphore = asyncio.Semaphore(settings.orch_concurrency)

    async def call_with_semaphore(call_info: Dict[str, Any]) -> Dict[str, Any]:
        async with semaphore:
            if "url" in call_info:
                result = await call_agent(
                    call_info["url"], brief, timeout_ms, context_id
                )

                agent_key = call_info["agent_key"]
                if result["success"]:
                    circuit_breaker.record_success(agent_key)
                    return {
                        "agent": call_info["agent"],
                        "items": result["data"].get("items", []),
                        "error": None,
                    }
                else:
                    circuit_breaker.record_failure(agent_key)
                    return {
                        "agent": call_info["agent"],
                        "items": [],
                        "error": result["error"],
                    }
            else:
                # Circuit breaker result
                return call_info

    # Execute all calls
    tasks = [call_with_semaphore(call_info) for call_info in agent_calls]
    results = await asyncio.gather(*tasks)

    return {
        "results": results,
        "context_id": context_id,
        "total_agents": len(agent_calls),
        "timeout_ms": timeout_ms,
    }
