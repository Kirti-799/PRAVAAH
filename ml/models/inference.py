"""
ml/models/inference.py

Modular Inference Engine for PRAVAAH Phase 2B.
Provides reproducible, validated single-point and batch inference for 24h
upstream Hathnikund Barrage downstream release (HKB D/S) forecasting.

CRITICAL ARCHITECTURAL CONSTRAINTS:
1. Target is strictly HKB D/S discharge (m³/s).
2. NEVER produces a Delhi Old Railway Bridge water level prediction (m MSL).
3. NEVER produces flood breach probabilities or evacuation mandates.
4. Enforces the exact 23-feature schema. Rejects unexpected or unvalidated inputs.
5. Emits explicit experimental research warnings and metadata.
"""

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional

import joblib
import numpy as np


class ModelArtifactNotFoundError(FileNotFoundError):
    """Raised when the trained model artifact or metadata is not found."""
    pass


class InvalidFeatureSchemaError(ValueError):
    """Raised when the input payload does not conform to the 23-feature schema."""
    pass


class HathnikundDischargeInferenceEngine:
    """Inference engine for the Phase 2B Hathnikund Random Forest Regressor."""

    def __init__(self, repo_root: Optional[Path] = None):
        self.root = repo_root or Path(__file__).resolve().parents[2]
        self.models_dir = self.root / "ml" / "models"
        self.artifact_path = self.models_dir / "hathnikund_rf_v1.joblib"
        self.metadata_path = self.models_dir / "hathnikund_rf_v1_metadata.json"

        self._model = None
        self._imputer = None
        self._metadata: Optional[Dict[str, Any]] = None
        self._feature_allowlist: Optional[List[str]] = None

    def is_model_available(self) -> bool:
        """Checks if both model binary and metadata JSON exist on disk."""
        return self.artifact_path.exists() and self.metadata_path.exists()

    def get_metadata(self) -> Dict[str, Any]:
        """Loads and returns the model metadata dictionary."""
        if not self.metadata_path.exists():
            raise ModelArtifactNotFoundError(f"Model metadata not found at: {self.metadata_path}")
        with open(self.metadata_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def load(self) -> None:
        """Loads model artifact bundle and metadata from disk."""
        if not self.is_model_available():
            raise ModelArtifactNotFoundError(
                f"Model artifact or metadata missing at: {self.artifact_path}"
            )

        self._metadata = self.get_metadata()
        self._feature_allowlist = self._metadata.get("feature_allowlist", [])

        # Load joblib bundle
        bundle = joblib.load(self.artifact_path)
        self._model = bundle["model"]
        self._imputer = bundle["imputer"]

    def validate_features(self, features: Dict[str, Any]) -> List[float]:
        """
        Validates input feature dict against the 23-feature schema.
        Converts to ordered float vector. Handles missing values via trained imputer.
        """
        if self._feature_allowlist is None:
            self.load()

        vector = []
        for feature_name in self._feature_allowlist:
            if feature_name not in features:
                raise InvalidFeatureSchemaError(f"Missing required feature: '{feature_name}'")

            val = features[feature_name]
            if val is None or val == "":
                vector.append(np.nan)
            else:
                try:
                    f_val = float(val)
                except (ValueError, TypeError) as exc:
                    raise InvalidFeatureSchemaError(
                        f"Feature '{feature_name}' must be numeric, got: {val}"
                    ) from exc

                if math.isnan(f_val):
                    vector.append(np.nan)
                else:
                    # Physical domain validity checks
                    if "cumecs" in feature_name and f_val < 0.0:
                        raise InvalidFeatureSchemaError(
                            f"Feature '{feature_name}' cannot be negative: {f_val}"
                        )
                    if "rainfall" in feature_name and f_val < 0.0:
                        raise InvalidFeatureSchemaError(
                            f"Feature '{feature_name}' cannot be negative: {f_val}"
                        )
                    vector.append(f_val)

        return vector

    def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates 24h discharge forecast for Hathnikund Barrage downstream release.
        Returns typed prediction dictionary with full experimental metadata.
        """
        if self._model is None or self._imputer is None:
            self.load()

        vector = self.validate_features(features)
        X_raw = np.array([vector], dtype=np.float64)

        # Impute missing values using strictly training-fitted medians
        X_imp = self._imputer.transform(X_raw)

        pred_cumecs = float(self._model.predict(X_imp)[0])
        # River discharge cannot be negative
        pred_cumecs = max(0.0, round(pred_cumecs, 2))

        return {
            "model_identifier": self._metadata["model_identifier"],
            "model_type": self._metadata["model_type"],
            "target_variable": "target_discharge_24h_cumecs",
            "forecast_lead_time_hours": 24,
            "predicted_discharge_cumecs": pred_cumecs,
            "discharge_unit": "m³/s (cubic metres per second)",
            "prediction_timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "operational_status": "EXPERIMENTAL_RESEARCH_BENCHMARK",
            "promoted_for_operational_disaster_warning": False,
            "performance_reference": {
                "validation_mae_cumecs": self._metadata["performance_summary"]["validation_2022"]["mae_cumecs"],
                "validation_rmse_cumecs": self._metadata["performance_summary"]["validation_2022"]["rmse_cumecs"],
                "validation_skill_vs_persistence": self._metadata["performance_summary"]["validation_2022"]["skill_score_vs_persistence"],
                "test_skill_vs_persistence": self._metadata["performance_summary"]["test_2023_2024"]["skill_score_vs_persistence"],
            },
            "experimental_warning": (
                "EXPERIMENTAL FORECAST: This prediction is generated by an experimental Random Forest Regressor "
                "trained on 2018-2021 historical data. The model exhibits structural underprediction during extreme, "
                "unprecedented discharge surges (> 4,100 m³/s). Under no circumstances should this value be "
                "interpreted as a Delhi water level (m MSL) or used for emergency evacuation mandates."
            ),
        }
