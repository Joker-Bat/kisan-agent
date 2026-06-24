import pytest
import asyncio
from unittest.mock import AsyncMock
from app.agents.router_node import dynamic_router_logic
from app.core.schemas import GraphState

class MockContext:
    def __init__(self):
        self.run_node = AsyncMock(return_value="mocked_result")

@pytest.mark.asyncio
async def test_router_forwards_to_active_agents():
    ctx = MockContext()
    state = GraphState(
        active_agents=["weather_agent", "market_agent"],
        missing_info_questions=[]
    )
    
    # Run the logic function directly
    event = await dynamic_router_logic(ctx, state)
    
    assert event.actions.route == "synthesis"
    assert ctx.run_node.call_count == 2
    
@pytest.mark.asyncio
async def test_router_returns_direct_response_when_missing_info():
    ctx = MockContext()
    state = GraphState(
        active_agents=["weather_agent"],
        missing_info_questions=["What is your location?"]
    )
    
    event = await dynamic_router_logic(ctx, state)
    
    assert event.actions.route == "direct_response"
    assert "location" in event.output

@pytest.mark.asyncio
async def test_router_returns_direct_response_when_no_active_agents():
    ctx = MockContext()
    state = GraphState(
        active_agents=[],
        missing_info_questions=[]
    )
    
    event = await dynamic_router_logic(ctx, state)
    
    assert event.actions.route == "direct_response"
