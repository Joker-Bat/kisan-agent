from google.adk.agents import LlmAgent
from google.adk.models import Gemini
from google.genai import types

from app.core.constants import SYNTHESIS_INSTRUCTION

synthesizer = LlmAgent(
    name="synthesizer",
    model=Gemini(model="gemini-2.5-flash", retry_options=types.HttpRetryOptions(attempts=3)),
    instruction=SYNTHESIS_INSTRUCTION,
)

def prepare_synthesis(node_input: dict) -> str:
    """Formats the parallel agent outputs into a synthesis prompt."""
    return f"Synthesize the following agricultural data into a bilingual advisory:\n{node_input}"
