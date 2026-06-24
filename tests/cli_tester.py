import asyncio
import sys
import uuid
from google.adk.runners import InMemoryRunner
from google.genai import types
from app.agent import app

async def main():
    print("========================================")
    print(" Kisan Agent Interactive CLI Tester ")
    print(" Type 'quit' or 'exit' to stop")
    print("========================================")
    
    runner = InMemoryRunner(app=app)
    
    # Generate a session
    session = await runner.session_service.create_session(app_name="app", user_id="cli_tester")
    session_id = session.id
    user_id = "cli_tester"
    
    print(f"\n[System] Created Session: {session_id}\n")
    
    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ['quit', 'exit']:
                break
                
            if not user_input.strip():
                continue
                
            print("\n[Agent is thinking...]")
            
            # Run the graph and stream events
            final_output = ""
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=types.Content(role="user", parts=[types.Part.from_text(text=user_input)])
            ):
                if hasattr(event, "branch") and event.branch == "direct_response":
                    final_output = str(event.output)
                elif hasattr(event, "branch") and event.branch == "synthesis":
                    # Synthesis agent output goes to final_advisory in state
                    if hasattr(event.state, "get"):
                        final_advisory = event.state.get("final_advisory")
                    elif isinstance(event.state, dict):
                        final_advisory = event.state.get("final_advisory")
                    else:
                        final_advisory = getattr(event.state, "final_advisory", "")
                        
                    if not final_advisory and hasattr(event.output, "final_advisory"):
                        final_advisory = getattr(event.output, "final_advisory", "")
                        
                    if final_advisory:
                        final_output = str(final_advisory)
            
            print(f"Kisan Agent:\n{final_output}\n")
            
            # Print state debug info
            session = await runner.session_service.get_session(session_id=session_id, app_name="app", user_id="cli_tester")
            if session:
                state_dict = session.state.to_dict() if hasattr(session.state, "to_dict") else dict(session.state)
                profile = state_dict.get('profile', {})
                active = state_dict.get('active_agents', [])
                print(f"[Debug Memory] Profile: location={profile.get('location_name')}, land={profile.get('land_size_acres')}")
                print(f"[Debug Memory] Active Agents: {active}\n")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\n[Error] {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
