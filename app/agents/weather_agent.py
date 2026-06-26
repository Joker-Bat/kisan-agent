import datetime
import logging

from google.adk.agents import LlmAgent
from google.adk.agents.context import Context
from google.adk.models import Gemini
from google.adk.workflow import node
from google.genai import types

from app.app_utils.log_config import bind_session_id
from app.core.constants import NODE_WEATHER
from app.core.schemas import GraphState, WeatherOutput
from app.providers.registry import active_weather_provider
from app.tools.geocoding import get_lat_lon

logger = logging.getLogger(__name__)

WEATHER_AGENT_INSTRUCTION = """
You are the expert Agricultural Meteorologist for the Kisan Agent system.
Your job is to analyze raw numerical weather data and translate it into a simple, actionable summary for farmers.

You MUST distinguish between forecast data (future weather) and historical data (past weather):
- If the context specifies the data is HISTORICAL, you MUST write your summary using the PAST tense (e.g. "temperatures peaked at", "it rained"). Do NOT use future/forecast language like "will be", "forecasted", "is expected".
- If the context specifies the data is a FORECAST, you MUST write your summary using the FUTURE tense (e.g. "temperatures will peak", "rain is expected").
Focus on critical parameters like temperature ranges, heavy rainfall, extreme heat, or historical trends.
Never hallucinate. If data is missing, clearly state that.
"""

weather_summarizer = LlmAgent(
    name="weather_summarizer",
    model=Gemini(
        model="gemini-3.1-flash-lite", retry_options=types.HttpRetryOptions(attempts=3)
    ),
    instruction=WEATHER_AGENT_INSTRUCTION,
    output_schema=WeatherOutput,
)


@node(rerun_on_resume=True)
async def weather_node(ctx: Context, node_input: GraphState):
    bind_session_id(ctx)
    if NODE_WEATHER not in node_input.active_agents:
        logger.info("Weather Agent: SKIPPED (not active)")
        return "SKIPPED"

    logger.info("Weather Agent: Starting processing")
    profile = node_input.profile
    lat, lon = profile.latitude, profile.longitude

    if lat is None or lon is None:
        if profile.location_name:
            logger.info(f"Weather Agent: Resolving geocoding for {profile.location_name}")
            coords = await get_lat_lon(profile.location_name)
            if coords:
                lat, lon = coords
                logger.info(f"Weather Agent: Resolved coords for {profile.location_name}: lat={lat}, lon={lon}")

    if lat is None or lon is None:
        logger.warning("Weather Agent: Could not determine coordinates for location")
        return WeatherOutput(
            summary="Could not determine location for weather forecast. Please provide exact coordinates or a valid city name.",
            forecast_days=[],
        )

    logger.info(f"Weather Agent: Fetching forecast for lat={lat}, lon={lon}")
    data = await active_weather_provider.fetch_forecast(
        lat,
        lon,
        start_date=profile.weather_start_date,
        end_date=profile.weather_end_date,
    )

    if not data:
        logger.error("Weather Agent: Weather service is unavailable or failed to fetch data")
        return WeatherOutput(
            summary="The weather service is temporarily unavailable. Please try again later.",
            forecast_days=[],
        )

    filtered_data = {
        "daily": data.get("daily", {}),
        "daily_units": data.get("daily_units", {}),
    }

    # Check if this query is for historical weather or a future forecast
    is_history = False
    if profile.weather_end_date:
        try:
            end_dt = datetime.date.fromisoformat(profile.weather_end_date)
            # If end date is in the past (before today), it's history
            if end_dt < datetime.date.today():
                is_history = True
        except Exception as e:
            logger.debug(f"Failed to parse weather_end_date: {e}")

    range_str = (
        f"from {profile.weather_start_date} to {profile.weather_end_date}"
        if (profile.weather_start_date and profile.weather_end_date)
        else ""
    )
    if is_history:
        context_instruction = f"Context: This is HISTORICAL weather observations {range_str}. Summarize the weather in the PAST tense (e.g. 'The temperature was...', 'It rained...'). Do NOT use future forecast language."
    else:
        context_instruction = f"Context: This is a future weather FORECAST {range_str}. Summarize the weather in the FUTURE tense (e.g. 'The temperature will be...', 'Rain is expected...')."

    logger.info(f"Weather Agent: Summarizing weather data. is_history={is_history}")
    try:
        # Run the LLM agent as a child node for proper ADK tracing
        return await ctx.run_node(
            weather_summarizer,
            node_input=f"{context_instruction}\nRaw data: {filtered_data}",
        )
    except Exception as e:
        logger.error(f"Weather LLM Error: {e}", exc_info=True)
        return WeatherOutput(
            summary="I'm having trouble analyzing the weather data right now due to a technical issue.",
            forecast_days=[],
        )
