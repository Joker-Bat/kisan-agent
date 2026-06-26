from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agents.market_agent import market_node
from app.core.schemas import FarmerProfile, GraphState, MarketOutput


class MockContext:
    def __init__(self):
        self.run_node = AsyncMock()


@pytest.mark.asyncio
async def test_market_node_skipped_when_not_active():
    ctx = MockContext()
    state = GraphState(active_agents=[])
    res = await market_node._func(ctx, state)
    assert res == "SKIPPED"


@pytest.mark.asyncio
async def test_market_node_missing_credentials(monkeypatch):
    ctx = MockContext()
    state = GraphState(
        active_agents=["market_agent"],
        profile=FarmerProfile(crop_intent=["tomato"], state="Tamil Nadu"),
    )

    from app.core.config import settings

    original_key = settings.DATA_GOV_IN_API_KEY
    settings.DATA_GOV_IN_API_KEY = None

    try:
        res = await market_node._func(ctx, state)
        assert res.crop == "tomato"
        assert res.state == "Tamil Nadu"
        assert "not configured" in res.summary
    finally:
        settings.DATA_GOV_IN_API_KEY = original_key


@pytest.mark.asyncio
async def test_market_node_multiple_crops(monkeypatch):
    ctx = MockContext()
    ctx.run_node.side_effect = lambda node, node_input, **kwargs: MarketOutput(
        crop="Cotton, Sorghum",
        state="Tamil Nadu",
        prices=[
            {
                "state": "Tamil Nadu",
                "district": "Salem",
                "commodity": "Cotton",
                "modal_price": "6000",
            },
            {
                "state": "Tamil Nadu",
                "district": "Salem",
                "commodity": "Sorghum",
                "modal_price": "2500",
            },
        ],
        summary="Here are the prices for Cotton and Sorghum in Tamil Nadu...",
    )

    state = GraphState(
        active_agents=["market_agent"],
        profile=FarmerProfile(crop_intent=["Cotton", "Sorghum"], state="Tamil Nadu"),
    )

    # Mock the API key so it does not trigger missing key error
    from app.core.config import settings

    monkeypatch.setattr(settings, "DATA_GOV_IN_API_KEY", "dummy_key")

    # Mock the fetch_prices method of active_market_provider
    from app.providers.registry import active_market_provider

    mock_fetch = AsyncMock()

    async def side_effect(crop, state, district=None, market=None):
        if crop == "Cotton":
            return [
                {
                    "state": state,
                    "district": "Salem",
                    "commodity": "Cotton",
                    "modal_price": "6000",
                }
            ]
        elif crop == "Sorghum":
            return [
                {
                    "state": state,
                    "district": "Salem",
                    "commodity": "Sorghum",
                    "modal_price": "2500",
                }
            ]
        return []

    mock_fetch.side_effect = side_effect
    monkeypatch.setattr(active_market_provider, "fetch_prices", mock_fetch)

    res = await market_node._func(ctx, state)

    assert mock_fetch.call_count == 2
    mock_fetch.assert_any_call(
        crop="Cotton", state="Tamil Nadu", district=None, market=None
    )
    mock_fetch.assert_any_call(
        crop="Sorghum", state="Tamil Nadu", district=None, market=None
    )
    assert res.crop == "Cotton, Sorghum"
    assert len(res.prices) == 2
    assert "Cotton" in res.summary
