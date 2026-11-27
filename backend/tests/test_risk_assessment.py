"""backend/tests/test_risk_assessment.py

Unit and integration tests for the simplified PRAVAAH 24-hour flood risk assessment endpoints:
- GET /api/assessment/areas
- POST /api/assessment/assess (Strict 24-hour prediction horizon)
- 3-tier risk categories (GREEN / YELLOW / RED)
- Audited ML metrics (Test R²=0.380, RMSE=469.5 m³/s, MAE=95.8 m³/s)
- Candidate shelter formatting and static planning capacity guardrails
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.risk_assessment_service import risk_assessment_service

client = TestClient(app)


def test_get_supported_areas():
    """Verify supported areas endpoint returns authentic geographical entities."""
    response = client.get("/api/assessment/areas")
    assert response.status_code == 200
    data = response.json()
    assert "areas" in data
    assert len(data["areas"]) >= 6
    area_ids = [a["id"] for a in data["areas"]]
    assert "DELHI_CENTRAL" in area_ids
    assert "ALL_CORRIDOR" in area_ids
    assert "UPSTREAM_CATCHMENT" in area_ids
    assert data["default_area_id"] == "DELHI_CENTRAL"
    assert data["total_corridor_length_km"] == 268.94


def test_confidence_24h_horizon():
    """Verify confidence reflects the 24-hour operational synoptic horizon."""
    conf = risk_assessment_service.calculate_confidence(1)
    assert conf.confidence_level == "HIGH"
    assert conf.confidence_score_pct >= 90
    assert conf.horizon_hours == 24


def test_assess_risk_24h_delhi_central():
    """Test 24-hour flood risk assessment for Delhi Central."""
    payload = {
        "area_id": "DELHI_CENTRAL",
    }
    response = client.post("/api/assessment/assess", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["area_id"] == "DELHI_CENTRAL"
    assert data["horizon_hours"] == 24
    assert data["risk_level"] in ["LOW", "MODERATE", "HIGH"]
    assert data["risk_color"] in ["GREEN", "YELLOW", "RED"]
    assert "summary" in data
    assert "guidance_action" in data
    assert "next 24 hours" in data["summary"].lower()

    # Upstream ML forecast with audited metrics
    ml_forecast = data["upstream_ml_forecast"]
    assert ml_forecast["predicted_inflow_cumecs"] > 0
    assert "Hathnikund" in ml_forecast["model_name"]
    assert ml_forecast["model_r2_score"] == 0.380
    assert ml_forecast["model_rmse_cumecs"] == 469.5
    assert ml_forecast["model_mae_cumecs"] == 95.8
    assert ml_forecast["horizon_hours"] == 24

    # Reaches and stations
    assert len(data["reach_risks"]) >= 5
    assert len(data["station_risks"]) == 7
    for r in data["reach_risks"]:
        assert r["risk_color"] in ["GREEN", "YELLOW", "RED"]

    # Candidate shelters with static planning capacity disclaimer
    assert len(data["candidate_shelters"]) >= 5
    first_shelter = data["candidate_shelters"][0]
    assert "ILLUSTRATIVE_PROTOTYPE" in first_shelter["validation_status"]
    assert first_shelter["approx_distance_km"] >= 0.0

    # Scientific provenance with 3-way distinction
    provenance = data["scientific_provenance"]
    assert "0.380" in provenance["ml_model_prediction"]
    assert "rule_based_risk_engine" in provenance
    assert "unavailable_realtime_data" in provenance


def test_assess_risk_corridor_all():
    """Test 24-hour assessment across the entire corridor."""
    payload = {
        "area_id": "ALL_CORRIDOR",
    }
    response = client.post("/api/assessment/assess", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["area_id"] == "ALL_CORRIDOR"
    assert data["horizon_hours"] == 24
    assert data["risk_color"] in ["GREEN", "YELLOW", "RED"]
    assert data["confidence"]["confidence_level"] == "HIGH"
