"""Tests for prompt precedence logic in sales agent evaluation."""

import pytest
from unittest.mock import patch, MagicMock

from app.services.sales_agent import evaluate_brief
from app.models.agent_settings import AgentSettings


class TestPromptPrecedence:
    """Test that prompt precedence works correctly."""

    @pytest.mark.asyncio
    async def test_tenant_with_prompt_override_uses_override(self):
        """Test tenant with prompt_override uses the override instead of default."""
        # Mock repositories
        mock_tenant_repo = MagicMock()
        mock_product_repo = MagicMock()
        mock_agent_settings_repo = MagicMock()

        # Mock tenant
        mock_tenant = MagicMock(id=1, name="Publisher A", slug="publisher-a")
        mock_tenant_repo.get_by_id.return_value = mock_tenant

        # Mock products
        mock_products = [
            MagicMock(
                id=1, product_id="prod_1", name="Product 1", description="Test product"
            )
        ]
        mock_product_repo.list_by_tenant.return_value = mock_products

        # Mock agent settings with prompt override
        mock_agent_settings = MagicMock(
            model_name="gemini-1.5-pro",
            timeout_ms=30000,
            prompt_override="CUSTOM PROMPT: Rank these products for {brief}",
        )
        mock_agent_settings_repo.get_by_tenant.return_value = mock_agent_settings

        # Mock AI provider response
        mock_ai_response = [
            {"product_id": "prod_1", "reason": "Custom prompt evaluation", "score": 0.9}
        ]

        with patch(
            "app.services.sales_agent.load_default_prompt",
            return_value="DEFAULT PROMPT",
        ):
            with patch(
                "app.services.sales_agent.gemini.rank_products",
                return_value=mock_ai_response,
            ) as mock_rank:
                # Call evaluate_brief
                result = await evaluate_brief(
                    tenant_id=1,
                    brief="Sports advertising",
                    agent_settings_repo=mock_agent_settings_repo,
                    product_repo=mock_product_repo,
                    tenant_repo=mock_tenant_repo,
                )

                # Verify the custom prompt was used
                mock_rank.assert_called_once()
                call_args = mock_rank.call_args
                prompt_used = call_args[0][1]  # prompt is the second argument

                assert "CUSTOM PROMPT" in prompt_used
                assert "DEFAULT PROMPT" not in prompt_used
                assert "Sports advertising" in prompt_used

                # Verify result
                assert result == mock_ai_response

    @pytest.mark.asyncio
    async def test_tenant_without_prompt_override_uses_default(self):
        """Test tenant without prompt_override uses the default prompt."""
        # Mock repositories
        mock_tenant_repo = MagicMock()
        mock_product_repo = MagicMock()
        mock_agent_settings_repo = MagicMock()

        # Mock tenant
        mock_tenant = MagicMock(id=2, name="Publisher B", slug="publisher-b")
        mock_tenant_repo.get_by_id.return_value = mock_tenant

        # Mock products
        mock_products = [
            MagicMock(
                id=2, product_id="prod_2", name="Product 2", description="Test product"
            )
        ]
        mock_product_repo.list_by_tenant.return_value = mock_products

        # Mock agent settings WITHOUT prompt override
        mock_agent_settings = MagicMock(
            model_name="gemini-1.5-pro", timeout_ms=30000, prompt_override=None
        )
        mock_agent_settings_repo.get_by_tenant.return_value = mock_agent_settings

        # Mock AI provider response
        mock_ai_response = [
            {
                "product_id": "prod_2",
                "reason": "Default prompt evaluation",
                "score": 0.8,
            }
        ]

        with patch(
            "app.services.sales_agent.load_default_prompt",
            return_value="DEFAULT PROMPT: Rank for {brief}",
        ):
            with patch(
                "app.services.sales_agent.gemini.rank_products",
                return_value=mock_ai_response,
            ) as mock_rank:
                # Call evaluate_brief
                result = await evaluate_brief(
                    tenant_id=2,
                    brief="Tech advertising",
                    agent_settings_repo=mock_agent_settings_repo,
                    product_repo=mock_product_repo,
                    tenant_repo=mock_tenant_repo,
                )

                # Verify the default prompt was used
                mock_rank.assert_called_once()
                call_args = mock_rank.call_args
                prompt_used = call_args[0][1]  # prompt is the second argument

                assert "DEFAULT PROMPT" in prompt_used
                assert "Tech advertising" in prompt_used

                # Verify result
                assert result == mock_ai_response

    @pytest.mark.asyncio
    async def test_tenant_with_empty_prompt_override_uses_default(self):
        """Test tenant with empty prompt_override uses the default prompt."""
        # Mock repositories
        mock_tenant_repo = MagicMock()
        mock_product_repo = MagicMock()
        mock_agent_settings_repo = MagicMock()

        # Mock tenant
        mock_tenant = MagicMock(id=3, name="Publisher C", slug="publisher-c")
        mock_tenant_repo.get_by_id.return_value = mock_tenant

        # Mock products
        mock_products = [
            MagicMock(
                id=3, product_id="prod_3", name="Product 3", description="Test product"
            )
        ]
        mock_product_repo.list_by_tenant.return_value = mock_products

        # Mock agent settings with empty prompt override
        mock_agent_settings = MagicMock(
            model_name="gemini-1.5-pro", timeout_ms=30000, prompt_override=""
        )
        mock_agent_settings_repo.get_by_tenant.return_value = mock_agent_settings

        # Mock AI provider response
        mock_ai_response = [
            {
                "product_id": "prod_3",
                "reason": "Default prompt evaluation",
                "score": 0.7,
            }
        ]

        with patch(
            "app.services.sales_agent.load_default_prompt",
            return_value="DEFAULT PROMPT: Rank for {brief}",
        ):
            with patch(
                "app.services.sales_agent.gemini.rank_products",
                return_value=mock_ai_response,
            ) as mock_rank:
                # Call evaluate_brief
                result = await evaluate_brief(
                    tenant_id=3,
                    brief="Food advertising",
                    agent_settings_repo=mock_agent_settings_repo,
                    product_repo=mock_product_repo,
                    tenant_repo=mock_tenant_repo,
                )

                # Verify the default prompt was used (empty override should be ignored)
                mock_rank.assert_called_once()
                call_args = mock_rank.call_args
                prompt_used = call_args[0][1]  # prompt is the second argument

                assert "DEFAULT PROMPT" in prompt_used
                assert "Food advertising" in prompt_used

                # Verify result
                assert result == mock_ai_response

    @pytest.mark.asyncio
    async def test_tenant_with_whitespace_prompt_override_uses_default(self):
        """Test tenant with whitespace-only prompt_override uses the default prompt."""
        # Mock repositories
        mock_tenant_repo = MagicMock()
        mock_product_repo = MagicMock()
        mock_agent_settings_repo = MagicMock()

        # Mock tenant
        mock_tenant = MagicMock(id=4, name="Publisher D", slug="publisher-d")
        mock_tenant_repo.get_by_id.return_value = mock_tenant

        # Mock products
        mock_products = [
            MagicMock(
                id=4, product_id="prod_4", name="Product 4", description="Test product"
            )
        ]
        mock_product_repo.list_by_tenant.return_value = mock_products

        # Mock agent settings with whitespace-only prompt override
        mock_agent_settings = MagicMock(
            model_name="gemini-1.5-pro", timeout_ms=30000, prompt_override="   \n\t   "
        )
        mock_agent_settings_repo.get_by_tenant.return_value = mock_agent_settings

        # Mock AI provider response
        mock_ai_response = [
            {
                "product_id": "prod_4",
                "reason": "Default prompt evaluation",
                "score": 0.6,
            }
        ]

        with patch(
            "app.services.sales_agent.load_default_prompt",
            return_value="DEFAULT PROMPT: Rank for {brief}",
        ):
            with patch(
                "app.services.sales_agent.gemini.rank_products",
                return_value=mock_ai_response,
            ) as mock_rank:
                # Call evaluate_brief
                result = await evaluate_brief(
                    tenant_id=4,
                    brief="Travel advertising",
                    agent_settings_repo=mock_agent_settings_repo,
                    product_repo=mock_product_repo,
                    tenant_repo=mock_tenant_repo,
                )

                # Verify the default prompt was used (whitespace-only override should be ignored)
                mock_rank.assert_called_once()
                call_args = mock_rank.call_args
                prompt_used = call_args[0][1]  # prompt is the second argument

                assert "DEFAULT PROMPT" in prompt_used
                assert "Travel advertising" in prompt_used

                # Verify result
                assert result == mock_ai_response

    @pytest.mark.asyncio
    async def test_tenant_without_agent_settings_uses_default(self):
        """Test tenant without any agent settings uses the default prompt."""
        # Mock repositories
        mock_tenant_repo = MagicMock()
        mock_product_repo = MagicMock()
        mock_agent_settings_repo = MagicMock()

        # Mock tenant
        mock_tenant = MagicMock(id=5, name="Publisher E", slug="publisher-e")
        mock_tenant_repo.get_by_id.return_value = mock_tenant

        # Mock products
        mock_products = [
            MagicMock(
                id=5, product_id="prod_5", name="Product 5", description="Test product"
            )
        ]
        mock_product_repo.list_by_tenant.return_value = mock_products

        # Mock no agent settings
        mock_agent_settings_repo.get_by_tenant.return_value = None

        # Mock AI provider response
        mock_ai_response = [
            {
                "product_id": "prod_5",
                "reason": "Default prompt evaluation",
                "score": 0.5,
            }
        ]

        with patch(
            "app.services.sales_agent.load_default_prompt",
            return_value="DEFAULT PROMPT: Rank for {brief}",
        ):
            with patch(
                "app.services.sales_agent.gemini.rank_products",
                return_value=mock_ai_response,
            ) as mock_rank:
                # Call evaluate_brief
                result = await evaluate_brief(
                    tenant_id=5,
                    brief="Fashion advertising",
                    agent_settings_repo=mock_agent_settings_repo,
                    product_repo=mock_product_repo,
                    tenant_repo=mock_tenant_repo,
                )

                # Verify the default prompt was used
                mock_rank.assert_called_once()
                call_args = mock_rank.call_args
                prompt_used = call_args[0][1]  # prompt is the second argument

                assert "DEFAULT PROMPT" in prompt_used
                assert "Fashion advertising" in prompt_used

                # Verify result
                assert result == mock_ai_response
