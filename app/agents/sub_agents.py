import json
import os
from google.adk.agents import Agent
from google.adk.models import Gemini
from google.genai import types

from app.core.schemas import WeatherOutput, MarketOutput, CropOutput, SchemeOutput, FarmerProfile
from app.tools.geocoding import get_lat_lon
from app.tools.weather_api import fetch_weather_forecast
from app.tools.market_api import fetch_mandi_prices

# Define the shared model configuration
# We use gemini-2.5-flash as it is fast and supports structured output
model = Gemini(
    model="gemini-2.5-flash",
    retry_options=types.HttpRetryOptions(attempts=3)
)

def run_weather_agent(profile: FarmerProfile) -> WeatherOutput:
    """Executes the Weather agent logic."""
    lat, lon = profile.latitude, profile.longitude
    
    # Use geocoding if lat/lon is missing but location_name is present
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
        model=model,
        instruction="Summarize the following raw weather data into a short, farmer-friendly summary, and extract the daily forecast points into the structured format.",
        output_type=WeatherOutput
    )
    return agent(f"Raw data: {data}")

def run_market_agent(profile: FarmerProfile) -> MarketOutput:
    """Executes the Market agent logic."""
    if not profile.crop_intent or not profile.state:
        return MarketOutput(
            crop=profile.crop_intent or "Unknown",
            state=profile.state or "Unknown",
            prices=[]
        )
        
    data = fetch_mandi_prices(profile.crop_intent, profile.state)
    
    agent = Agent(
        name="market_summarizer",
        model=model,
        instruction="Extract the market prices from this raw JSON and summarize them into the structured format.",
        output_type=MarketOutput
    )
    return agent(f"Crop: {profile.crop_intent}\nState: {profile.state}\nData: {data}")

def run_crop_agent(profile: FarmerProfile, weather_info: WeatherOutput = None) -> CropOutput:
    """Executes the Crop agent logic."""
    agent = Agent(
        name="crop_recommender",
        model=model,
        instruction="You are an expert agronomist. Recommend the top 3 best crops based on the farmer's soil profile (N, P, K, pH) and location. Provide a detailed rationale.",
        output_type=CropOutput
    )
    prompt = f"Profile: {profile.model_dump_json()}"
    if weather_info:
        prompt += f"\nWeather context: {weather_info.summary}"
    return agent(prompt)

def run_scheme_agent(profile: FarmerProfile) -> SchemeOutput:
    """Executes the Scheme agent logic."""
    # Load the scheme database
    scheme_path = os.path.join(os.path.dirname(__file__), "..", "data", "schemes", "TN_INDIA.json")
    with open(scheme_path, "r", encoding="utf-8") as f:
        schemes_db = json.load(f)
        
    agent = Agent(
        name="scheme_evaluator",
        model=model,
        instruction="Evaluate the farmer's profile against the provided government schemes database. Determine exactly which schemes they are eligible for and provide application instructions.",
        output_type=SchemeOutput
    )
    prompt = f"Farmer Profile: {profile.model_dump_json()}\nSchemes DB: {json.dumps(schemes_db)}"
    return agent(prompt)
