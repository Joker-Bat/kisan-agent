import logging
import math
import os
from typing import Any

import pandas as pd

from app.providers.interfaces import CropProvider

logger = logging.getLogger(__name__)


class LocalCsvCropProvider(CropProvider):
    def __init__(self, csv_path: str | None = None):
        if csv_path is None:
            # Dynamically resolve relative to this file's directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.csv_path = os.path.normpath(
                os.path.join(current_dir, "..", "..", "data", "Crop_recommendation.csv")
            )
        else:
            self.csv_path = csv_path
        self.stats: dict[str, dict[str, dict[str, float]]] = {}

    def _load_data(self) -> None:
        """Lazy loader: Loads the Kaggle Crop recommendation dataset and precomputes centroids."""
        # Only load if not already loaded and cached
        if self.stats:
            return

        if not os.path.exists(self.csv_path):
            logger.warning(f"Crop recommendation dataset not found at {self.csv_path}")
            return

        logger.info(f"Loading crop recommendation dataset from {self.csv_path}")
        try:
            df = pd.read_csv(self.csv_path)
            features = ["N", "P", "K", "ph", "rainfall", "temperature"]
            grouped = df.groupby("label")
            for crop, group in grouped:
                self.stats[crop] = {}
                for f in features:
                    mean_val = float(group[f].mean())
                    std_val = float(group[f].std())
                    # Prevent division by zero
                    if std_val < 1e-3:
                        std_val = 1e-3
                    self.stats[crop][f] = {"mean": mean_val, "std": std_val}
        except Exception as e:
            logger.error(f"Error loading crop dataset stats: {e}", exc_info=True)

    def match_crops(
        self,
        n: float | None = None,
        p: float | None = None,
        k: float | None = None,
        ph: float | None = None,
        rainfall: float | None = None,
        temperature: float | None = None,
    ) -> list[dict[str, Any]]:
        """Matches input soil/climate parameters against the crop centroids using Z-score distance."""
        # Trigger lazy loader
        self._load_data()

        if not self.stats:
            logger.warning("No crop stats available for matching.")
            return []

        inputs = {
            "N": n,
            "P": p,
            "K": k,
            "ph": ph,
            "rainfall": rainfall,
            "temperature": temperature,
        }

        # Filter out features that are None
        active_inputs = {f: val for f, val in inputs.items() if val is not None}
        if not active_inputs:
            logger.info("match_crops called with no active soil/weather inputs.")
            return []

        scores = []
        for crop, f_stats in self.stats.items():
            d_squared = 0.0
            for f, val in active_inputs.items():
                if f in f_stats:
                    mean = f_stats[f]["mean"]
                    std = f_stats[f]["std"]
                    d_squared += ((val - mean) / std) ** 2

            # Compatibility score: 100 - 10 * sqrt(D^2)
            dist = math.sqrt(d_squared)
            compatibility = max(0.0, 100.0 - 10.0 * dist)
            scores.append(
                {
                    "crop": str(crop),
                    "compatibility": round(compatibility, 1),
                    "distance": round(dist, 3),
                }
            )

        # Sort by compatibility in descending order
        scores.sort(key=lambda x: x["compatibility"], reverse=True)
        return scores[:5]
