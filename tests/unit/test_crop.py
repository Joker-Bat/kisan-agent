from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agents.crop_agent import crop_node
from app.core.schemas import CropOutput, FarmerProfile, GraphState
from app.providers.crop.local_csv import LocalCsvCropProvider


class MockContext:
    def __init__(self):
        self.run_node = AsyncMock()


@pytest.mark.asyncio
async def test_crop_node_skipped_when_not_active():
    ctx = MockContext()
    state = GraphState(active_agents=[])
    res = await crop_node._func(ctx, state)
    assert res == "SKIPPED"


def test_local_csv_crop_provider_lazy_loading():
    # Load dataset stats
    provider = LocalCsvCropProvider()
    assert len(provider.stats) == 0  # Not loaded yet (lazy load)

    # Run a match to trigger lazy loading
    matches = provider.match_crops(n=90, p=42, k=43, ph=6.5)
    assert len(provider.stats) > 0  # Loaded and cached
    assert len(matches) > 0
    assert (
        matches[0]["crop"] == "rice"
    )  # Rice is the exact match for these centroid NPK values!


def test_local_csv_crop_provider_matching():
    provider = LocalCsvCropProvider()
    matches = provider.match_crops(n=50, p=50, k=50, ph=6.0)
    assert len(matches) == 5
    for m in matches:
        assert "crop" in m
        assert "compatibility" in m
        assert "distance" in m


@pytest.mark.asyncio
async def test_crop_node_integration(monkeypatch):
    ctx = MockContext()
    ctx.run_node.return_value = CropOutput(
        recommended_crops=["rice", "maize"],
        rationale="Based on 98% compatibility with soil NPK...",
    )

    state = GraphState(
        active_agents=["crop_agent"],
        profile=FarmerProfile(n_val=90, p_val=42, k_val=43, ph_val=6.5),
    )

    from app.providers.registry import active_crop_provider

    mock_match = MagicMock()
    mock_match.return_value = [
        {"crop": "rice", "compatibility": 100.0, "distance": 0.0},
        {"crop": "maize", "compatibility": 85.0, "distance": 1.5},
    ]
    monkeypatch.setattr(active_crop_provider, "match_crops", mock_match)

    res = await crop_node._func(ctx, state)

    mock_match.assert_called_once_with(n=90, p=42, k=43, ph=6.5, temperature=None)
    assert res.recommended_crops == ["rice", "maize"]
    assert "98% compatibility" in res.rationale
