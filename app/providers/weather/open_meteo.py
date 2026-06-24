import httpx
from typing import Dict, Any
from app.core.constants import OPEN_METEO_URL
from app.providers.interfaces import WeatherProvider

class OpenMeteoProvider(WeatherProvider):
    def fetch_forecast(self, lat: float, lon: float) -> Dict[str, Any]:
        """Fetches a 14-day weather forecast from Open-Meteo for given coordinates."""
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": "precipitation_sum,temperature_2m_max,temperature_2m_min",
            "forecast_days": 14,
            "timezone": "auto"
        }
        try:
            response = httpx.get(OPEN_METEO_URL, params=params, timeout=10.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Weather API error: {e}")
            return {}
