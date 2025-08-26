"""Tests for MCP error handling and validation."""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.responses import JSONResponse

from app.routes.mcp import rank_products
from app.ai.errors import AIConfigError, AITimeoutError, AIRequestError


class TestMCPErrors:
    """Test MCP error handling and validation."""

    @pytest.mark.asyncio
    async def test_rank_products_unknown_tenant(self):
        """Test POST /mcp/agents/{slug}/rank with unknown tenant slug."""
        # Mock repositories
        mock_tenant_repo = MagicMock()
        mock_product_repo = MagicMock()
        mock_agent_settings_repo = MagicMock()

        # Mock tenant not found
        mock_tenant_repo.get_by_slug.return_value = None

        # Create request
        from app.routes.mcp import AdCPRankingRequest

        request = AdCPRankingRequest(brief="Test brief")

        # Call function
        result = await rank_products(
            tenant_slug="unknown-tenant",
            request=request,
            tenant_repo=mock_tenant_repo,
            product_repo=mock_product_repo,
            agent_settings_repo=mock_agent_settings_repo,
        )

        # Verify 404 error response
        assert isinstance(result, JSONResponse)
        assert result.status_code == 404
        content = result.body.decode()
        assert "Tenant 'unknown-tenant' not found" in content
        assert '"type":"invalid_request"' in content

    @pytest.mark.asyncio
    async def test_rank_products_missing_brief(self):
        """Test POST /mcp/agents/{slug}/rank with missing brief."""
        # Mock repositories
        mock_tenant_repo = MagicMock()
        mock_product_repo = MagicMock()
        mock_agent_settings_repo = MagicMock()

        # Mock tenant
        mock_tenant = MagicMock(id=1, slug="publisher-a")
        mock_tenant_repo.get_by_slug.return_value = mock_tenant

        # Create request with empty brief
        from app.routes.mcp import AdCPRankingRequest

        request = AdCPRankingRequest(brief="")

        # Call function
        result = await rank_products(
            tenant_slug="publisher-a",
            request=request,
            tenant_repo=mock_tenant_repo,
            product_repo=mock_product_repo,
            agent_settings_repo=mock_agent_settings_repo,
        )

        # Verify 400 error response
        assert isinstance(result, JSONResponse)
        assert result.status_code == 400
        content = result.body.decode()
        assert "Brief is required and must be non-empty" in content
        assert '"type":"invalid_request"' in content

    @pytest.mark.asyncio
    async def test_rank_products_whitespace_brief(self):
        """Test POST /mcp/agents/{slug}/rank with whitespace-only brief."""
        # Mock repositories
        mock_tenant_repo = MagicMock()
        mock_product_repo = MagicMock()
        mock_agent_settings_repo = MagicMock()

        # Mock tenant
        mock_tenant = MagicMock(id=1, slug="publisher-a")
        mock_tenant_repo.get_by_slug.return_value = mock_tenant

        # Create request with whitespace-only brief
        from app.routes.mcp import AdCPRankingRequest

        request = AdCPRankingRequest(brief="   \n\t   ")

        # Call function
        result = await rank_products(
            tenant_slug="publisher-a",
            request=request,
            tenant_repo=mock_tenant_repo,
            product_repo=mock_product_repo,
            agent_settings_repo=mock_agent_settings_repo,
        )

        # Verify 400 error response
        assert isinstance(result, JSONResponse)
        assert result.status_code == 400
        content = result.body.decode()
        assert "Brief is required and must be non-empty" in content

    @pytest.mark.asyncio
    async def test_rank_products_no_products(self):
        """Test POST /mcp/agents/{slug}/rank with tenant that has no products."""
        # Mock repositories
        mock_tenant_repo = MagicMock()
        mock_product_repo = MagicMock()
        mock_agent_settings_repo = MagicMock()

        # Mock tenant
        mock_tenant = MagicMock(id=1, slug="publisher-a")
        mock_tenant_repo.get_by_slug.return_value = mock_tenant

        # Mock no products
        mock_product_repo.list_by_tenant.return_value = []

        # Create request
        from app.routes.mcp import AdCPRankingRequest

        request = AdCPRankingRequest(brief="Test brief")

        # Call function
        result = await rank_products(
            tenant_slug="publisher-a",
            request=request,
            tenant_repo=mock_tenant_repo,
            product_repo=mock_product_repo,
            agent_settings_repo=mock_agent_settings_repo,
        )

        # Verify 422 error response
        assert isinstance(result, JSONResponse)
        assert result.status_code == 422
        content = result.body.decode()
        assert "No products found for tenant 'publisher-a'" in content
        assert "Please add products before using AI evaluation" in content

    @pytest.mark.asyncio
    async def test_rank_products_ai_config_error(self):
        """Test POST /mcp/agents/{slug}/rank with AIConfigError."""
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

        # Mock AIConfigError
        with patch(
            "app.routes.mcp.evaluate_brief",
            side_effect=AIConfigError("Missing API key"),
        ):
            # Create request
            from app.routes.mcp import AdCPRankingRequest

            request = AdCPRankingRequest(brief="Test brief")

            # Call function
            result = await rank_products(
                tenant_slug="publisher-a",
                request=request,
                tenant_repo=mock_tenant_repo,
                product_repo=mock_product_repo,
                agent_settings_repo=mock_agent_settings_repo,
            )

            # Verify 500 error response with ai_config_error type
            assert isinstance(result, JSONResponse)
            assert result.status_code == 500
            content = result.body.decode()
            assert '"type":"ai_config_error"' in content
            assert "Missing API key" in content

    @pytest.mark.asyncio
    async def test_rank_products_ai_timeout_error(self):
        """Test POST /mcp/agents/{slug}/rank with AITimeoutError."""
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

        # Mock AITimeoutError
        with patch(
            "app.routes.mcp.evaluate_brief",
            side_effect=AITimeoutError("Request timed out"),
        ):
            # Create request
            from app.routes.mcp import AdCPRankingRequest

            request = AdCPRankingRequest(brief="Test brief")

            # Call function
            result = await rank_products(
                tenant_slug="publisher-a",
                request=request,
                tenant_repo=mock_tenant_repo,
                product_repo=mock_product_repo,
                agent_settings_repo=mock_agent_settings_repo,
            )

            # Verify 408 error response with timeout type
            assert isinstance(result, JSONResponse)
            assert result.status_code == 408
            content = result.body.decode()
            assert '"type":"timeout"' in content
            assert "Request timed out" in content

    @pytest.mark.asyncio
    async def test_rank_products_ai_request_error(self):
        """Test POST /mcp/agents/{slug}/rank with AIRequestError."""
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

        # Mock AIRequestError
        with patch(
            "app.routes.mcp.evaluate_brief",
            side_effect=AIRequestError("Invalid response"),
        ):
            # Create request
            from app.routes.mcp import AdCPRankingRequest

            request = AdCPRankingRequest(brief="Test brief")

            # Call function
            result = await rank_products(
                tenant_slug="publisher-a",
                request=request,
                tenant_repo=mock_tenant_repo,
                product_repo=mock_product_repo,
                agent_settings_repo=mock_agent_settings_repo,
            )

            # Verify 502 error response with ai_request_error type
            assert isinstance(result, JSONResponse)
            assert result.status_code == 502
            content = result.body.decode()
            assert '"type":"ai_request_error"' in content
            assert "Invalid response" in content

    @pytest.mark.asyncio
    async def test_rank_products_unexpected_error(self):
        """Test POST /mcp/agents/{slug}/rank with unexpected error."""
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

        # Mock unexpected error
        with patch(
            "app.routes.mcp.evaluate_brief", side_effect=Exception("Unexpected error")
        ):
            # Create request
            from app.routes.mcp import AdCPRankingRequest

            request = AdCPRankingRequest(brief="Test brief")

            # Call function
            result = await rank_products(
                tenant_slug="publisher-a",
                request=request,
                tenant_repo=mock_tenant_repo,
                product_repo=mock_product_repo,
                agent_settings_repo=mock_agent_settings_repo,
            )

            # Verify 500 error response with internal type
            assert isinstance(result, JSONResponse)
            assert result.status_code == 500
            content = result.body.decode()
            assert '"type":"internal"' in content
            assert "Unexpected error" in content
