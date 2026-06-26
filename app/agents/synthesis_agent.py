import json
import logging

from google.adk.agents import LlmAgent
from google.adk.agents.context import Context
from google.adk.models import Gemini
from google.adk.workflow import node
from google.genai import types

from app.app_utils.log_config import bind_session_id
from app.core.constants import SYNTHESIS_INSTRUCTION

logger = logging.getLogger(__name__)

synthesizer = LlmAgent(
    name="synthesizer",
    model=Gemini(
        model="gemini-3.5-flash", retry_options=types.HttpRetryOptions(attempts=3)
    ),
    instruction=SYNTHESIS_INSTRUCTION,
)


@node(rerun_on_resume=True)
async def synthesis_node(ctx: Context, node_input: dict):
    """Formats outputs, runs the synthesis LLM, and handles errors."""
    bind_session_id(ctx)
    logger.info("Synthesis Agent: Starting processing")

    profile_dict = ctx.state.get("profile", {})
    profile_json = json.dumps(profile_dict, indent=2)
    prompt = f"Farmer Profile:\n{profile_json}\n\nAgent Results:\n"

    for agent_name, agent_output in node_input.items():
        if agent_output == "SKIPPED":
            continue
        if agent_name not in ["profile", "active_agents", "missing_info_questions"]:
            prompt += f"--- {agent_name.upper()} ---\n{agent_output}\n\n"

    logger.info("Synthesis Agent: Invoking synthesis LLM")
    try:
        return await ctx.run_node(synthesizer, node_input=prompt, use_as_output=True)
    except Exception as e:
        logger.error(f"Synthesis LLM Error: {e}", exc_info=True)
        return "The system gathered your data, but faced an error compiling the final advisory. Please try asking again."
