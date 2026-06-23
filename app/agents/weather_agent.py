from google.adk.agents import LlmAgent
from google.adk.models import Gemini
from google.genai import types
from google.adk.workflow import node
from google.adk.agents.context import Context

from app.core.schemas import WeatherOutput, GraphState
from app.tools.geocoding import get_lat_lon
from app.tools.weather_api import fetch_weather_forecast

WEATHER_AGENT_INSTRUCTION = """
You are the expert Agricultural Meteorologist for the Kisan Agent system.
Your job is to analyze raw numerical weather data and translate it into a simple, actionable summary for farmers.
Focus on critical parameters like sudden temperature drops, heavy rainfall, or extreme heat.
Never hallucinate forecasts. If data is missing, clearly state that.
"""

weather_summarizer = LlmAgent(
    name="weather_summarizer",
    model=Gemini(model="gemini-2.5-flash", retry_options=types.HttpRetryOptions(attempts=3)),
    instruction=WEATHER_AGENT_INSTRUCTION,
    output_schema=WeatherOutput
)

@node(rerun_on_resume=True)
async def weather_node(ctx: Context, node_input: GraphState):
    profile = node_input.profile
    lat, lon = profile.latitude, profile.longitude
    
    if lat is None or lon is None:
        if profile.location_name:
            coords = get_lat_lon(profile.location_name)
            if coords:
                lat, lon = coords
    
    if lat is None or lon is None:
        return WeatherOutput(
            summary="Could not determine location for weather forecast. Please provide exact coordinates or a valid city name.",
            forecast_days=[]
        )
        
    data = fetch_weather_forecast(lat, lon)
    
    # Run the LLM agent as a child node for proper ADK tracing
    return await ctx.run_node(weather_summarizer, node_input=f"Raw data: {data}")
