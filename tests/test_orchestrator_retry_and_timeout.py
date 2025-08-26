"""Tests for orchestrator retry logic, timeouts, and circuit breaker."""

import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

from app.services.orchestrator import CircuitBreaker, call_agent, orchestrate


class TestOrchestratorRetryAndTimeout:
    """Test orchestrator retry logic, timeouts, and circuit breaker."""

    @pytest.mark.asyncio
    async def test_agent_timeout_handling(self):
        """Test that agent timeouts are handled correctly."""
        # Mock httpx client that times out
        mock_response = MagicMock()
        mock_response.status_code = 408
        mock_response.json.return_value = {
            "error": {"type": "timeout", "message": "Request timed out", "status": 408}
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__ = AsyncMock(
                return_value=mock_client
            )
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_client.post.return_value = mock_response

            # Call agent with timeout
            result = await call_agent(
                agent_key="test-agent",
                url="http://test-agent.com/rank",
                brief="Test brief",
                timeout_ms=1000,
            )

            # Verify timeout error is returned
            assert result["success"] is False
            assert result["error"]["type"] == "timeout"
            assert "timed out" in result["error"]["message"].lower()

    @pytest.mark.asyncio
    async def test_circuit_breaker_failure_threshold(self):
        """Test circuit breaker opens after failure threshold is reached."""
        breaker = CircuitBreaker(failure_threshold=3, ttl_seconds=60)

        # Simulate 3 consecutive failures
        for i in range(3):
            breaker.record_failure("test-agent")

        # Verify circuit breaker is open
        assert breaker.is_open("test-agent") is True

        # Verify subsequent calls are blocked
        result = await call_agent(
            agent_key="test-agent",
            url="http://test-agent.com/rank",
            brief="Test brief",
            timeout_ms=1000,
        )

        assert result["success"] is False
        assert result["error"]["type"] == "breaker"
        assert "circuit breaker" in result["error"]["message"].lower()

    @pytest.mark.asyncio
    async def test_circuit_breaker_ttl_recovery(self):
        """Test circuit breaker recovers after TTL expires."""
        breaker = CircuitBreaker(
            failure_threshold=2, ttl_seconds=0.1
        )  # Very short TTL for testing

        # Simulate 2 consecutive failures
        breaker.record_failure("test-agent")
        breaker.record_failure("test-agent")

        # Verify circuit breaker is open
        assert breaker.is_open("test-agent") is True

        # Wait for TTL to expire
        await asyncio.sleep(0.2)

        # Verify circuit breaker is closed again
        assert breaker.is_open("test-agent") is False

    @pytest.mark.asyncio
    async def test_circuit_breaker_success_reset(self):
        """Test circuit breaker resets on successful call."""
        breaker = CircuitBreaker(failure_threshold=2, ttl_seconds=60)

        # Simulate 1 failure
        breaker.record_failure("test-agent")

        # Record success
        breaker.record_success("test-agent")

        # Verify circuit breaker is closed
        assert breaker.is_open("test-agent") is False

        # Verify failure count is reset
        assert breaker._failure_counts.get("test-agent", 0) == 0

    @pytest.mark.asyncio
    async def test_orchestrator_with_timeout_and_breaker(self):
        """Test orchestrator handles timeouts and circuit breaker correctly."""
        # Mock repositories
        mock_tenant_repo = MagicMock()
        mock_external_agent_repo = MagicMock()

        # Mock tenants
        mock_tenants = [
            MagicMock(id=1, name="Publisher A", slug="publisher-a"),
            MagicMock(id=2, name="Publisher B", slug="publisher-b"),
        ]
        mock_tenant_repo.list_all.return_value = mock_tenants
        mock_external_agent_repo.list_enabled.return_value = []

        # Mock HTTP responses - first agent times out, second succeeds
        mock_timeout_response = MagicMock()
        mock_timeout_response.status_code = 408
        mock_timeout_response.json.return_value = {
            "error": {"type": "timeout", "message": "Request timed out", "status": 408}
        }

        mock_success_response = MagicMock()
        mock_success_response.status_code = 200
        mock_success_response.json.return_value = {
            "items": [{"product_id": "prod_2", "reason": "Good match", "score": 0.8}]
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__ = AsyncMock(
                return_value=mock_client
            )
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

            # Mock different responses for different URLs
            def mock_post(url, **kwargs):
                if "publisher-a" in url:
                    return mock_timeout_response
                elif "publisher-b" in url:
                    return mock_success_response
                else:
                    raise Exception(f"Unexpected URL: {url}")

            mock_client.post.side_effect = mock_post

            # Create request
            from app.routes.orchestrator import OrchestrateRequest

            request = OrchestrateRequest(
                brief="Test brief",
                internal_tenant_slugs=["publisher-a", "publisher-b"],
                external_urls=None,
            )

            # Call orchestrator
            result = await orchestrate(
                brief=request.brief,
                internal_tenant_slugs=request.internal_tenant_slugs,
                external_urls=request.external_urls,
                timeout_ms=1000,
            )

            # Verify result
            assert result["total_agents"] == 2
            assert len(result["results"]) == 2

            # Verify first agent has timeout error
            assert result["results"][0]["agent"]["slug"] == "publisher-a"
            assert result["results"][0]["error"]["type"] == "timeout"
            assert len(result["results"][0]["items"]) == 0

            # Verify second agent succeeds
            assert result["results"][1]["agent"]["slug"] == "publisher-b"
            assert result["results"][1]["error"] is None
            assert len(result["results"][1]["items"]) == 1

    @pytest.mark.asyncio
    async def test_orchestrator_retry_after_breaker_opens(self):
        """Test orchestrator retries agent after circuit breaker opens and recovers."""
        # Mock repositories
        mock_tenant_repo = MagicMock()
        mock_external_agent_repo = MagicMock()

        # Mock single tenant
        mock_tenants = [MagicMock(id=1, name="Publisher A", slug="publisher-a")]
        mock_tenant_repo.list_all.return_value = mock_tenants
        mock_external_agent_repo.list_enabled.return_value = []

        # Mock HTTP responses - first 3 calls fail, then succeed
        mock_failure_response = MagicMock()
        mock_failure_response.status_code = 500
        mock_failure_response.json.return_value = {
            "error": {
                "type": "internal",
                "message": "Internal server error",
                "status": 500,
            }
        }

        mock_success_response = MagicMock()
        mock_success_response.status_code = 200
        mock_success_response.json.return_value = {
            "items": [
                {"product_id": "prod_1", "reason": "Success after retry", "score": 0.9}
            ]
        }

        call_count = 0

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__ = AsyncMock(
                return_value=mock_client
            )
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

            # Mock responses based on call count
            def mock_post(url, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count <= 3:
                    return mock_failure_response
                else:
                    return mock_success_response

            mock_client.post.side_effect = mock_post

            # Create request
            from app.routes.orchestrator import OrchestrateRequest

            request = OrchestrateRequest(
                brief="Test brief",
                internal_tenant_slugs=["publisher-a"],
                external_urls=None,
            )

            # First call - should fail 3 times then hit breaker
            result1 = await orchestrate(
                brief=request.brief,
                internal_tenant_slugs=request.internal_tenant_slugs,
                external_urls=request.external_urls,
                timeout_ms=1000,
            )

            # Verify circuit breaker opened
            assert result1["results"][0]["error"]["type"] == "breaker"

            # Wait for TTL to expire (use short TTL for testing)
            await asyncio.sleep(0.2)

            # Second call - should succeed after TTL expires
            result2 = await orchestrate(
                brief=request.brief,
                internal_tenant_slugs=request.internal_tenant_slugs,
                external_urls=request.external_urls,
                timeout_ms=1000,
            )

            # Verify success after recovery
            assert result2["results"][0]["error"] is None
            assert len(result2["results"][0]["items"]) == 1

    @pytest.mark.asyncio
    async def test_concurrent_agent_calls_with_timeouts(self):
        """Test concurrent agent calls handle timeouts correctly."""
        # Mock repositories
        mock_tenant_repo = MagicMock()
        mock_external_agent_repo = MagicMock()

        # Mock multiple tenants
        mock_tenants = [
            MagicMock(id=1, name="Publisher A", slug="publisher-a"),
            MagicMock(id=2, name="Publisher B", slug="publisher-b"),
            MagicMock(id=3, name="Publisher C", slug="publisher-c"),
        ]
        mock_tenant_repo.list_all.return_value = mock_tenants
        mock_external_agent_repo.list_enabled.return_value = []

        # Mock HTTP responses with different timing
        mock_timeout_response = MagicMock()
        mock_timeout_response.status_code = 408
        mock_timeout_response.json.return_value = {
            "error": {"type": "timeout", "message": "Request timed out", "status": 408}
        }

        mock_success_response = MagicMock()
        mock_success_response.status_code = 200
        mock_success_response.json.return_value = {
            "items": [{"product_id": "prod_1", "reason": "Success", "score": 0.8}]
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__ = AsyncMock(
                return_value=mock_client
            )
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

            # Mock different responses for different URLs
            def mock_post(url, **kwargs):
                if "publisher-a" in url:
                    return mock_timeout_response
                elif "publisher-b" in url:
                    return mock_success_response
                elif "publisher-c" in url:
                    return mock_timeout_response
                else:
                    raise Exception(f"Unexpected URL: {url}")

            mock_client.post.side_effect = mock_post

            # Create request
            from app.routes.orchestrator import OrchestrateRequest

            request = OrchestrateRequest(
                brief="Test brief",
                internal_tenant_slugs=["publisher-a", "publisher-b", "publisher-c"],
                external_urls=None,
            )

            # Call orchestrator
            result = await orchestrate(
                brief=request.brief,
                internal_tenant_slugs=request.internal_tenant_slugs,
                external_urls=request.external_urls,
                timeout_ms=1000,
            )

            # Verify result
            assert result["total_agents"] == 3
            assert len(result["results"]) == 3

            # Verify timeout agents have errors
            timeout_agents = [
                r for r in result["results"] if r["error"]["type"] == "timeout"
            ]
            success_agents = [r for r in result["results"] if r["error"] is None]

            assert len(timeout_agents) == 2
            assert len(success_agents) == 1
