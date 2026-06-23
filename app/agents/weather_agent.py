from google.adk.agents import Agent
from google.adk.models import Gemini
from google.genai import types

from app.core.schemas import WeatherOutput, FarmerProfile
from app.tools.geocoding import get_lat_lon
from app.tools.weather_api import fetch_weather_forecast

WEATHER_AGENT_INSTRUCTION = """
You are the expert Agricultural Meteorologist for the Kisan Agent system.
Your job is to analyze raw numerical weather data and translate it into a simple, actionable summary for farmers.
Focus on critical parameters like sudden temperature drops, heavy rainfall, or extreme heat.
Never hallucinate forecasts. If data is missing, clearly state that.
"""

def get_weather_model():
    """Configurable model for the weather agent."""
    return Gemini(model="gemini-2.5-flash", retry_options=types.HttpRetryOptions(attempts=3))

def run_weather_agent(profile: FarmerProfile) -> WeatherOutput:
    """Executes the Weather agent logic."""
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
    
    agent = Agent(
        name="weather_summarizer",
        model=get_weather_model(),
        instruction=WEATHER_AGENT_INSTRUCTION,
        output_type=WeatherOutput
    )
    return agent(f"Raw data: {data}")
