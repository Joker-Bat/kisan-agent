import httpx
from typing import Optional, Tuple

def get_lat_lon(location_name: str) -> Optional[Tuple[float, float]]:
    """Resolves a location name to Latitude and Longitude using the free Nominatim API.
    
    Args:
        location_name: The city, district, or village name.
        
    Returns:
        A tuple of (latitude, longitude) floats, or None if not found.
    """
    # Nominatim requires a User-Agent
    headers = {"User-Agent": "KisanAgent/1.0 (contact@example.com)"}
    url = f"https://nominatim.openstreetmap.org/search?q={location_name}&format=json&limit=1"
    
    try:
        response = httpx.get(url, headers=headers, timeout=10.0)
        response.raise_for_status()
        data = response.json()
        if data and len(data) > 0:
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            return (lat, lon)
    except Exception as e:
        print(f"Geocoding error: {e}")
    return None
