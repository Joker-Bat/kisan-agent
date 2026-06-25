from google.adk.workflow import node
from google.adk.agents.context import Context
from google.adk.agents import LlmAgent
from google.adk.models import Gemini
from google.genai import types

from app.core.schemas import GraphState
from app.core.constants import ORCHESTRATOR_INSTRUCTION
from typing import Any

orchestrator_llm = LlmAgent(
    name="orchestrator",
    model=Gemini(model="gemini-3.5-flash", retry_options=types.HttpRetryOptions(attempts=3)),
    instruction=ORCHESTRATOR_INSTRUCTION,
    output_schema=GraphState
)

from google.adk.events.event import Event

@node(rerun_on_resume=True)
async def orchestrator_node(ctx: Context, node_input: Any):
    return await orchestrator_logic(ctx, node_input)

async def orchestrator_logic(ctx: Context, node_input: Any):
    # Convert ADK State object to a standard python dictionary
    current_state_dict = ctx.state.to_dict() if hasattr(ctx.state, "to_dict") else dict(ctx.state)
    current_profile = current_state_dict.get("profile", {})
    
    # Check if the node_input is the raw Content object from START or string
    if hasattr(node_input, "parts"):
        user_msg = node_input.parts[0].text if node_input.parts else ""
    else:
        user_msg = str(node_input)
    
    prompt = f"Accumulated Profile: {current_profile}\nNew User Query: {user_msg}\nUpdate the profile based on the latest input."
    
    # Run the LLM to extract new info from the current turn
    try:
        new_state_dict = await ctx.run_node(orchestrator_llm, node_input=prompt)
    except Exception as e:
        print(f"Orchestrator LLM Error: {e}")
        from app.core.constants import ROUTE_DIRECT_RESPONSE
        # Event is already imported at the top of the file
        return Event(
            output="I am currently experiencing technical difficulties and cannot process your request. Please try again later.",
            route=ROUTE_DIRECT_RESPONSE
        )
    new_state = GraphState(**new_state_dict)
    
    # Python deterministic merge for nested profile
    new_profile_data = new_state.profile.model_dump(exclude_none=True)
    merged_profile = {**current_profile, **new_profile_data}
    
    # Inherit active agents if none provided in current turn
    existing_active_agents = current_state_dict.get("active_agents", [])
    merged_active_agents = new_state.active_agents if new_state.active_agents else existing_active_agents
    
    # We construct the exact state delta to patch the global ADK memory
    state_delta = {
        "user_query": user_msg,
        "profile": merged_profile,
        "active_agents": merged_active_agents,
        "missing_info_questions": new_state.missing_info_questions,
    }
    
    # Directly update the ADK context state using its built-in method
    if hasattr(ctx.state, "update"):
        ctx.state.update(state_delta)
    else:
        for k, v in state_delta.items():
            ctx.state[k] = v
            
    # The output is the fully merged state passed downstream to the router.
    merged_full_state_dict = {
        "user_query": user_msg,
        "profile": merged_profile,
        "active_agents": merged_active_agents,
        "missing_info_questions": new_state.missing_info_questions,
        "weather_info": current_state_dict.get("weather_info"),
        "market_info": current_state_dict.get("market_info"),
        "crop_info": current_state_dict.get("crop_info"),
        "scheme_info": current_state_dict.get("scheme_info"),
        "final_advisory": current_state_dict.get("final_advisory"),
    }
    
    return Event(
        output=GraphState(**merged_full_state_dict)
    )
