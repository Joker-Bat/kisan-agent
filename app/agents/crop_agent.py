import json

from google.adk.agents import LlmAgent
from google.adk.agents.context import Context
from google.adk.models import Gemini
from google.adk.workflow import node
from google.genai import types

from app.core.schemas import CropOutput, GraphState

CROP_AGENT_INSTRUCTION = """
You are the Chief Agronomist for the Kisan Agent system.
Your objective is to recommend the top 3 crops that will thrive in the farmer's soil.
You MUST choose your crop recommendations strictly from the provided Grounded Database Matches.
Do NOT recommend any crops that are not present in the Grounded Database Matches.
Explain to the farmer why these crops were chosen, referencing their compatibility scores and how the N, P, K, and pH values align with the crop requirements.
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

    avg_temp = None
    if weather_info and weather_info.forecast_days:
        try:
            temps = []
            for day in weather_info.forecast_days:
                t_max = day.get("temperature_2m_max")
                t_min = day.get("temperature_2m_min")
                if t_max is not None and t_min is not None:
                    temps.append((t_max + t_min) / 2.0)
            if temps:
                avg_temp = sum(temps) / len(temps)
        except Exception:
            pass

    from app.providers.registry import active_crop_provider

    # Match crops using the local CSV provider based on soil parameters
    matches = active_crop_provider.match_crops(
        n=profile.n_val,
        p=profile.p_val,
        k=profile.k_val,
        ph=profile.ph_val,
        temperature=avg_temp,
    )

    prompt = f"Farmer Profile: {profile.model_dump_json(exclude_none=True)}\n"
    if matches:
        prompt += f"Grounded Database Matches (Calculated from Kaggle Crop Recommendation dataset based on soil NPK/pH):\n{json.dumps(matches, indent=2)}\n\n"
    if weather_info:
        prompt += f"Weather Context:\n{weather_info.summary}\n\n"

    prompt += "Identify the best crop recommendations from the Grounded Database Matches. Provide an agronomical rationale explaining why the recommended crops are the best match for the farmer's soil nutrients and pH values, referencing the compatibility scores."

    try:
        return await ctx.run_node(crop_recommender, node_input=prompt)
    except Exception as e:
        print(f"Crop LLM Error: {e}")
        return CropOutput(
            recommended_crops=["N/A"],
            rationale="I'm having trouble analyzing your soil data right now due to a technical issue.",
        )
