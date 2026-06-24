import os
import json
from typing import Dict, Any, List
from app.providers.interfaces import SchemeProvider
from app.core.schemas import SchemeModel

class LocalJsonSchemeProvider(SchemeProvider):
    def get_schemes(self, region: str) -> List[SchemeModel]:
        """Loads available schemes from a local JSON file based on the region."""
        region_file = f"{region}.json"
        
        # Path relative to this file: ../../data/schemes/
        scheme_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "schemes", region_file)
        
        if not os.path.exists(scheme_path):
            return []
            
        with open(scheme_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        schemes = data.get("schemes", [])
        return [SchemeModel(**scheme) for scheme in schemes]
