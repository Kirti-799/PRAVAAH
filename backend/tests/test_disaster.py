"""Unit tests for Disaster Intelligence and Shelters API routes."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_disaster_risk_summary():
    """Verify disaster risk summary returns authentic structure and non-fabricated data."""
    response = client.get("/api/disaster/risk-summary")
    assert response.status_code == 200
    data = response.json()
    assert "overall_alert_level" in data
    assert "active_advisories" in data
    assert "cwc_gauge" in data
    assert "discharge_status" in data
    assert "shelters_available" in data
    assert "total_shelter_capacity" in data
    assert "population_exposure" in data

    # Verify CWC Gauge thresholds
    cwc = data["cwc_gauge"]
    assert cwc["warning_level_msl"] == 204.50
    assert cwc["danger_level_msl"] == 205.33
    assert cwc["highest_flood_level_msl"] == 208.66

    # Verify population exposure disclaimer
    pop = data["population_exposure"]
    assert "disclaimer" in pop
    assert "raster" in pop["disclaimer"].lower()


def test_disaster_risk_summary_high_inflow():
    """Verify high inflow triggers warning status."""
    response = client.get("/api/disaster/risk-summary?inflow_cumecs=5000.0")
    assert response.status_code == 200
    data = response.json()
    assert data["overall_alert_level"] == "WARNING"
    assert data["discharge_status"]["risk_category"] == "HIGH_FLOOD"


def test_disaster_shelters_geojson():
    """Verify shelters GeoJSON returns valid FeatureCollection."""
    response = client.get("/api/disaster/shelters")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) >= 5
    for feat in data["features"]:
        assert feat["type"] == "Feature"
        assert feat["geometry"]["type"] == "Point"
        assert "capacity_persons" in feat["properties"]
        assert "facilities" in feat["properties"]
        assert feat["properties"]["status"] == "ILLUSTRATIVE_PROTOTYPE"


def test_disaster_evacuation_corridors_geojson():
    """Verify evacuation corridors GeoJSON returns valid FeatureCollection."""
    response = client.get("/api/disaster/evacuation-corridors")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) >= 4
    for feat in data["features"]:
        assert feat["type"] == "Feature"
        assert feat["geometry"]["type"] == "LineString"
        assert "destination_shelter_id" in feat["properties"]
        assert feat["properties"]["status"] == "UNVALIDATED_PROTOTYPE"

