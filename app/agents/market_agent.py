from google.adk.agents import LlmAgent
from google.adk.models import Gemini
from google.genai import types
from google.adk.workflow import node
from google.adk.agents.context import Context

from app.core.schemas import MarketOutput, GraphState
from app.tools.market_api import fetch_mandi_prices

MARKET_AGENT_INSTRUCTION = """
You are the Market Economics Analyst for the Kisan Agent system.
Your job is to process raw JSON mandi prices and identify the best selling opportunities for the farmer.
Highlight the market with the highest modal price and explicitly tell the farmer where to sell for maximum profit.
Never make up prices. If the dataset is empty, advise the farmer that no recent price data is available for that crop in their state.
"""

market_summarizer = LlmAgent(
    name="market_summarizer",
    model=Gemini(model="gemini-2.5-flash", retry_options=types.HttpRetryOptions(attempts=3)),
    instruction=MARKET_AGENT_INSTRUCTION,
    output_schema=MarketOutput
)

@node(rerun_on_resume=True)
async def market_node(ctx: Context, node_input: GraphState):
    profile = node_input.profile
    if not profile.crop_intent or not profile.state:
        return MarketOutput(
            crop=profile.crop_intent or "Unknown",
            state=profile.state or "Unknown",
            prices=[]
        )
        
    data = fetch_mandi_prices(profile.crop_intent, profile.state)
    
    return await ctx.run_node(market_summarizer, node_input=f"Crop: {profile.crop_intent}\nState: {profile.state}\nData: {data}")
