"""Tests for successful MCP endpoint calls."""

import pytest
from unittest.mock import patch, MagicMock

from app.routes.mcp import get_mcp_info, rank_products


class TestMCPEndpoint:
    """Test successful MCP endpoint calls."""

    @pytest.mark.asyncio
    async def test_get_mcp_info_success(self):
        """Test GET /mcp/ returns service information."""
        with patch("os.getenv", return_value="adcp-demo-0.1"):
            with patch("subprocess.run") as mock_subprocess:
                mock_subprocess.return_value.returncode = 0
                mock_subprocess.return_value.stdout = "abc123\n"

                result = await get_mcp_info()

                assert result["service"] == "AdCP Demo Orchestrator"
                assert result["adcp_version"] == "adcp-demo-0.1"
                assert result["commit_hash"] == "abc123"
                assert result["capabilities"] == ["ranking"]

    @pytest.mark.asyncio
    async def test_get_mcp_info_git_fallback(self):
        """Test GET /mcp/ handles git command failure gracefully."""
        with patch("os.getenv", return_value="adcp-demo-0.1"):
            with patch("subprocess.run", side_effect=FileNotFoundError()):
                result = await get_mcp_info()

                assert result["service"] == "AdCP Demo Orchestrator"
                assert result["adcp_version"] == "adcp-demo-0.1"
                assert result["commit_hash"] == "unknown"
                assert result["capabilities"] == ["ranking"]

    @pytest.mark.asyncio
    async def test_rank_products_success(self):
        """Test POST /mcp/agents/{slug}/rank with valid request."""
        # Mock repositories
        mock_tenant_repo = MagicMock()
        mock_product_repo = MagicMock()
        mock_agent_settings_repo = MagicMock()

        # Mock tenant
        mock_tenant = MagicMock(id=1, slug="publisher-a")
        mock_tenant_repo.get_by_slug.return_value = mock_tenant

        # Mock products
        mock_products = [MagicMock(id=1, product_id="prod_1")]
        mock_product_repo.list_by_tenant.return_value = mock_products

        # Mock sales agent response
        mock_sales_agent_response = [
            {
                "product_id": "prod_1",
                "reason": "Perfect match for sports advertising",
                "score": 0.95,
            },
            {"product_id": "prod_2", "reason": "Good demographic fit", "score": 0.85},
        ]

        with patch(
            "app.routes.mcp.evaluate_brief", return_value=mock_sales_agent_response
        ):
            # Create request
            from app.routes.mcp import AdCPRankingRequest

            request = AdCPRankingRequest(brief="Sports advertising campaign")

            # Call function
            result = await rank_products(
                tenant_slug="publisher-a",
                request=request,
                tenant_repo=mock_tenant_repo,
                product_repo=mock_product_repo,
                agent_settings_repo=mock_agent_settings_repo,
            )

            # Verify result
            assert result["items"] == mock_sales_agent_response
            assert len(result["items"]) == 2
            assert result["items"][0]["product_id"] == "prod_1"
            assert (
                result["items"][0]["reason"] == "Perfect match for sports advertising"
            )
            assert result["items"][0]["score"] == 0.95

    @pytest.mark.asyncio
    async def test_rank_products_with_context_id(self):
        """Test POST /mcp/agents/{slug}/rank with context_id."""
        # Mock repositories
        mock_tenant_repo = MagicMock()
        mock_product_repo = MagicMock()
        mock_agent_settings_repo = MagicMock()

        # Mock tenant
        mock_tenant = MagicMock(id=1, slug="publisher-a")
        mock_tenant_repo.get_by_slug.return_value = mock_tenant

        # Mock products
        mock_products = [MagicMock(id=1, product_id="prod_1")]
        mock_product_repo.list_by_tenant.return_value = mock_products

        # Mock sales agent response
        mock_sales_agent_response = [
            {"product_id": "prod_1", "reason": "Test response", "score": 0.9}
        ]

        with patch(
            "app.routes.mcp.evaluate_brief", return_value=mock_sales_agent_response
        ):
            # Create request with context_id
            from app.routes.mcp import AdCPRankingRequest

            request = AdCPRankingRequest(brief="Test brief", context_id="ctx-123")

            # Call function
            result = await rank_products(
                tenant_slug="publisher-a",
                request=request,
                tenant_repo=mock_tenant_repo,
                product_repo=mock_product_repo,
                agent_settings_repo=mock_agent_settings_repo,
            )

            # Verify result (context_id should be ignored in response)
            assert result["items"] == mock_sales_agent_response
            assert len(result["items"]) == 1

    @pytest.mark.asyncio
    async def test_rank_products_no_score(self):
        """Test POST /mcp/agents/{slug}/rank with items that don't have scores."""
        # Mock repositories
        mock_tenant_repo = MagicMock()
        mock_product_repo = MagicMock()
        mock_agent_settings_repo = MagicMock()

        # Mock tenant
        mock_tenant = MagicMock(id=1, slug="publisher-a")
        mock_tenant_repo.get_by_slug.return_value = mock_tenant

        # Mock products
        mock_products = [MagicMock(id=1, product_id="prod_1")]
        mock_product_repo.list_by_tenant.return_value = mock_products

        # Mock sales agent response without scores
        mock_sales_agent_response = [
            {"product_id": "prod_1", "reason": "Perfect match for sports advertising"},
            {"product_id": "prod_2", "reason": "Good demographic fit"},
        ]

        with patch(
            "app.routes.mcp.evaluate_brief", return_value=mock_sales_agent_response
        ):
            # Create request
            from app.routes.mcp import AdCPRankingRequest

            request = AdCPRankingRequest(brief="Sports advertising campaign")

            # Call function
            result = await rank_products(
                tenant_slug="publisher-a",
                request=request,
                tenant_repo=mock_tenant_repo,
                product_repo=mock_product_repo,
                agent_settings_repo=mock_agent_settings_repo,
            )

            # Verify result
            assert result["items"] == mock_sales_agent_response
            assert len(result["items"]) == 2
            assert "score" not in result["items"][0]
            assert "score" not in result["items"][1]

    @pytest.mark.asyncio
    async def test_rank_products_preserves_order(self):
        """Test POST /mcp/agents/{slug}/rank preserves the order from sales agent."""
        # Mock repositories
        mock_tenant_repo = MagicMock()
        mock_product_repo = MagicMock()
        mock_agent_settings_repo = MagicMock()

        # Mock tenant
        mock_tenant = MagicMock(id=1, slug="publisher-a")
        mock_tenant_repo.get_by_slug.return_value = mock_tenant

        # Mock products
        mock_products = [MagicMock(id=1, product_id="prod_1")]
        mock_product_repo.list_by_tenant.return_value = mock_products

        # Mock sales agent response with specific order
        mock_sales_agent_response = [
            {"product_id": "prod_3", "reason": "Third best match", "score": 0.7},
            {"product_id": "prod_1", "reason": "Best match", "score": 0.95},
            {"product_id": "prod_2", "reason": "Second best match", "score": 0.85},
        ]

        with patch(
            "app.routes.mcp.evaluate_brief", return_value=mock_sales_agent_response
        ):
            # Create request
            from app.routes.mcp import AdCPRankingRequest

            request = AdCPRankingRequest(brief="Sports advertising campaign")

            # Call function
            result = await rank_products(
                tenant_slug="publisher-a",
                request=request,
                tenant_repo=mock_tenant_repo,
                product_repo=mock_product_repo,
                agent_settings_repo=mock_agent_settings_repo,
            )

            # Verify order is preserved
            assert result["items"] == mock_sales_agent_response
            assert result["items"][0]["product_id"] == "prod_3"
            assert result["items"][1]["product_id"] == "prod_1"
            assert result["items"][2]["product_id"] == "prod_2"
