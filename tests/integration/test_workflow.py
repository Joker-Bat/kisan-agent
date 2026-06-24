import pytest
import asyncio
from google.adk.runners import InMemoryRunner
from google.genai import types
from app.agent import app
from app.core.schemas import GraphState

@pytest.mark.asyncio
async def test_workflow_live_api():
    runner = InMemoryRunner(app=app)
    session = await runner.session_service.create_session(app_name="app", user_id="test_user")
    session_id = session.id
    
    # --- Turn 1: Partial Query ---
    print("Sending Turn 1...")
    response_text = ""
    async for event in runner.run_async(
        user_id="test_user",
        session_id=session_id,
        new_message=types.Content(role="user", parts=[types.Part.from_text(text="What is the weather for my farm?")])
    ):
        if hasattr(event, "output") and event.output:
            response_text += str(event.output)
            
    print(f"Turn 1 Response: {response_text}")
    assert "location" in response_text.lower() or "where" in response_text.lower()
    
    # Verify the memory persisted that the active agent is weather_agent
    session = await runner.session_service.get_session(session_id=session_id, app_name="app", user_id="test_user")
    state_dict = session.state.to_dict() if hasattr(session.state, "to_dict") else dict(session.state)
    assert "weather_agent" in state_dict.get("active_agents", [])
    
    # --- Turn 2: Providing the Missing Info ---
    print("Sending Turn 2...")
    response_text = ""
    async for event in runner.run_async(
        user_id="test_user",
        session_id=session_id,
        new_message=types.Content(role="user", parts=[types.Part.from_text(text="I am in Salem, Tamil Nadu")])
    ):
        if hasattr(event, "output") and event.output:
            response_text += str(event.output)
            
    print(f"Turn 2 Response: {response_text}")
    
    # The final output should have weather data in it
    assert "temperature" in response_text.lower() or "weather" in response_text.lower() or "salem" in response_text.lower()
    
    # Verify memory contains the location
    session = await runner.session_service.get_session(session_id=session_id, app_name="app", user_id="test_user")
    state_dict = session.state.to_dict() if hasattr(session.state, "to_dict") else dict(session.state)
    assert state_dict["profile"]["location_name"].lower() == "salem"
    
    # The final output should have weather data in it
    assert "temperature" in response_text.lower() or "weather" in response_text.lower() or "salem" in response_text.lower()
    
    # Verify memory contains the location
    session = await runner.session_service.get_session(session_id=session_id, app_name="app", user_id="test_user")
    state_dict = session.state.to_dict() if hasattr(session.state, "to_dict") else dict(session.state)
    assert state_dict["profile"]["location_name"].lower() == "salem"
