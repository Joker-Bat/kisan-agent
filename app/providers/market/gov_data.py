import httpx
from typing import Dict, Any, List
from app.core.config import settings
from app.core.constants import DATA_GOV_IN_URL
from app.providers.interfaces import MarketProvider

class GovDataMarketProvider(MarketProvider):
    def fetch_prices(self, crop: str, state: str) -> List[Dict[str, Any]]:
        """Fetches wholesale mandi prices from data.gov.in AGMARKNET API."""
        if not settings.DATA_GOV_IN_API_KEY:
            # Fallback Mock Data
            return [
                {"state": state, "district": "Salem", "market": "Attur", "commodity": crop, "min_price": "1200", "max_price": "1500", "modal_price": "1350", "arrival_date": "Today"},
                {"state": state, "district": "Coimbatore", "market": "Mettupalayam", "commodity": crop, "min_price": "1300", "max_price": "1600", "modal_price": "1450", "arrival_date": "Today"}
            ]

        params = {
            "api-key": settings.DATA_GOV_IN_API_KEY,
            "format": "json",
            "filters[State]": state,
            "filters[Commodity]": crop,
            "limit": 10
        }
        
        try:
            response = httpx.get(DATA_GOV_IN_URL, params=params, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            return data.get("records", [])
        except Exception as e:
            print(f"Market API error: {e}")
            return []
