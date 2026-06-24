import pytest
from app.agents.synthesis_agent import synthesis_node
from app.core.schemas import FarmerProfile, GraphState

class MockContext:
    def __init__(self):
        self.state = {"profile": {"location_name": "Madurai"}}

    async def run_node(self, node, node_input=None, **kwargs):
        return f"Mock synthesis for: {node_input}"

@pytest.mark.asyncio
async def test_synthesis_node_formatting():
    node_input = {
        "weather": "Heavy rain tomorrow.",
        "market": "Tomatoes at ₹20/kg.",
        "active_agents": ["weather", "market"]
    }
    
    ctx = MockContext()
    
    # Run the node's underlying function directly
    prompt = await synthesis_node._func(ctx, node_input)
    
    assert "Mock synthesis for" in prompt
    assert "Heavy rain" in prompt
