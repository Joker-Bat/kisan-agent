import pytest
from app.agents.synthesis_agent import prepare_synthesis

def test_synthesis_formatter():
    node_input = {
        "weather_info": "Sunny",
        "market_info": "Prices up"
    }
    
    prompt = prepare_synthesis(node_input)
    
    assert "Sunny" in prompt
    assert "Prices up" in prompt
    assert "Synthesize the following agricultural data into a bilingual advisory" in prompt
