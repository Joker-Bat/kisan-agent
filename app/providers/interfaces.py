from typing import Protocol, Any, Dict, List
from app.core.schemas import SchemeModel

class WeatherProvider(Protocol):
    def fetch_forecast(self, lat: float, lon: float) -> Dict[str, Any]:
        """Fetch weather forecast for the given coordinates."""
        ...

class MarketProvider(Protocol):
    def fetch_prices(self, crop: str, state: str) -> List[Dict[str, Any]]:
        """Fetch market prices for the given crop and state."""
        ...

class SchemeProvider(Protocol):
    def get_schemes(self, region: str) -> List[SchemeModel]:
        """Get available schemes for the given region."""
        ...
