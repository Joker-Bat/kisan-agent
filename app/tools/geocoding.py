import logging
from typing import Any
import httpx

from app.providers.cache import TtlCache

logger = logging.getLogger(__name__)

# Global cache for geocoding results, persisting 24 hours
_geocoding_cache = TtlCache(ttl_seconds=86400)


async def geocode_location(location_name: str) -> dict[str, Any] | None:
    """Resolves a location name to coordinates, state, and district using the Nominatim API, with caching.

    Args:
        location_name: The city, district, or village name.

    Returns:
        A dictionary containing latitude, longitude, state, district, and city, or None if not found.
    """
    clean_key = location_name.strip().lower()
    cached_data = _geocoding_cache.get(clean_key)
    if cached_data is not None:
        logger.info(f"Geocoding: Cache HIT for '{location_name}'")
        return cached_data

    # Nominatim strictly enforces realistic User-Agents. We must use a unique one.
    headers = {
        "User-Agent": "KisanAgentBot/1.0 (https://github.com/google/kisan-agent-demo; support@kisanagent.local)"
    }
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": location_name, "format": "json", "limit": 1, "countrycodes": "in", "addressdetails": 1}

    logger.info(f"Geocoding: Resolving '{location_name}' via Nominatim with addressdetails")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            if data and len(data) > 0:
                lat = float(data[0]["lat"])
                lon = float(data[0]["lon"])
                address = data[0].get("address", {})
                
                # In India, state_district or county usually maps to the mandi district name
                resolved_state = address.get("state")
                resolved_district = address.get("state_district") or address.get("county") or address.get("district")
                resolved_city = address.get("city") or address.get("town") or address.get("village")
                
                result = {
                    "latitude": lat,
                    "longitude": lon,
                    "state": resolved_state,
                    "district": resolved_district,
                    "city": resolved_city
                }
                
                logger.info(f"Geocoding: Resolved '{location_name}' to {result}")
                _geocoding_cache.set(clean_key, result)
                return result
            logger.warning(f"Geocoding: No results found for '{location_name}'")
    except Exception as e:
        logger.error(f"Geocoding error: {e}", exc_info=True)
    return None


async def get_lat_lon(location_name: str) -> tuple[float, float] | None:
    """Backward-compatible helper to resolve location name to latitude and longitude."""
    res = await geocode_location(location_name)
    if res:
        return (res["latitude"], res["longitude"])
    return None
