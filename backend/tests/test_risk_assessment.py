"""backend/tests/test_risk_assessment.py

Unit and integration tests for the simplified PRAVAAH flood risk assessment endpoints:
- GET /api/assessment/areas
- POST /api/assessment/assess (2 to 10 days horizon)
- Confidence calculation and uncertainty decay
- Candidate shelter formatting and de-authentication
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


def test_confidence_decay_calculation():
    """Verify confidence decays progressively from 2 to 10 days."""
    conf_2d = risk_assessment_service.calculate_confidence(2)
    conf_5d = risk_assessment_service.calculate_confidence(5)
    conf_10d = risk_assessment_service.calculate_confidence(10)

    assert conf_2d.confidence_level == "HIGH"
    assert conf_2d.confidence_score_pct >= 85
    assert conf_5d.confidence_level == "MODERATE"
    assert conf_10d.confidence_level == "LOW"
    assert conf_10d.confidence_score_pct < conf_2d.confidence_score_pct


def test_assess_risk_default_horizon():
    """Test risk assessment for Delhi Central with 3-day forecast."""
    payload = {
        "area_id": "DELHI_CENTRAL",
        "forecast_days": 3,
    }
    response = client.post("/api/assessment/assess", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["area_id"] == "DELHI_CENTRAL"
    assert data["forecast_days"] == 3
    assert data["risk_level"] in ["LOW", "MODERATE", "HIGH"]
    assert data["risk_color"] in ["GREEN", "ORANGE", "RED"]
    assert "summary" in data
    assert "guidance_action" in data
    assert data["confidence"]["forecast_days"] == 3

    # Upstream ML forecast
    assert "upstream_ml_forecast" in data
    assert data["upstream_ml_forecast"]["predicted_inflow_cumecs"] > 0
    assert "Hathnikund" in data["upstream_ml_forecast"]["model_name"]

    # Reaches and stations
    assert len(data["reach_risks"]) >= 5
    assert len(data["station_risks"]) == 7

    # Candidate shelters
    assert len(data["candidate_shelters"]) >= 5
    first_shelter = data["candidate_shelters"][0]
    assert "ILLUSTRATIVE_PROTOTYPE" in first_shelter["validation_status"]
    assert first_shelter["approx_distance_km"] >= 0.0

    # Scientific provenance
    assert "ml_model_prediction" in data["scientific_provenance"]
    assert "rule_based_risk_engine" in data["scientific_provenance"]
    assert "unavailable_realtime_data" in data["scientific_provenance"]


def test_assess_risk_long_horizon_10_days():
    """Test 10-day forecast horizon reflects low confidence and transparent uncertainty."""
    payload = {
        "area_id": "ALL_CORRIDOR",
        "forecast_days": 10,
    }
    response = client.post("/api/assessment/assess", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["forecast_days"] == 10
    assert data["confidence"]["confidence_level"] == "LOW"
    assert "Advisory only" in data["confidence"]["decay_explanation"]

