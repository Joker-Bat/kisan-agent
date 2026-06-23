from google.adk.agents import Agent
from google.adk.models import Gemini
from google.genai import types

from app.core.schemas import CropOutput, WeatherOutput, FarmerProfile

CROP_AGENT_INSTRUCTION = """
You are the Chief Agronomist for the Kisan Agent system.
Your objective is to analyze the farmer's soil profile (N, P, K, pH) and recommend the top 3 crops that will thrive in those specific conditions.
Consider any provided weather context (like heavy rain or drought).
Provide a highly detailed agricultural rationale for WHY these crops were chosen, mentioning the specific nutrient and pH alignments.
Do not recommend water-intensive crops if the soil is dry and rainfall is low.
"""

def get_crop_model():
    """Configurable model for the crop agent."""
    return Gemini(model="gemini-2.5-pro", retry_options=types.HttpRetryOptions(attempts=3))

def run_crop_agent(profile: FarmerProfile, weather_info: WeatherOutput = None) -> CropOutput:
    """Executes the Crop agent logic."""
    agent = Agent(
        name="crop_recommender",
        model=get_crop_model(),
        instruction=CROP_AGENT_INSTRUCTION,
        output_type=CropOutput
    )
    prompt = f"Profile: {profile.model_dump_json()}"
    if weather_info:
        prompt += f"\nWeather context: {weather_info.summary}"
    return agent(prompt)
