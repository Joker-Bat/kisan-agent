from unittest.mock import AsyncMock

import pytest

from app.agents.orchestrator_agent import orchestrator_logic


class MockState:
    def __init__(self, initial_data=None):
        self._data = initial_data or {}

    def to_dict(self):
        return self._data

    def update(self, delta):
        self._data.update(delta)

    def get(self, key, default=None):
        return self._data.get(key, default)


class MockContext:
    def __init__(self, initial_state=None):
        self.state = MockState(initial_state)
        self.run_node = AsyncMock()


@pytest.mark.asyncio
async def test_orchestrator_extracts_and_routes():
    # Setup the mocked environment
    ctx = MockContext(initial_state={"profile": {"location_name": "Salem"}})

    # Mock what the LLM would return for a follow-up query
    ctx.run_node.return_value = {
        "user_query": "I have 5 acres",
        "profile": {"land_size_acres": 5.0},
        "active_agents": ["crop_agent"],
        "missing_info_questions": [],
        "weather_info": None,
        "market_info": None,
        "crop_info": None,
        "scheme_info": None,
        "final_advisory": "Vanakkam! I am Kisan Agent...",
    }

    # Run the logic
    event = await orchestrator_logic(ctx, "I have 5 acres")

    # Assert LLM was called
    ctx.run_node.assert_called_once()

    # Assert that the returned Event contains the correct state delta to be merged by ADK
    assert (
        event.actions.state_delta["profile"]["location_name"] == "Salem"
    )  # Retained old memory
    assert (
        event.actions.state_delta["profile"]["land_size_acres"] == 5.0
    )  # Merged new memory
    assert (
        event.actions.state_delta["final_advisory"] == "Vanakkam! I am Kisan Agent..."
    )

    # Assert that the Event emitted contains the unified downstream output
    assert event.output.profile.location_name == "Salem"
    assert event.output.profile.land_size_acres == 5.0
    assert "crop_agent" in event.output.active_agents
    assert event.output.final_advisory == "Vanakkam! I am Kisan Agent..."
