from google.adk.agents import Agent
from google.adk.models import Gemini
from google.genai import types

from app.core.schemas import MarketOutput, FarmerProfile
from app.tools.market_api import fetch_mandi_prices

MARKET_AGENT_INSTRUCTION = """
You are the Market Economics Analyst for the Kisan Agent system.
Your job is to process raw JSON mandi prices and identify the best selling opportunities for the farmer.
Highlight the market with the highest modal price and explicitly tell the farmer where to sell for maximum profit.
Never make up prices. If the dataset is empty, advise the farmer that no recent price data is available for that crop in their state.
"""

def get_market_model():
    """Configurable model for the market agent."""
    return Gemini(model="gemini-2.5-flash", retry_options=types.HttpRetryOptions(attempts=3))

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
        model=get_market_model(),
        instruction=MARKET_AGENT_INSTRUCTION,
        output_type=MarketOutput
    )
    return agent(f"Crop: {profile.crop_intent}\nState: {profile.state}\nData: {data}")
