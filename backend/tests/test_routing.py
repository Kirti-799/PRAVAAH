"""
backend/tests/test_routing.py

Automated integration tests for PRAVAAH Routing API Endpoints:
- GET /api/hydrology/routing-readiness
- GET /api/hydrology/routing-simulation
Verifies typed response models, explicit uncalibrated flags,
rejection of unstable parameters, and strict preservation of existing endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_routing_readiness_endpoint():
    """Verify routing-readiness endpoint returns complete catalog and uncalibrated status."""
    response = client.get("/api/hydrology/routing-readiness")
    assert response.status_code == 200

    data = response.json()
    assert data["service"] == "PRAVAAH Hydraulic Routing Readiness Evaluator"
    assert data["readiness_status"] == "ROUTING_PARAMETRIC_PROTOTYPE_UNCALIBRATED"
    assert data["target_gauge_id"] == "028-MDD"
    assert data["downstream_calibration_available"] is False

    # Check methods evaluation
    methods = {m["method_name"]: m["is_feasible"] for m in data["methods_evaluation"]}
    assert any("Dynamic Wave" in name for name in methods)
    assert any("Muskingum-Cunge" in name for name in methods)
    # St. Venant & Cunge must be infeasible
    for name, feasible in methods.items():
        if "Dynamic Wave" in name or "Muskingum-Cunge" in name or "Calibrated" in name:
            assert feasible is False

    # Check parameters detail
    assert len(data["parameters_detail"]) >= 8
    bathymetry = next(p for p in data["parameters_detail"] if p["symbol"] == "A(y), B(y)")
    assert bathymetry["status"] == "UNAVAILABLE"

    # Check critical blockers
    assert len(data["critical_blockers"]) >= 3
    assert any("028-MDD" in b for b in data["critical_blockers"])


def test_routing_simulation_default_2023_episode():
    """Verify routing simulation on the historic 2023 flood episode."""
    response = client.get("/api/hydrology/routing-simulation")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "SIMULATION_SUCCESS_UNCALIBRATED_PROTOTYPE"
    assert data["routing_method"] == "Hydrological Muskingum Storage Routing"
    assert data["episode_id"] == "EPISODE_2023_08"
    assert data["numerical_stability_verified"] is True
    assert data["mass_balance_error_percent"] < 0.1
    assert data["observed_hathnikund_peak_release_cumecs"] >= 8000.0
    assert data["simulated_peak_downstream_discharge_cumecs"] > 5000.0
    assert data["documented_delhi_crest_stage_m"] == 208.66

    # Verify disclaimer is explicit
    assert "SIMULATED DOWNSTREAM DISCHARGE — NOT OBSERVED DELHI WATER LEVEL" in data["scientific_disclaimer"]

    # Verify time series points have null stage
    assert len(data["time_series"]) > 0
    for pt in data["time_series"]:
        assert pt["observed_downstream_stage_m"] is None
        assert pt["simulated_downstream_discharge_cumecs"] >= 0.0


def test_routing_simulation_historical_episodes():
    """Verify simulation runs for 2019 and 2022 flood episodes."""
    # 2019 Episode
    res_2019 = client.get("/api/hydrology/routing-simulation?episode_id=EPISODE_2019_04&K_hours=36.0&x=0.20")
    assert res_2019.status_code == 200
    data_2019 = res_2019.json()
    assert data_2019["episode_id"] == "EPISODE_2019_04"
    assert data_2019["documented_delhi_crest_stage_m"] == 206.60

    # 2022 Episode
    res_2022 = client.get("/api/hydrology/routing-simulation?episode_id=EPISODE_2022_07&K_hours=36.0&x=0.20")
    assert res_2022.status_code == 200
    data_2022 = res_2022.json()
    assert data_2022["episode_id"] == "EPISODE_2022_07"
    assert data_2022["documented_delhi_crest_stage_m"] == 205.99


def test_routing_simulation_rejects_unstable_parameters():
    """
    Verify API rejects parameters violating numerical stability with HTTP 422.
    K=90h, x=0.4 -> 2*K*x = 72h. dt=24h < 72h -> negative C0!
    """
    response = client.get("/api/hydrology/routing-simulation?K_hours=90.0&x=0.40")
    assert response.status_code == 422
    assert "Numerical instability" in response.json()["detail"]


def test_routing_simulation_rejects_unknown_episode():
    """Verify API returns 404 for non-existent episode ID."""
    response = client.get("/api/hydrology/routing-simulation?episode_id=NON_EXISTENT_99")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_existing_endpoints_preserved():
    """Ensure existing endpoints /health, /summary, /events remain functional and intact."""
    res_health = client.get("/api/health")
    assert res_health.status_code == 200

    res_summary = client.get("/api/hydrology/summary")
    assert res_summary.status_code == 200
    assert res_summary.json()["service"] == "PRAVAAH Hydrological Intelligence Service"

    res_events = client.get("/api/hydrology/events")
    assert res_events.status_code == 200
    assert res_events.json()["total_episodes"] == 10


# ==============================================================================
# Phase 2C-B: Tabletop Scenario Simulation Endpoint Tests
# ==============================================================================

def test_tabletop_presets_endpoint():
    """Verify GET /api/hydrology/tabletop-presets returns preset hydrographs and parameter catalog."""
    response = client.get("/api/hydrology/tabletop-presets")
    assert response.status_code == 200
    data = response.json()
    assert "presets" in data
    assert len(data["presets"]) >= 4
    preset_ids = [p["preset_id"] for p in data["presets"]]
    assert "PRESET_CONSTANT" in preset_ids
    assert "PRESET_GRADUAL_RISE" in preset_ids
    assert "PRESET_FLASH_PULSE" in preset_ids
    assert "PRESET_SUSTAINED_HIGH" in preset_ids

    assert "documented_parameters" in data
    cfg_ids = [c["config_id"] for c in data["documented_parameters"]]
    assert "AUTHORITATIVE_BASELINE" in cfg_ids
    assert "ALTERNATIVE_UPPER_BOUND_HEURISTIC" in cfg_ids


def test_tabletop_scenario_simulation_success():
    """Verify POST /api/hydrology/tabletop-scenario routes a pulse hydrograph correctly."""
    payload = {
        "scenario_id": "TEST_PULSE_API",
        "scenario_name": "API Pulse Test",
        "scenario_type": "PULSE",
        "scenario_description": "Testing pulse routing via POST endpoint",
        "inflow_hydrograph": [400.0, 600.0, 6500.0, 1800.0, 800.0, 500.0, 400.0],
        "K_hours": 36.0,
        "x": 0.20,
        "dt_hours": 24.0,
    }
    response = client.post("/api/hydrology/tabletop-scenario", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["scenario_id"] == "TEST_PULSE_API"
    assert data["numerical_validity_status"] == "VALID"
    assert data["stability_criteria_met"] is True
    assert data["peak_inflow_discharge_cumecs"] == 6500.0
    assert data["peak_simulated_outflow_discharge_cumecs"] < 6500.0
    assert data["peak_attenuation_cumecs"] > 1000.0
    assert data["apparent_lag_hours"] >= 24.0
    assert data["mass_conservation_error_percent"] < 0.05
    assert data["reproducibility_hash"].startswith("sha256:")

    # Verify no simulated Delhi stage
    for pt in data["time_series"]:
        assert pt["observed_downstream_stage_m"] is None

    assert "MODE: TABLETOP SCENARIO SIMULATION" in data["scientific_disclaimer"]


def test_tabletop_scenario_constant_inflow_invariant():
    """Verify constant inflow yields zero attenuation and exact equality at all steps."""
    payload = {
        "scenario_id": "TEST_CONSTANT_API",
        "scenario_name": "Constant Inflow Invariant",
        "inflow_hydrograph": [1500.0] * 6,
        "K_hours": 36.0,
        "x": 0.20,
        "dt_hours": 24.0,
    }
    response = client.post("/api/hydrology/tabletop-scenario", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["peak_attenuation_cumecs"] == 0.0
    assert data["mass_conservation_error_percent"] < 0.001
    for pt in data["time_series"]:
        assert pt["simulated_outflow_cumecs"] == 1500.0


def test_tabletop_scenario_rejects_negative_discharge():
    """Verify negative discharge inputs are rejected with HTTP 422."""
    payload = {
        "scenario_id": "TEST_INVALID_NEG",
        "inflow_hydrograph": [500.0, -200.0, 800.0],
    }
    response = client.post("/api/hydrology/tabletop-scenario", json=payload)
    assert response.status_code == 422
    assert "violates physical non-negativity" in response.json()["detail"]


def test_tabletop_scenario_rejects_unstable_parameters():
    """Verify numerically unstable parameters are rejected with HTTP 422."""
    payload = {
        "scenario_id": "TEST_INVALID_UNSTABLE",
        "inflow_hydrograph": [500.0, 1000.0, 700.0],
        "K_hours": 80.0,
        "x": 0.35,  # 2Kx = 56h > dt=24h -> unstable!
        "dt_hours": 24.0,
    }
    response = client.post("/api/hydrology/tabletop-scenario", json=payload)
    assert response.status_code == 422
    assert "Numerical instability" in response.json()["detail"]


def test_tabletop_scenario_rejects_single_point_hydrograph():
    """Verify hydrograph with fewer than 2 points is rejected by Pydantic schema."""
    payload = {
        "scenario_id": "TEST_TOO_SHORT",
        "inflow_hydrograph": [500.0],
    }
    response = client.post("/api/hydrology/tabletop-scenario", json=payload)
    assert response.status_code == 422


def test_spatial_routing_simulation_endpoints_success():
    """Verify Phase 3E.4 spatial routing endpoints return 200 OK with mapped wave points."""
    # Test hydrology router endpoint
    resp1 = client.get("/api/hydrology/routing-simulation-spatial?episode_id=EPISODE_2023_08")
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["status"] == "SIMULATION_SUCCESS_SPATIAL_MAPPED"
    assert len(data1["time_steps"]) == 26
    assert data1["total_stations_count"] >= 55
    assert data1["reach_length_km"] >= 265.0
    assert "NOT A 2D FLOOD INUNDATION MODEL" in data1["scientific_disclaimer"]

    # Verify first point is OBSERVED release at Hathnikund
    first_pt = data1["time_steps"][0]["points"][0]
    assert first_pt["value_type"] == "OBSERVED"
    assert first_pt["chainage_km"] == 0.0

    # Test spatial router convenience endpoint
    resp2 = client.get("/api/spatial/routing/simulation?episode_id=EPISODE_2023_08")
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["status"] == "SIMULATION_SUCCESS_SPATIAL_MAPPED"


