"""End-to-end smoke test with mocked AI provider."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from app.models.tenant import Tenant
from app.models.product import Product
from app.models.agent_settings import AgentSettings
from app.repositories.tenants import TenantRepository
from app.repositories.products import ProductRepository
from app.repositories.agent_settings import AgentSettingsRepository
from app.services.sales_agent import evaluate_brief
from app.routes.orchestrator import orchestrate


class TestEndToEndSmoke:
    """End-to-end smoke test with mocked AI provider."""

    @pytest.mark.asyncio
    async def test_end_to_end_smoke_with_mocked_ai(self):
        """Test complete end-to-end flow with mocked AI provider."""
        # Create real tenants and products via repositories
        mock_tenant_repo = MagicMock()
        mock_product_repo = MagicMock()
        mock_agent_settings_repo = MagicMock()

        # Create tenant A with custom prompt
        tenant_a = Tenant(id=1, name="Sports Publisher", slug="sports-publisher")

        # Create tenant B without custom prompt (uses default)
        tenant_b = Tenant(id=2, name="Tech Publisher", slug="tech-publisher")

        # Create products for tenant A
        products_a = [
            Product(
                id=1,
                tenant_id=1,
                product_id="sports_prod_1",
                name="Sports Banner Ad",
                description="High-visibility banner for sports websites",
            ),
            Product(
                id=2,
                tenant_id=1,
                product_id="sports_prod_2",
                name="Sports Video Ad",
                description="Video advertisement for sports content",
            ),
        ]

        # Create products for tenant B
        products_b = [
            Product(
                id=3,
                tenant_id=2,
                product_id="tech_prod_1",
                name="Tech Display Ad",
                description="Display advertisement for tech websites",
            ),
            Product(
                id=4,
                tenant_id=2,
                product_id="tech_prod_2",
                name="Tech Native Ad",
                description="Native advertisement for tech content",
            ),
        ]

        # Create agent settings for tenant A with custom prompt
        agent_settings_a = AgentSettings(
            tenant_id=1,
            model_name="gemini-1.5-pro",
            timeout_ms=30000,
            prompt_override="SPORTS PROMPT: Rank these sports products for {brief}",
        )

        # No agent settings for tenant B (uses default)

        # Mock repository responses
        mock_tenant_repo.get_by_id.side_effect = lambda id: (
            tenant_a if id == 1 else tenant_b
        )
        mock_tenant_repo.get_by_slug.side_effect = lambda slug: (
            tenant_a if slug == "sports-publisher" else tenant_b
        )
        mock_tenant_repo.list_all.return_value = [tenant_a, tenant_b]

        mock_product_repo.list_by_tenant.side_effect = lambda tenant_id: (
            products_a if tenant_id == 1 else products_b
        )

        mock_agent_settings_repo.get_by_tenant.side_effect = lambda tenant_id: (
            agent_settings_a if tenant_id == 1 else None
        )

        # Mock AI provider responses
        def mock_ai_rank_products(brief, prompt, products, model_name, timeout_ms):
            # Deterministic responses based on tenant
            if "sports" in prompt.lower():
                # Sports publisher response
                return [
                    {
                        "product_id": "sports_prod_1",
                        "reason": "Perfect match for sports advertising campaign",
                        "score": 0.95,
                    },
                    {
                        "product_id": "sports_prod_2",
                        "reason": "Good video option for sports content",
                        "score": 0.85,
                    },
                ]
            else:
                # Tech publisher response (default prompt)
                return [
                    {
                        "product_id": "tech_prod_1",
                        "reason": "Excellent display ad for tech audience",
                        "score": 0.92,
                    },
                    {
                        "product_id": "tech_prod_2",
                        "reason": "Native ad format works well for tech content",
                        "score": 0.78,
                    },
                ]

        # Test 1: Call each tenant's MCP rank endpoint
        with patch(
            "app.services.sales_agent.load_default_prompt",
            return_value="DEFAULT PROMPT: Rank for {brief}",
        ):
            with patch(
                "app.services.sales_agent.gemini.rank_products",
                side_effect=mock_ai_rank_products,
            ):
                # Test tenant A (sports publisher with custom prompt)
                result_a = await evaluate_brief(
                    tenant_id=1,
                    brief="Sports advertising campaign for young adults",
                    agent_settings_repo=mock_agent_settings_repo,
                    product_repo=mock_product_repo,
                    tenant_repo=mock_tenant_repo,
                )

                # Verify tenant A results
                assert len(result_a) == 2
                assert result_a[0]["product_id"] == "sports_prod_1"
                assert (
                    result_a[0]["reason"]
                    == "Perfect match for sports advertising campaign"
                )
                assert result_a[0]["score"] == 0.95
                assert result_a[1]["product_id"] == "sports_prod_2"
                assert result_a[1]["score"] == 0.85

                # Test tenant B (tech publisher with default prompt)
                result_b = await evaluate_brief(
                    tenant_id=2,
                    brief="Tech advertising campaign for developers",
                    agent_settings_repo=mock_agent_settings_repo,
                    product_repo=mock_product_repo,
                    tenant_repo=mock_tenant_repo,
                )

                # Verify tenant B results
                assert len(result_b) == 2
                assert result_b[0]["product_id"] == "tech_prod_1"
                assert result_b[0]["reason"] == "Excellent display ad for tech audience"
                assert result_b[0]["score"] == 0.92
                assert result_b[1]["product_id"] == "tech_prod_2"
                assert result_b[1]["score"] == 0.78

        # Test 2: Call orchestrator for both tenants
        mock_external_agent_repo = MagicMock()
        mock_external_agent_repo.list_enabled.return_value = []

        # Mock HTTP responses for orchestrator
        mock_response_a = MagicMock()
        mock_response_a.status_code = 200
        mock_response_a.json.return_value = {
            "items": [
                {
                    "product_id": "sports_prod_1",
                    "reason": "Perfect match for sports advertising campaign",
                    "score": 0.95,
                },
                {
                    "product_id": "sports_prod_2",
                    "reason": "Good video option for sports content",
                    "score": 0.85,
                },
            ]
        }

        mock_response_b = MagicMock()
        mock_response_b.status_code = 200
        mock_response_b.json.return_value = {
            "items": [
                {
                    "product_id": "tech_prod_1",
                    "reason": "Excellent display ad for tech audience",
                    "score": 0.92,
                },
                {
                    "product_id": "tech_prod_2",
                    "reason": "Native ad format works well for tech content",
                    "score": 0.78,
                },
            ]
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__ = AsyncMock(
                return_value=mock_client
            )
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

            # Mock different responses for different URLs
            def mock_post(url, **kwargs):
                if "sports-publisher" in url:
                    return mock_response_a
                elif "tech-publisher" in url:
                    return mock_response_b
                else:
                    raise Exception(f"Unexpected URL: {url}")

            mock_client.post.side_effect = mock_post

            # Create orchestrator request
            from app.routes.orchestrator import OrchestrateRequest

            request = OrchestrateRequest(
                brief="Advertising campaign for young professionals",
                internal_tenant_slugs=["sports-publisher", "tech-publisher"],
                external_urls=None,
            )

            # Call orchestrator
            result = await orchestrate(
                brief=request.brief,
                internal_tenant_slugs=request.internal_tenant_slugs,
                external_urls=request.external_urls,
                timeout_ms=5000,
            )

            # Verify orchestrator results
            assert result["total_agents"] == 2
            assert len(result["results"]) == 2

            # Verify sports publisher results
            sports_result = next(
                r for r in result["results"] if r["agent"]["slug"] == "sports-publisher"
            )
            assert sports_result["error"] is None
            assert len(sports_result["items"]) == 2
            assert sports_result["items"][0]["product_id"] == "sports_prod_1"
            assert sports_result["items"][0]["score"] == 0.95
            assert sports_result["items"][1]["product_id"] == "sports_prod_2"
            assert sports_result["items"][1]["score"] == 0.85

            # Verify tech publisher results
            tech_result = next(
                r for r in result["results"] if r["agent"]["slug"] == "tech-publisher"
            )
            assert tech_result["error"] is None
            assert len(tech_result["items"]) == 2
            assert tech_result["items"][0]["product_id"] == "tech_prod_1"
            assert tech_result["items"][0]["score"] == 0.92
            assert tech_result["items"][1]["product_id"] == "tech_prod_2"
            assert tech_result["items"][1]["score"] == 0.78

            # Verify ordering is preserved (sports first, tech second)
            assert result["results"][0]["agent"]["slug"] == "sports-publisher"
            assert result["results"][1]["agent"]["slug"] == "tech-publisher"

    @pytest.mark.asyncio
    async def test_end_to_end_with_partial_failures(self):
        """Test end-to-end flow with one agent failing."""
        # Create real tenants and products
        mock_tenant_repo = MagicMock()
        mock_product_repo = MagicMock()
        mock_agent_settings_repo = MagicMock()
        mock_external_agent_repo = MagicMock()

        # Create tenants
        tenant_a = Tenant(id=1, name="Publisher A", slug="publisher-a")
        tenant_b = Tenant(id=2, name="Publisher B", slug="publisher-b")

        # Create products
        products_a = [
            Product(
                id=1,
                tenant_id=1,
                product_id="prod_a_1",
                name="Product A1",
                description="Test product",
            )
        ]
        products_b = [
            Product(
                id=2,
                tenant_id=2,
                product_id="prod_b_1",
                name="Product B1",
                description="Test product",
            )
        ]

        # Mock repository responses
        mock_tenant_repo.get_by_id.side_effect = lambda id: (
            tenant_a if id == 1 else tenant_b
        )
        mock_tenant_repo.get_by_slug.side_effect = lambda slug: (
            tenant_a if slug == "publisher-a" else tenant_b
        )
        mock_tenant_repo.list_all.return_value = [tenant_a, tenant_b]

        mock_product_repo.list_by_tenant.side_effect = lambda tenant_id: (
            products_a if tenant_id == 1 else products_b
        )
        mock_agent_settings_repo.get_by_tenant.return_value = None
        mock_external_agent_repo.list_enabled.return_value = []

        # Mock AI provider - tenant A succeeds, tenant B fails
        def mock_ai_rank_products(brief, prompt, products, model_name, timeout_ms):
            if "publisher-a" in str(products[0].tenant_id):
                return [
                    {
                        "product_id": "prod_a_1",
                        "reason": "Successful match",
                        "score": 0.9,
                    }
                ]
            else:
                raise Exception("AI provider error for tenant B")

        # Mock HTTP responses for orchestrator
        mock_success_response = MagicMock()
        mock_success_response.status_code = 200
        mock_success_response.json.return_value = {
            "items": [
                {"product_id": "prod_a_1", "reason": "Successful match", "score": 0.9}
            ]
        }

        mock_failure_response = MagicMock()
        mock_failure_response.status_code = 500
        mock_failure_response.json.return_value = {
            "error": {
                "type": "internal",
                "message": "AI provider error for tenant B",
                "status": 500,
            }
        }

        with patch(
            "app.services.sales_agent.load_default_prompt",
            return_value="DEFAULT PROMPT",
        ):
            with patch(
                "app.services.sales_agent.gemini.rank_products",
                side_effect=mock_ai_rank_products,
            ):
                with patch("httpx.AsyncClient") as mock_client_class:
                    mock_client = AsyncMock()
                    mock_client_class.return_value.__aenter__ = AsyncMock(
                        return_value=mock_client
                    )
                    mock_client_class.return_value.__aexit__ = AsyncMock(
                        return_value=None
                    )

                    # Mock different responses for different URLs
                    def mock_post(url, **kwargs):
                        if "publisher-a" in url:
                            return mock_success_response
                        elif "publisher-b" in url:
                            return mock_failure_response
                        else:
                            raise Exception(f"Unexpected URL: {url}")

                    mock_client.post.side_effect = mock_post

                    # Create orchestrator request
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
                        timeout_ms=5000,
                    )

                    # Verify results
                    assert result["total_agents"] == 2
                    assert len(result["results"]) == 2

                    # Verify success for tenant A
                    success_result = next(
                        r
                        for r in result["results"]
                        if r["agent"]["slug"] == "publisher-a"
                    )
                    assert success_result["error"] is None
                    assert len(success_result["items"]) == 1
                    assert success_result["items"][0]["product_id"] == "prod_a_1"

                    # Verify failure for tenant B
                    failure_result = next(
                        r
                        for r in result["results"]
                        if r["agent"]["slug"] == "publisher-b"
                    )
                    assert failure_result["error"] is not None
                    assert failure_result["error"]["type"] == "internal"
                    assert len(failure_result["items"]) == 0
