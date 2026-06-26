import json
import logging
import os

from app.core.schemas import SchemeModel
from app.providers.interfaces import SchemeProvider

logger = logging.getLogger(__name__)


class LocalJsonSchemeProvider(SchemeProvider):
    def __init__(self) -> None:
        self._cache: dict[str, list[SchemeModel]] = {}

    def get_schemes(self, region: str) -> list[SchemeModel]:
        """Loads available schemes from a local JSON file based on the region, with caching."""
        if region in self._cache:
            logger.debug(f"Retrieved schemes for region {region} from cache.")
            return self._cache[region]

        region_file = f"{region}.json"

        # Path relative to this file: ../../data/schemes/
        scheme_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "data", "schemes", region_file
        )

        if not os.path.exists(scheme_path):
            logger.warning(f"Scheme file not found at {scheme_path} for region {region}.")
            self._cache[region] = []
            return []

        logger.info(f"Loading schemes from {scheme_path} for region {region}.")
        try:
            with open(scheme_path, encoding="utf-8") as f:
                data = json.load(f)

            schemes_data = data.get("schemes", [])
            schemes = [SchemeModel(**scheme) for scheme in schemes_data]
            self._cache[region] = schemes
            return schemes
        except Exception as e:
            logger.error(f"Error loading scheme JSON at {scheme_path}: {e}", exc_info=True)
            return []
