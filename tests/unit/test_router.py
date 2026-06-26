import pytest
from app.agents.router_node import dynamic_router
from app.core.schemas import GraphState

def test_router_forwards_to_specialists():
    state = GraphState(
        active_agents=["weather_agent", "market_agent"],
        missing_info_questions=[]
    )
    
    event = dynamic_router._func(state)
    
    assert event.actions.route == "specialists"
    assert event.output == state

def test_router_returns_direct_response_when_missing_info():
    state = GraphState(
        active_agents=["weather_agent"],
        missing_info_questions=["What is your location?"]
    )
    
    event = dynamic_router._func(state)
    
    assert event.actions.route == "direct_response"
    assert "location" in event.output

def test_router_returns_direct_response_when_no_active_agents():
    state = GraphState(
        active_agents=[],
        missing_info_questions=[]
    )
    
    event = dynamic_router._func(state)
    
    assert event.actions.route == "direct_response"
    assert event.output == "I am the Kisan Agent. How can I assist you with your farming needs today?"

def test_router_returns_final_advisory_when_no_active_agents():
    state = GraphState(
        active_agents=[],
        missing_info_questions=[],
        final_advisory="Vanakkam! I am Kisan Agent..."
    )
    
    event = dynamic_router._func(state)
    
    assert event.actions.route == "direct_response"
    assert event.output == "Vanakkam! I am Kisan Agent..."
