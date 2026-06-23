import json
import os
from google.adk.agents import LlmAgent
from google.adk.models import Gemini
from google.genai import types
from google.adk.workflow import node
from google.adk.agents.context import Context

from app.core.schemas import SchemeOutput, GraphState
from app.core.config import settings

SCHEME_AGENT_INSTRUCTION = """
You are the Government Scheme Advisor for the Kisan Agent system.
You will be given a farmer's profile and a database of available schemes.
Strictly cross-reference the farmer's details (land size, income, disaster status) against the eligibility criteria of EACH scheme.
Only recommend schemes the farmer is ACTUALLY eligible for.
Provide clear, step-by-step application instructions for the matching schemes. Do not hallucinate URLs or schemes outside the provided database.
"""

scheme_evaluator = LlmAgent(
    name="scheme_evaluator",
    model=Gemini(model="gemini-2.5-pro", retry_options=types.HttpRetryOptions(attempts=3)),
    instruction=SCHEME_AGENT_INSTRUCTION,
    output_schema=SchemeOutput
)

@node(rerun_on_resume=True)
async def scheme_node(ctx: Context, node_input: GraphState):
    profile = node_input.profile
    region_file = f"{settings.REGION}.json"
    scheme_path = os.path.join(os.path.dirname(__file__), "..", "data", "schemes", region_file)
    with open(scheme_path, "r", encoding="utf-8") as f:
        schemes_db = json.load(f)
        
    prompt = f"Farmer Profile: {profile.model_dump_json()}\nSchemes DB: {json.dumps(schemes_db)}"
    return await ctx.run_node(scheme_evaluator, node_input=prompt)
