from typing import Any, Protocol

from app.core.schemas import SchemeModel


class WeatherProvider(Protocol):
    async def fetch_forecast(
        self,
        lat: float,
        lon: float,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        """Fetch weather forecast/history for the given coordinates and date range."""
        ...


class MarketProvider(Protocol):
    async def fetch_prices(self, crop: str, state: str) -> list[dict[str, Any]]:
        """Fetch market prices for the given crop and state."""
        ...


class SchemeProvider(Protocol):
    def get_schemes(self, region: str) -> list[SchemeModel]:
        """Get available schemes for the given region."""
        ...


class CropProvider(Protocol):
    def match_crops(
        self,
        n: float | None = None,
        p: float | None = None,
        k: float | None = None,
        ph: float | None = None,
        rainfall: float | None = None,
        temperature: float | None = None,
    ) -> list[dict[str, Any]]:
        """Find the top matching crops from the Kaggle dataset."""
        ...
