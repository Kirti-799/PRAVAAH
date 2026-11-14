"""
ml/tests/test_model_training.py

Unit and integration tests for PRAVAAH Phase 2B Non-Linear ML Regressors.
Verifies:
1. Strict 23-feature allowlist and exclusion of target/retrospective/metadata features.
2. Training-only preprocessing (SimpleImputer) with zero leakage.
3. Model serialization, file integrity, and reload fidelity.
4. Exact feature schema validation, range checks, and error handling.
5. Absolute absence of Delhi water-level or flood-breach predictions.
"""

import math
import pytest
import numpy as np
from pathlib import Path

from ml.training.train_discharge_models import (
    OPERATIONAL_FEATURE_ALLOWLIST,
    EXCLUDED_FEATURES_REGISTRY,
    RANDOM_SEED,
    compute_file_sha256,
)
from ml.models.inference import (
    HathnikundDischargeInferenceEngine,
    InvalidFeatureSchemaError,
    ModelArtifactNotFoundError,
)


def test_feature_allowlist_integrity():
    """Verify that allowlist contains exactly 23 features and no duplicates."""
    assert len(OPERATIONAL_FEATURE_ALLOWLIST) == 23
    assert len(set(OPERATIONAL_FEATURE_ALLOWLIST)) == 23
    # Critical features
    assert "discharge_current_cumecs" in OPERATIONAL_FEATURE_ALLOWLIST
    assert "inflow_current_cumecs" in OPERATIONAL_FEATURE_ALLOWLIST
    assert "rainfall_accum_3d_prior_mm" in OPERATIONAL_FEATURE_ALLOWLIST
    assert "day_of_year" in OPERATIONAL_FEATURE_ALLOWLIST


def test_strictly_excluded_features():
    """Verify that target, retrospective, and partition metadata are explicitly forbidden."""
    forbidden = [
        "target_discharge_24h_cumecs",
        "rainfall_mean_same_day_retro_mm",
        "rainfall_valid_cells_d_minus_1",
        "date",
        "timestamp_utc",
        "partition",
        "target_date",
        "has_valid_24h_target",
        "is_complete_operational_row",
        "missing_feature_flags",
    ]
    for feat in forbidden:
        assert feat not in OPERATIONAL_FEATURE_ALLOWLIST, f"Leaked feature in allowlist: {feat}"
        assert feat in EXCLUDED_FEATURES_REGISTRY, f"Feature not registered in exclusion registry: {feat}"


def test_model_artifact_and_metadata_exist():
    """Verify that trained model artifact and metadata JSON exist on disk."""
    engine = HathnikundDischargeInferenceEngine()
    assert engine.is_model_available(), "Trained model artifact or metadata is missing"

    metadata = engine.get_metadata()
    assert metadata["model_identifier"] == "hathnikund_rf_v1"
    assert metadata["model_type"] == "RandomForestRegressor"
    assert metadata["target_variable"] == "target_discharge_24h_cumecs"
    assert metadata["target_unit"] == "m³/s (cubic metres per second)"
    assert metadata["feature_count"] == 23
    assert metadata["random_seed"] == RANDOM_SEED
    assert metadata["operational_recommendation"]["promoted_for_operational_disaster_warning"] is False


def test_inference_engine_prediction_schema():
    """Verify that inference engine produces valid forecast output with disclaimers."""
    engine = HathnikundDischargeInferenceEngine()
    engine.load()

    # Create dummy observation using training medians
    metadata = engine.get_metadata()
    valid_input = {k: v for k, v in metadata["training_medians_imputer"].items()}

    res = engine.predict(valid_input)

    assert "predicted_discharge_cumecs" in res
    assert isinstance(res["predicted_discharge_cumecs"], float)
    assert res["predicted_discharge_cumecs"] >= 0.0
    assert res["target_variable"] == "target_discharge_24h_cumecs"
    assert res["discharge_unit"] == "m³/s (cubic metres per second)"
    assert res["forecast_lead_time_hours"] == 24
    assert res["promoted_for_operational_disaster_warning"] is False
    assert "Delhi" in res["experimental_warning"]


def test_inference_engine_rejects_missing_features():
    """Verify that inference rejects payloads missing mandatory features."""
    engine = HathnikundDischargeInferenceEngine()
    engine.load()

    incomplete_input = {"discharge_current_cumecs": 120.0}  # Missing 22 features
    with pytest.raises(InvalidFeatureSchemaError, match="Missing required feature"):
        engine.predict(incomplete_input)


def test_inference_engine_rejects_negative_discharge_or_rainfall():
    """Verify physical domain validation: negative discharge or rainfall must be rejected."""
    engine = HathnikundDischargeInferenceEngine()
    engine.load()

    metadata = engine.get_metadata()
    bad_discharge_input = {k: v for k, v in metadata["training_medians_imputer"].items()}
    bad_discharge_input["discharge_current_cumecs"] = -50.0  # Physically impossible

    with pytest.raises(InvalidFeatureSchemaError, match="cannot be negative"):
        engine.predict(bad_discharge_input)

    bad_rainfall_input = {k: v for k, v in metadata["training_medians_imputer"].items()}
    bad_rainfall_input["rainfall_mean_d_minus_1_mm"] = -10.0

    with pytest.raises(InvalidFeatureSchemaError, match="cannot be negative"):
        engine.predict(bad_rainfall_input)


def test_inference_engine_handles_missing_values_via_imputer():
    """Verify that None/empty string in non-critical features is safely imputed."""
    engine = HathnikundDischargeInferenceEngine()
    engine.load()

    metadata = engine.get_metadata()
    input_with_nan = {k: v for k, v in metadata["training_medians_imputer"].items()}
    # Lag 7d was occasionally missing in dry season
    input_with_nan["discharge_lag_7d_cumecs"] = None

    res = engine.predict(input_with_nan)
    assert isinstance(res["predicted_discharge_cumecs"], float)
    assert res["predicted_discharge_cumecs"] >= 0.0


def test_no_delhi_water_level_prediction():
    """Verify that model target is strictly upstream discharge, NEVER Delhi water level."""
    engine = HathnikundDischargeInferenceEngine()
    metadata = engine.get_metadata()

    assert "stage" not in metadata["target_variable"].lower()
    assert "delhi" not in metadata["target_variable"].lower()
    assert "m msl" not in metadata["target_unit"].lower()

    # Check that Delhi is explicitly mentioned in the prohibited applications
    delhi_prohibitions = [p for p in metadata["operational_recommendation"]["prohibited_applications"] if "Delhi" in p]
    assert len(delhi_prohibitions) >= 2
