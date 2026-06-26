from typing import Any

import httpx

from app.core.config import settings
from app.core.constants import DATA_GOV_IN_URL
from app.providers.interfaces import MarketProvider


class GovDataMarketProvider(MarketProvider):
    def fetch_prices(self, crop: str, state: str) -> list[dict[str, Any]]:
        """Fetches wholesale mandi prices from data.gov.in AGMARKNET API."""
        if not settings.DATA_GOV_IN_API_KEY:
            return None

        params = {
            "api-key": settings.DATA_GOV_IN_API_KEY,
            "format": "json",
            "filters[state]": state,
            "limit": 30,
        }
        if crop:
            params["filters[commodity]"] = crop

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        try:
            response = httpx.get(
                DATA_GOV_IN_URL, params=params, headers=headers, timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
            return data.get("records", [])
        except Exception as e:
            print(f"Market API error: {e}")
            return []
