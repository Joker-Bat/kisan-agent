import json
import os
from google.adk.agents import Agent
from google.adk.models import Gemini
from google.genai import types

from app.core.schemas import SchemeOutput, FarmerProfile
from app.core.config import settings

SCHEME_AGENT_INSTRUCTION = """
You are the Government Scheme Advisor for the Kisan Agent system.
You will be given a farmer's profile and a database of available schemes.
Strictly cross-reference the farmer's details (land size, income, disaster status) against the eligibility criteria of EACH scheme.
Only recommend schemes the farmer is ACTUALLY eligible for.
Provide clear, step-by-step application instructions for the matching schemes. Do not hallucinate URLs or schemes outside the provided database.
"""

def get_scheme_model():
    """Configurable model for the scheme agent."""
    return Gemini(model="gemini-2.5-pro", retry_options=types.HttpRetryOptions(attempts=3))

def run_scheme_agent(profile: FarmerProfile) -> SchemeOutput:
    """Executes the Scheme agent logic."""
    region_file = f"{settings.REGION}.json"
    scheme_path = os.path.join(os.path.dirname(__file__), "..", "data", "schemes", region_file)
    with open(scheme_path, "r", encoding="utf-8") as f:
        schemes_db = json.load(f)
        
    agent = Agent(
        name="scheme_evaluator",
        model=get_scheme_model(),
        instruction=SCHEME_AGENT_INSTRUCTION,
        output_type=SchemeOutput
    )
    prompt = f"Farmer Profile: {profile.model_dump_json()}\nSchemes DB: {json.dumps(schemes_db)}"
    return agent(prompt)
