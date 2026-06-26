import json
import os

from app.core.schemas import SchemeModel
from app.providers.interfaces import SchemeProvider


class LocalJsonSchemeProvider(SchemeProvider):
    def get_schemes(self, region: str) -> list[SchemeModel]:
        """Loads available schemes from a local JSON file based on the region."""
        region_file = f"{region}.json"

        # Path relative to this file: ../../data/schemes/
        scheme_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "data", "schemes", region_file
        )

        if not os.path.exists(scheme_path):
            return []

        with open(scheme_path, encoding="utf-8") as f:
            data = json.load(f)

        schemes = data.get("schemes", [])
        return [SchemeModel(**scheme) for scheme in schemes]
