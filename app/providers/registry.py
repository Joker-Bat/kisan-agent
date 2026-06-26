from app.providers.interfaces import MarketProvider, SchemeProvider, WeatherProvider
from app.providers.market.gov_data import GovDataMarketProvider
from app.providers.schemes.local_json import LocalJsonSchemeProvider
from app.providers.weather.open_meteo import OpenMeteoProvider

# Instantiate active providers
active_weather_provider: WeatherProvider = OpenMeteoProvider()
active_market_provider: MarketProvider = GovDataMarketProvider()
active_scheme_provider: SchemeProvider = LocalJsonSchemeProvider()
