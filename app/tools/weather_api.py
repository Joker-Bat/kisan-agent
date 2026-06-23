import httpx
from app.core.constants import OPEN_METEO_URL

def fetch_weather_forecast(lat: float, lon: float) -> dict:
    """Fetches a 14-day weather forecast from Open-Meteo for given coordinates.
    
    Args:
        lat: Latitude
        lon: Longitude
        
    Returns:
        A dictionary containing the forecast data.
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "precipitation_sum,temperature_2m_max,temperature_2m_min,soil_temperature_0cm",
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
