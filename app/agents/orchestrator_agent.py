from google.adk.agents import LlmAgent
from google.adk.models import Gemini
from google.genai import types

from app.core.schemas import GraphState
from app.core.constants import ORCHESTRATOR_INSTRUCTION

orchestrator = LlmAgent(
    name="orchestrator",
    model=Gemini(model="gemini-2.5-flash", retry_options=types.HttpRetryOptions(attempts=3)),
    instruction=ORCHESTRATOR_INSTRUCTION,
    output_schema=GraphState
)
