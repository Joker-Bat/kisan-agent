import logging
from typing import Any

import httpx

from app.core.config import settings
from app.core.constants import DATA_GOV_IN_URL
from app.providers.cache import TtlCache
from app.providers.interfaces import MarketProvider

logger = logging.getLogger(__name__)


class GovDataMarketProvider(MarketProvider):
    def __init__(self) -> None:
        # Cache for 1 hour
        self._cache = TtlCache(ttl_seconds=3600)

    async def fetch_prices(
        self,
        crop: str,
        state: str,
        district: str | None = None,
        market: str | None = None,
    ) -> list[dict[str, Any]]:
        """Fetches wholesale mandi prices from data.gov.in AGMARKNET API, with caching."""
        cache_key = (crop, state, district, market)
        cached_data = self._cache.get(cache_key)
        if cached_data is not None:
            logger.info(f"Market Agent: Cache HIT for crop='{crop}', state='{state}', district='{district}', market='{market}'")
            return cached_data

        if not settings.DATA_GOV_IN_API_KEY:
            logger.warning("fetch_prices called but DATA_GOV_IN_API_KEY is not set.")
            return []

        params = {
            "api-key": settings.DATA_GOV_IN_API_KEY,
            "format": "json",
            "filters[state]": state,
            "limit": 30,
        }
        if crop:
            params["filters[commodity]"] = crop
        if district:
            params["filters[district]"] = district
        if market:
            params["filters[market]"] = market

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        logger.info(
            f"Fetching market prices from {DATA_GOV_IN_URL} for crop={crop}, state={state}, district={district}, market={market}"
        )
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    DATA_GOV_IN_URL, params=params, headers=headers
                )
                response.raise_for_status()
                data = response.json()
                records = data.get("records", [])
                self._cache.set(cache_key, records)
                return records
        except Exception as e:
            logger.error(f"Market API error: {e}", exc_info=True)
            return []
