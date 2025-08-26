"""Tests for circuit breaker functionality."""

import time
import pytest
from unittest.mock import patch, MagicMock

from app.services.orchestrator import CircuitBreaker, orchestrate


class TestCircuitBreaker:
    """Test circuit breaker functionality."""

    def test_circuit_breaker_initial_state(self):
        """Test circuit breaker starts in closed state."""
        cb = CircuitBreaker()
        assert not cb.should_skip("test-agent")

    def test_circuit_breaker_single_failure(self):
        """Test circuit breaker with single failure."""
        cb = CircuitBreaker()

        # First failure
        cb.record_failure("test-agent")
        assert not cb.should_skip("test-agent")  # Still below threshold

    def test_circuit_breaker_threshold_reached(self):
        """Test circuit breaker opens after threshold reached."""
        cb = CircuitBreaker()

        # Record failures up to threshold (default is 3)
        cb.record_failure("test-agent")
        cb.record_failure("test-agent")
        cb.record_failure("test-agent")

        # Should now skip
        assert cb.should_skip("test-agent")

    def test_circuit_breaker_success_resets(self):
        """Test that success resets failure count."""
        cb = CircuitBreaker()

        # Record some failures
        cb.record_failure("test-agent")
        cb.record_failure("test-agent")

        # Success should reset
        cb.record_success("test-agent")
        assert not cb.should_skip("test-agent")

    def test_circuit_breaker_ttl_expiry(self):
        """Test circuit breaker recovers after TTL expires."""
        cb = CircuitBreaker()

        # Record failures to open circuit
        cb.record_failure("test-agent")
        cb.record_failure("test-agent")
        cb.record_failure("test-agent")

        assert cb.should_skip("test-agent")

        # Manually expire TTL by modifying last_failure time
        cb.failures["test-agent"]["last_failure"] = (
            time.time() - 70
        )  # TTL is 60 seconds

        # Should no longer skip
        assert not cb.should_skip("test-agent")

    def test_circuit_breaker_multiple_agents(self):
        """Test circuit breaker handles multiple agents independently."""
        cb = CircuitBreaker()

        # Fail agent A
        cb.record_failure("agent-a")
        cb.record_failure("agent-a")
        cb.record_failure("agent-a")

        # Agent A should be skipped
        assert cb.should_skip("agent-a")

        # Agent B should not be skipped
        assert not cb.should_skip("agent-b")

    @pytest.mark.asyncio
    async def test_circuit_breaker_integration_with_orchestrator(self):
        """Test circuit breaker integration with orchestrator."""
        from httpx import TimeoutException

        # First call - should fail and record failure
        with patch(
            "httpx.AsyncClient.post", side_effect=TimeoutException("Request timed out")
        ):
            result1 = await orchestrate(
                brief="Test brief",
                internal_tenant_slugs=["circuit-test"],
                external_urls=[],
                timeout_ms=1000,
            )

        # Second call - should fail and record failure
        with patch(
            "httpx.AsyncClient.post", side_effect=TimeoutException("Request timed out")
        ):
            result2 = await orchestrate(
                brief="Test brief",
                internal_tenant_slugs=["circuit-test"],
                external_urls=[],
                timeout_ms=1000,
            )

        # Third call - should fail and record failure
        with patch(
            "httpx.AsyncClient.post", side_effect=TimeoutException("Request timed out")
        ):
            result3 = await orchestrate(
                brief="Test brief",
                internal_tenant_slugs=["circuit-test"],
                external_urls=[],
                timeout_ms=1000,
            )

        # Fourth call - should be skipped by circuit breaker
        result4 = await orchestrate(
            brief="Test brief",
            internal_tenant_slugs=["circuit-test"],
            external_urls=[],
            timeout_ms=1000,
        )

        # Verify first three calls had timeout errors
        for result in [result1, result2, result3]:
            assert len(result["results"]) == 1
            assert result["results"][0]["error"]["type"] == "timeout"

        # Verify fourth call was skipped by circuit breaker
        assert len(result4["results"]) == 1
        assert result4["results"][0]["error"]["type"] == "breaker"
        assert "Circuit breaker open" in result4["results"][0]["error"]["message"]

    @pytest.mark.asyncio
    async def test_circuit_breaker_recovery_after_success(self):
        """Test circuit breaker recovers after successful call."""
        from httpx import TimeoutException

        # First two calls fail
        for _ in range(2):
            with patch(
                "httpx.AsyncClient.post",
                side_effect=TimeoutException("Request timed out"),
            ):
                await orchestrate(
                    brief="Test brief",
                    internal_tenant_slugs=["circuit-recovery"],
                    external_urls=[],
                    timeout_ms=1000,
                )

        # Third call succeeds - should reset circuit breaker
        mock_success = MagicMock(
            status_code=200,
            json=lambda: {
                "items": [
                    {
                        "product_id": "recovery_prod",
                        "reason": "Recovery test",
                        "score": 0.85,
                    }
                ]
            },
        )

        with patch("httpx.AsyncClient.post", return_value=mock_success):
            result = await orchestrate(
                brief="Test brief",
                internal_tenant_slugs=["circuit-recovery"],
                external_urls=[],
                timeout_ms=1000,
            )

        # Should have succeeded
        assert len(result["results"]) == 1
        assert result["results"][0]["error"] is None
        assert len(result["results"][0]["items"]) == 1

        # Next failure call should not be skipped (circuit breaker reset)
        with patch(
            "httpx.AsyncClient.post", side_effect=TimeoutException("Request timed out")
        ):
            result_failure = await orchestrate(
                brief="Test brief",
                internal_tenant_slugs=["circuit-recovery"],
                external_urls=[],
                timeout_ms=1000,
            )

        # Should not be skipped by circuit breaker
        assert result_failure["results"][0]["error"]["type"] == "timeout"
        assert "breaker" not in result_failure["results"][0]["error"]["type"]
