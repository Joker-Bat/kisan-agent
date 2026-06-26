import httpx


def get_lat_lon(location_name: str) -> tuple[float, float] | None:
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
    params = {"q": location_name, "format": "json", "limit": 1}

    try:
        response = httpx.get(url, params=params, headers=headers, timeout=10.0)
        response.raise_for_status()
        data = response.json()
        if data and len(data) > 0:
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            return (lat, lon)
    except Exception as e:
        print(f"Geocoding error: {e}")
    return None
