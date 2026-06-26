import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agents.weather_agent import weather_node
from app.core.schemas import FarmerProfile, GraphState, WeatherOutput
from app.providers.weather.open_meteo import OpenMeteoProvider


class MockContext:
    def __init__(self):
        self.run_node = AsyncMock()


@pytest.mark.asyncio
async def test_weather_node_skipped_when_not_active():
    ctx = MockContext()
    state = GraphState(active_agents=[])
    res = await weather_node._func(ctx, state)
    assert res == "SKIPPED"


@pytest.mark.asyncio
async def test_weather_node_custom_range(monkeypatch):
    ctx = MockContext()
    ctx.run_node.return_value = WeatherOutput(
        summary="Clear weather for Salem",
        forecast_days=[{"time": "2026-06-25", "precipitation_sum": 0.0}],
    )

    state = GraphState(
        active_agents=["weather_agent"],
        profile=FarmerProfile(
            latitude=11.6643,
            longitude=78.146,
            weather_start_date="2026-06-25",
            weather_end_date="2026-06-27",
        ),
    )

    from app.providers.registry import active_weather_provider

    mock_fetch = MagicMock()
    mock_fetch.return_value = {
        "daily": {
            "time": ["2026-06-25", "2026-06-26", "2026-06-27"],
            "precipitation_sum": [0.0, 0.0, 0.0],
        },
        "daily_units": {"time": "iso8601", "precipitation_sum": "mm"},
    }
    monkeypatch.setattr(active_weather_provider, "fetch_forecast", mock_fetch)

    res = await weather_node._func(ctx, state)

    mock_fetch.assert_called_once_with(
        11.6643, 78.146, start_date="2026-06-25", end_date="2026-06-27"
    )
    assert res.summary == "Clear weather for Salem"
    assert len(res.forecast_days) == 1


def test_open_meteo_provider_routing(monkeypatch):
    provider = OpenMeteoProvider()
    mock_get = MagicMock()
    monkeypatch.setattr("httpx.get", mock_get)

    # 1. Test standard forecast (no dates)
    provider.fetch_forecast(11.6643, 78.146)
    mock_get.assert_called_once()
    args, kwargs = mock_get.call_args
    assert args[0] == "https://api.open-meteo.com/v1/forecast"
    assert kwargs["params"]["forecast_days"] == 14

    mock_get.reset_mock()

    # 2. Test recent range (within 90 days)
    today = datetime.date.today()
    start_date = (today - datetime.timedelta(days=10)).isoformat()
    end_date = today.isoformat()
    provider.fetch_forecast(11.6643, 78.146, start_date=start_date, end_date=end_date)
    args, kwargs = mock_get.call_args
    assert args[0] == "https://api.open-meteo.com/v1/forecast"
    assert kwargs["params"]["start_date"] == start_date
    assert kwargs["params"]["end_date"] == end_date

    mock_get.reset_mock()

    # 3. Test older historical range (beyond 90 days)
    old_start_date = (today - datetime.timedelta(days=100)).isoformat()
    old_end_date = (today - datetime.timedelta(days=95)).isoformat()
    provider.fetch_forecast(
        11.6643, 78.146, start_date=old_start_date, end_date=old_end_date
    )
    args, kwargs = mock_get.call_args
    assert args[0] == "https://archive-api.open-meteo.com/v1/archive"
    assert kwargs["params"]["start_date"] == old_start_date
    assert kwargs["params"]["end_date"] == old_end_date
