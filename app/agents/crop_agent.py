from google.adk.agents import LlmAgent
from google.adk.agents.context import Context
from google.adk.models import Gemini
from google.adk.workflow import node
from google.genai import types

from app.core.schemas import CropOutput, GraphState

CROP_AGENT_INSTRUCTION = """
You are the Chief Agronomist for the Kisan Agent system.
Your objective is to analyze the farmer's soil profile (N, P, K, pH) and recommend the top 3 crops that will thrive in those specific conditions.
Consider any provided weather context (like heavy rain or drought).
Provide a highly detailed agricultural rationale for WHY these crops were chosen, mentioning the specific nutrient and pH alignments.
Do not recommend water-intensive crops if the soil is dry and rainfall is low.
"""

crop_recommender = LlmAgent(
    name="crop_recommender",
    model=Gemini(
        model="gemini-2.5-pro", retry_options=types.HttpRetryOptions(attempts=3)
    ),
    instruction=CROP_AGENT_INSTRUCTION,
    output_schema=CropOutput,
)

from app.core.constants import NODE_CROP


@node(rerun_on_resume=True)
async def crop_node(ctx: Context, node_input: GraphState):
    if NODE_CROP not in node_input.active_agents:
        return "SKIPPED"

    profile = node_input.profile
    weather_info = node_input.weather_info

    prompt = f"Profile: {profile.model_dump_json(exclude_none=True)}"
    if weather_info:
        prompt += f"\nWeather context: {weather_info.summary}"

    try:
        return await ctx.run_node(crop_recommender, node_input=prompt)
    except Exception as e:
        print(f"Crop LLM Error: {e}")
        return CropOutput(
            recommended_crops=["N/A"],
            rationale="I'm having trouble analyzing your soil data right now due to a technical issue.",
        )
