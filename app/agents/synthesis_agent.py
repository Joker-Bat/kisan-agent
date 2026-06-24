from google.adk.agents import LlmAgent
from google.adk.models import Gemini
from google.genai import types

from app.core.constants import SYNTHESIS_INSTRUCTION

synthesizer = LlmAgent(
    name="synthesizer",
    model=Gemini(model="gemini-2.5-flash", retry_options=types.HttpRetryOptions(attempts=3)),
    instruction=SYNTHESIS_INSTRUCTION,
)

from google.adk.workflow import node
from google.adk.agents.context import Context

@node(rerun_on_resume=True)
async def synthesis_node(ctx: Context, node_input: dict):
    """Formats outputs, runs the synthesis LLM, and handles errors."""
    profile_dict = ctx.state.get("profile", {})
    import json
    profile_json = json.dumps(profile_dict, indent=2)
    prompt = f"Farmer Profile:\n{profile_json}\n\nAgent Results:\n"
    
    for agent_name, agent_output in node_input.items():
        if agent_name not in ["profile", "active_agents", "missing_info_questions"]:
            prompt += f"--- {agent_name.upper()} ---\n{agent_output}\n\n"
            
    try:
        return await ctx.run_node(synthesizer, node_input=prompt, use_as_output=True)
    except Exception as e:
        print(f"Synthesis LLM Error: {e}")
        return "The system gathered your data, but faced an error compiling the final advisory. Please try asking again."
