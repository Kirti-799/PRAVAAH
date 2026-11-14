"""
backend/tests/test_forecasting.py

Automated integration tests for PRAVAAH Forecasting API Endpoints:
- GET /api/forecasting/readiness: Upstream 24h dataset readiness & baseline benchmarks (Phase 2A).
- GET /api/forecasting/model-status: Model status, validation/test metrics, and governance (Phase 2B).
- POST /api/forecasting/predict: Validated 24h discharge forecast given 23 operational features (Phase 2B).
- GET /api/forecasting/sample-forecast: Demonstration forecast from latest verified historical observation (Phase 2B).

Verifies:
- Typed response models and schema conformance.
- Strict scientific gating and disclaimers separating upstream discharge from Delhi stage.
- Rejection of invalid, negative, or incomplete feature vectors.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from ml.training.train_discharge_models import OPERATIONAL_FEATURE_ALLOWLIST

client = TestClient(app)


def test_forecasting_readiness_endpoint():
    """Verify forecasting readiness endpoint returns complete metadata and baseline metrics."""
    response = client.get("/api/forecasting/readiness")
    assert response.status_code == 200

    data = response.json()
    assert data["service"] == "PRAVAAH Upstream Discharge Forecasting Readiness Service"
    assert data["status"] == "PRELIMINARY_BASELINES_EVALUATED_NOT_VALIDATED_FOR_OPERATIONS"
    assert data["target_station"] == "Hathnikund Barrage (HKB D/S)"
    assert data["target_unit"] == "m³/s (cumecs)"
    assert data["delhi_flood_stage_status"] == "STRICTLY_BLOCKED_PENDING_CWC_028_MDD_STAGE"
    assert data["dataset_available"] is True

    # Check partition counts
    assert data["dataset_rows_total"] == 2491
    assert data["valid_target_rows"] == 2468
    assert data["complete_operational_rows"] == 2345
    assert data["partitions"]["TRAIN"] == 1412
    assert data["partitions"]["VAL"] == 322
    assert data["partitions"]["TEST"] == 611

    # Check baseline benchmarks
    benchmarks = data["baseline_benchmarks"]
    assert len(benchmarks) >= 8

    val_models = {b["model_name"] for b in benchmarks if b["partition"] == "VAL"}
    assert "persistence" in val_models
    assert "linear_regression_ols" in val_models
    assert "trailing_3d_mean" in val_models
    assert "seasonal_naive_doy" in val_models

    coeffs = data["linear_model_coefficients"]
    assert coeffs["q_current_beta1"] > 0.0

    caveats = data["scientific_caveats"]
    assert any("NOT A DELHI FLOOD PREDICTION" in c for c in caveats)
    assert any("028-MDD" in c for c in caveats)


def test_model_status_endpoint():
    """Verify Phase 2B model status endpoint returns metrics, governance, and disclaimers."""
    response = client.get("/api/forecasting/model-status")
    assert response.status_code == 200

    data = response.json()
    assert data["service"] == "PRAVAAH Hathnikund Discharge Model Service"
    assert data["model_identifier"] == "hathnikund_rf_v1"
    assert data["model_type"] == "RandomForestRegressor"
    assert data["target_variable"] == "target_discharge_24h_cumecs"
    assert "m³/s" in data["target_unit"]
    assert data["forecast_horizon_hours"] == 24
    assert data["is_artifact_available"] is True
    assert data["operational_status"] == "EXPERIMENTAL_RESEARCH_BENCHMARK"
    assert data["promoted_for_operational_disaster_warning"] is False
    assert data["feature_count"] == 23
    assert len(data["feature_allowlist"]) == 23

    # Check validation metrics
    val = data["validation_metrics"]
    assert val["sample_count"] == 322
    assert val["mae_cumecs"] < 90.0  # RF beats persistence (97.39)
    assert val["rmse_cumecs"] < 500.0  # RF beats persistence (588.29)
    assert val["skill_score_vs_persistence"] > 0.25

    # Check test metrics
    test = data["test_metrics"]
    assert test["sample_count"] == 611

    # Check high flow sample counts
    high_flows = data["high_flow_samples"]
    assert high_flows["train_samples_ge_1500"] == 9
    assert high_flows["val_samples_ge_1500"] == 4
    assert high_flows["test_samples_ge_1500"] == 8

    # Check governance disclaimers
    prohibitions = data["prohibited_applications"]
    assert any("Delhi" in p for p in prohibitions)
    assert any("evacuation" in p.lower() for p in prohibitions)


def test_predict_endpoint_success():
    """Verify POST /api/forecasting/predict produces valid prediction on complete feature payload."""
    status_resp = client.get("/api/forecasting/model-status")
    allowlist = status_resp.json()["feature_allowlist"]

    # Provide valid feature dictionary
    valid_features = {feat: 15.0 for feat in allowlist}
    valid_features["day_of_year"] = 180.0
    valid_features["month"] = 7.0
    valid_features["sin_doy"] = 0.0
    valid_features["cos_doy"] = -1.0
    valid_features["is_monsoon"] = 1.0

    response = client.post("/api/forecasting/predict", json={"features": valid_features})
    assert response.status_code == 200

    data = response.json()
    assert data["model_identifier"] == "hathnikund_rf_v1"
    assert data["target_variable"] == "target_discharge_24h_cumecs"
    assert data["forecast_lead_time_hours"] == 24
    assert isinstance(data["predicted_discharge_cumecs"], float)
    assert data["predicted_discharge_cumecs"] >= 0.0
    assert data["promoted_for_operational_disaster_warning"] is False
    assert "experimental_warning" in data
    assert "Delhi" in data["experimental_warning"]


def test_predict_endpoint_rejects_missing_features():
    """Verify POST /api/forecasting/predict rejects payload missing required features with 422."""
    incomplete_features = {"discharge_current_cumecs": 120.0}
    response = client.post("/api/forecasting/predict", json={"features": incomplete_features})
    assert response.status_code == 422
    assert "Missing required feature" in response.json()["detail"]


def test_predict_endpoint_rejects_negative_discharge():
    """Verify POST /api/forecasting/predict rejects physically impossible negative discharge with 422."""
    status_resp = client.get("/api/forecasting/model-status")
    allowlist = status_resp.json()["feature_allowlist"]

    features = {feat: 10.0 for feat in allowlist}
    features["discharge_current_cumecs"] = -100.0  # Physically impossible

    response = client.post("/api/forecasting/predict", json={"features": features})
    assert response.status_code == 422
    assert "cannot be negative" in response.json()["detail"]


def test_sample_historical_forecast_endpoint():
    """Verify GET /api/forecasting/sample-forecast returns demonstration forecast with context."""
    response = client.get("/api/forecasting/sample-forecast")
    assert response.status_code == 200

    data = response.json()
    assert data["model_identifier"] == "hathnikund_rf_v1"
    assert data["forecast_lead_time_hours"] == 24
    assert isinstance(data["predicted_discharge_cumecs"], float)
    assert data["predicted_discharge_cumecs"] >= 0.0
    assert "Historical Observation Date" in data["observation_context"]
    assert data["promoted_for_operational_disaster_warning"] is False


# ==============================================================================
# Phase 3E.2 Hydrometeorological Coupling Tests
# ==============================================================================

def test_hydromet_status_endpoint():
    """Verify GET /api/forecasting/hydromet-status returns coupling audit and governance status."""
    response = client.get("/api/forecasting/hydromet-status")
    assert response.status_code == 200

    data = response.json()
    assert data["service"] == "PRAVAAH Hydrometeorological Coupling Service"
    assert data["coupling_status"] == "DISCONNECTED_FOR_AUTONOMOUS_OPERATIONS"
    assert data["has_live_discharge_telemetry"] is False
    assert data["has_live_meteorological_feed"] is True
    assert data["sampling_nodes_count"] == 20
    assert data["promoted_for_operational_disaster_warning"] is False

    # Check temporal alignment summary
    temporal = data["temporal_alignment_summary"]
    assert temporal["phase_shift_hours"] == 8.5
    assert "08:30" in temporal["imd_reporting_window"]
    assert "midnight" in temporal["open_meteo_daily_window"]

    # Check spatial comparison
    spatial = data["spatial_domain_comparison"]
    assert spatial["spatial_domain_match"] is False
    assert "91 IMD grid cells" in spatial["training_dataset_footprint"]
    assert "20 elevational point nodes" in spatial["live_sampling_footprint"]

    # Check warnings and caveats
    assert len(data["missing_telemetry_inputs"]) >= 2
    assert len(data["covariate_shift_warnings"]) >= 3
    assert len(data["governance_caveats"]) >= 2
    assert any("flood warnings" in c.lower() for c in data["governance_caveats"])


def test_predict_coupled_with_operator_discharge():
    """Verify POST /api/forecasting/predict-coupled with operator discharge and custom rainfall."""
    payload = {
        "current_discharge_cumecs": 120.0,
        "current_inflow_cumecs": 150.0,
        "discharge_history_cumecs": [120.0, 110.0, 100.0, 95.0, 90.0, 85.0, 80.0, 75.0],
        "use_live_catchment_rainfall": False,
        "custom_rainfall_mean_d_minus_1_mm": 12.5,
        "custom_rainfall_accum_3d_prior_mm": 35.0,
        "custom_rainfall_accum_7d_prior_mm": 65.0,
        "custom_rainfall_max_cell_3d_prior_mm": 22.0,
    }

    response = client.post("/api/forecasting/predict-coupled", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["model_identifier"] == "hathnikund_rf_v1"
    assert data["forecast_lead_time_hours"] == 24
    assert isinstance(data["predicted_discharge_cumecs"], float)
    assert data["predicted_discharge_cumecs"] >= 0.0
    assert data["operational_status"] == "EXPERIMENTAL_RESEARCH_BENCHMARK"
    assert data["promoted_for_operational_disaster_warning"] is False

    # Historical observations used
    hist = data["historical_observations_used"]
    assert hist["discharge_source"] == "OPERATOR_OR_EXTERNAL_INPUT"
    assert hist["discharge_current_cumecs"] == 120.0
    assert hist["inflow_current_cumecs"] == 150.0

    # Meteorological inputs used
    meteo = data["live_meteorological_inputs_used"]
    assert meteo["custom_rainfall_mean_d_minus_1_mm"] == 12.5
    assert meteo["custom_rainfall_accum_3d_prior_mm"] == 35.0

    # Experimental warning
    assert "flood warning" in data["experimental_warning"].lower()


def test_predict_coupled_handles_missing_telemetry_transparently():
    """Verify POST /api/forecasting/predict-coupled transparently documents missing live discharge telemetry."""
    payload = {
        "use_live_catchment_rainfall": False,
        "custom_rainfall_mean_d_minus_1_mm": 2.0,
        "custom_rainfall_accum_3d_prior_mm": 5.0,
        "custom_rainfall_accum_7d_prior_mm": 10.0,
        "custom_rainfall_max_cell_3d_prior_mm": 4.0,
    }

    response = client.post("/api/forecasting/predict-coupled", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["predicted_discharge_cumecs"] >= 0.0
    assert "live_discharge_telemetry" in data["missing_or_imputed_inputs"]
    assert "UNAVAILABLE_LIVE" in data["missing_or_imputed_inputs"]["live_discharge_telemetry"]
    assert data["promoted_for_operational_disaster_warning"] is False
    assert len(data["scientific_caveats"]) >= 3

