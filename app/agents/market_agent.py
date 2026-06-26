import logging
import re
from typing import Any

from google.adk.agents import LlmAgent
from google.adk.agents.context import Context
from google.adk.models import Gemini
from google.adk.workflow import node
from google.genai import types

from app.app_utils.log_config import bind_session_id
from app.core.config import settings
from app.core.constants import NODE_MARKET
from app.core.schemas import GraphState, MarketOutput
from app.providers.registry import active_market_provider

logger = logging.getLogger(__name__)

MARKET_AGENT_INSTRUCTION = """
You are the Market Economics Analyst for the Kisan Agent system.
Your job is to process raw JSON mandi prices and identify the best selling opportunities for the farmer.
Highlight the market with the highest modal price and explicitly tell the farmer where to sell for maximum profit.
Never make up prices. If the dataset is empty, advise the farmer that no recent price data is available for that crop in their state.

### Important Pricing Unit Rules:
- The raw prices from data.gov.in are in Rupees per Quintal (100 kg).
- You MUST explicitly state that the prices are per quintal (100 kg).
- For maximum clarity, always calculate and present the price per kilogram as well (by dividing the quintal price by 100, e.g., "₹2200 per quintal, which is ₹22 per kg").
"""

market_summarizer = LlmAgent(
    name="market_summarizer",
    model=Gemini(
        model="gemini-3.1-flash-lite", retry_options=types.HttpRetryOptions(attempts=3)
    ),
    instruction=MARKET_AGENT_INSTRUCTION,
    output_schema=MarketOutput,
)


def parse_crop_intent(crop_intent: str | list[str] | None) -> list[str]:
    """Helper to parse and split crop intents from string or list format."""
    if not crop_intent:
        return []
    raw_crops = crop_intent if isinstance(crop_intent, list) else [crop_intent]
    crop_names = []
    for crop in raw_crops:
        if isinstance(crop, str):
            splits = re.split(r"\band\b|&|,", crop)
            for s in splits:
                s_clean = s.strip()
                if s_clean:
                    crop_names.append(s_clean)
    return crop_names


@node(rerun_on_resume=True)
async def market_node(ctx: Context, node_input: GraphState):
    bind_session_id(ctx)
    if NODE_MARKET not in node_input.active_agents:
        logger.info("Market Agent: SKIPPED (not active)")
        return "SKIPPED"

    logger.info("Market Agent: Starting processing")
    profile = node_input.profile

    crop_names = parse_crop_intent(profile.crop_intent)
    crop_str = ", ".join(crop_names) if crop_names else "Unknown"

    if not crop_names or not profile.state:
        logger.warning(f"Market Agent: Missing criteria. crop_names={crop_names}, state={profile.state}")
        return MarketOutput(crop=crop_str, state=profile.state or "Unknown", prices=[])

    if not settings.DATA_GOV_IN_API_KEY:
        logger.warning("Market Agent: API key for data.gov.in missing")
        return MarketOutput(
            crop=crop_str,
            state=profile.state,
            prices=[],
            summary="The wholesale mandi price service is not configured. To enable live mandi prices, please set 'DATA_GOV_IN_API_KEY' in your .env file with your API key from data.gov.in.",
        )

    all_prices = []
    for crop_name in crop_names:
        logger.info(
            f"Market Agent: Fetching local prices for {crop_name} in {profile.state}, district={profile.district}, market={profile.market}"
        )
        data = await active_market_provider.fetch_prices(
            crop=crop_name,
            state=profile.state,
            district=profile.district,
            market=profile.market,
        )
        if data:
            all_prices.extend(data)
        elif profile.district or profile.market:
            # Fall back to state-wide prices if local prices are missing
            logger.info(
                f"Market Agent: No local prices found for {crop_name} in district '{profile.district}'. Falling back to state-wide query."
            )
            state_data = await active_market_provider.fetch_prices(crop_name, profile.state)
            if state_data:
                all_prices.extend(state_data)

    if not all_prices:
        logger.info(f"Market Agent: No prices found for {crop_str} in {profile.state}. Fetching state suggestions.")
        # Fetch up to 30 recent records for the state to suggest active crops
        state_records = await active_market_provider.fetch_prices(
            crop="", state=profile.state
        )
        suggested_crops = []
        if state_records:
            seen_crops = set()
            for r in state_records:
                commodity_name = r.get("commodity")
                if commodity_name:
                    # Clean up names like "Black Gram(Urd Beans)(Whole)" for readability
                    clean_name = commodity_name.split("(")[0].strip()
                    if clean_name and clean_name not in seen_crops:
                        seen_crops.add(clean_name)
                        suggested_crops.append(clean_name)
                        if len(suggested_crops) >= 5:
                            break

        if suggested_crops:
            suggestions_str = ", ".join(suggested_crops)
            summary_msg = f"No recent mandi price data found for '{crop_str}' in {profile.state}. The crops currently active in {profile.state} are: {suggestions_str}. Would you like to check prices for any of these?"
        else:
            summary_msg = f"No recent mandi price data found for '{crop_str}' in {profile.state}. Please try again later."

        return MarketOutput(
            crop=crop_str, state=profile.state, prices=[], summary=summary_msg
        )

    logger.info(f"Market Agent: Summarizing {len(all_prices)} price records")
    try:
        return await ctx.run_node(
            market_summarizer,
            node_input=f"Crop: {crop_str}\nState: {profile.state}\nData: {all_prices}",
        )
    except Exception as e:
        logger.error(f"Market LLM Error: {e}", exc_info=True)
        return MarketOutput(
            crop=crop_str,
            state=profile.state,
            prices=[],
            summary="I'm having trouble analyzing the market data right now due to a technical issue.",
        )
