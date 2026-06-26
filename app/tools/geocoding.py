import logging
import httpx

logger = logging.getLogger(__name__)


async def get_lat_lon(location_name: str) -> tuple[float, float] | None:
    """Resolves a location name to Latitude and Longitude using the free Nominatim API.

    Args:
        location_name: The city, district, or village name.

    Returns:
        A tuple of (latitude, longitude) floats, or None if not found.
    """
    # Nominatim strictly enforces realistic User-Agents. We must use a unique one.
    headers = {
        "User-Agent": "KisanAgentBot/1.0 (https://github.com/google/kisan-agent-demo; support@kisanagent.local)"
    }
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": location_name, "format": "json", "limit": 1, "countrycodes": "in"}

    logger.info(f"Geocoding: Resolving '{location_name}' via Nominatim")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            if data and len(data) > 0:
                lat = float(data[0]["lat"])
                lon = float(data[0]["lon"])
                logger.info(f"Geocoding: Resolved '{location_name}' to lat={lat}, lon={lon}")
                return (lat, lon)
            logger.warning(f"Geocoding: No results found for '{location_name}'")
    except Exception as e:
        logger.error(f"Geocoding error: {e}", exc_info=True)
    return None
