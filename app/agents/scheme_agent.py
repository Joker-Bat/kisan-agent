import json
import logging

from google.adk.agents import LlmAgent
from google.adk.agents.context import Context
from google.adk.models import Gemini
from google.adk.workflow import node
from google.genai import types

from app.app_utils.log_config import bind_session_id
from app.core.config import settings
from app.core.constants import NODE_SCHEME
from app.core.schemas import GraphState, SchemeOutput
from app.providers.registry import active_scheme_provider

logger = logging.getLogger(__name__)

SCHEME_AGENT_INSTRUCTION = """
You are the Government Scheme Advisor for the Kisan Agent system.
You will be given a farmer's profile and a database of available schemes.
Strictly cross-reference the farmer's details (land size, income, disaster status) against the eligibility criteria of EACH scheme.
Only recommend schemes the farmer is ACTUALLY eligible for.
Provide clear, step-by-step application instructions for the matching schemes. Do not hallucinate URLs or schemes outside the provided database.
"""

scheme_evaluator = LlmAgent(
    name="scheme_evaluator",
    model=Gemini(
        model="gemini-2.5-pro", retry_options=types.HttpRetryOptions(attempts=3)
    ),
    instruction=SCHEME_AGENT_INSTRUCTION,
    output_schema=SchemeOutput,
)


@node(rerun_on_resume=True)
async def scheme_node(ctx: Context, node_input: GraphState):
    bind_session_id(ctx)
    if NODE_SCHEME not in node_input.active_agents:
        logger.info("Scheme Agent: SKIPPED (not active)")
        return "SKIPPED"

    logger.info(f"Scheme Agent: Starting processing for region {settings.REGION}")
    profile = node_input.profile
    schemes_db = active_scheme_provider.get_schemes(settings.REGION)

    # Convert Pydantic models back to dict for the prompt
    schemes_json = [scheme.model_dump(exclude_none=True) for scheme in schemes_db]

    prompt = f"Farmer Profile: {profile.model_dump_json(exclude_none=True)}\nSchemes DB: {json.dumps(schemes_json, indent=2)}"
    
    logger.info("Scheme Agent: Querying scheme LLM evaluator")
    try:
        return await ctx.run_node(scheme_evaluator, node_input=prompt)
    except Exception as e:
        logger.error(f"Scheme LLM Error: {e}", exc_info=True)
        return SchemeOutput(
            applicable_schemes=[],
            instructions="I'm having trouble analyzing your eligibility right now due to a technical issue. Please try again later.",
        )
