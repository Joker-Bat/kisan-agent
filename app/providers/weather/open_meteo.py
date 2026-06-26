import datetime
import logging
from typing import Any

import httpx

from app.core.constants import OPEN_METEO_URL
from app.providers.interfaces import WeatherProvider

logger = logging.getLogger(__name__)


class OpenMeteoProvider(WeatherProvider):
    async def fetch_forecast(
        self,
        lat: float,
        lon: float,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        """Fetches weather forecast or historical data from Open-Meteo for given coordinates and date range."""

        # Decide which URL to use and parameters
        if start_date and end_date:
            try:
                s_date = datetime.date.fromisoformat(start_date)
                today = datetime.date.today()
                # If start date is older than 90 days ago, use historical archive API
                if (today - s_date).days > 90:
                    url = "https://archive-api.open-meteo.com/v1/archive"
                else:
                    url = OPEN_METEO_URL
            except Exception as e:
                logger.debug(f"Failed to parse dates, defaulting to forecast URL: {e}")
                url = OPEN_METEO_URL

            params = {
                "latitude": lat,
                "longitude": lon,
                "daily": "precipitation_sum,temperature_2m_max,temperature_2m_min",
                "timezone": "auto",
                "start_date": start_date,
                "end_date": end_date,
            }
        else:
            url = OPEN_METEO_URL
            params = {
                "latitude": lat,
                "longitude": lon,
                "daily": "precipitation_sum,temperature_2m_max,temperature_2m_min",
                "forecast_days": 14,
                "timezone": "auto",
            }

        logger.info(f"Fetching weather from {url} for lat={lat}, lon={lon}")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Weather API error: {e}", exc_info=True)
            return {}
