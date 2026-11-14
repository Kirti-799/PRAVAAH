"""
backend/tests/test_hydrology.py

Automated tests for PRAVAAH Hydrological Intelligence API routes:
- GET /api/hydrology/summary
- GET /api/hydrology/events
- Graceful missing-data handling (HTTP 503)
- Target gauge unobserved integrity check
"""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.hydrology import HydrologyService

client = TestClient(app)


def test_get_hydrology_summary_success():
    """Verify that GET /api/hydrology/summary returns 200 and adheres to contract."""
    response = client.get("/api/hydrology/summary")
    assert response.status_code == 200
    data = response.json()

    assert data["service"] == "PRAVAAH Hydrological Intelligence Service"
    assert "latest_observations" in data
    assert "rainfall_accumulations" in data
    assert "discharge_statistics" in data
    assert "data_quality" in data
    assert "limitations" in data

    latest = data["latest_observations"]
    assert latest["inflow_discharge_cumecs"] is not None
    assert latest["release_discharge_cumecs"] is not None
    assert latest["inflow_discharge_cumecs"] >= 0.0
    assert latest["release_discharge_cumecs"] >= 0.0

    # Critical downstream target integrity check:
    tg = latest["target_gauge"]
    assert tg["station_id"] == "028-MDD"
    assert tg["danger_mark_m"] == 205.33
    assert tg["observation_status"] == "DATA_RESTRICTED_PENDING_CWC_REQUISITION"
    assert tg["latest_water_level_m"] is None  # MUST NEVER be fabricated!

    # Rainfall accumulations check
    rf_accum = data["rainfall_accumulations"]
    assert rf_accum["spatial_coverage_cells"] == 91
    assert rf_accum["accum_1d_mm"] is not None
    assert rf_accum["accum_3d_mm"] is not None
    assert rf_accum["accum_7d_mm"] is not None

    # Discharge statistics check
    d_stats = data["discharge_statistics"]
    assert d_stats["total_days"] > 2000
    assert d_stats["inflow_statistics_hkb_us"]["max_cumecs"] >= 17000.0
    assert d_stats["release_statistics_hkb_ds"]["max_cumecs"] >= 8000.0


def test_get_historical_events_success():
    """Verify that GET /api/hydrology/events returns extracted episodes."""
    response = client.get("/api/hydrology/events")
    assert response.status_code == 200
    data = response.json()

    assert data["service"] == "PRAVAAH Historical Flood Events Registry"
    assert data["total_episodes"] >= 1
    episodes = data["episodes"]
    assert len(episodes) == data["total_episodes"]

    # Verify documented flood episodes are captured
    historical_floods = [e for e in episodes if e["is_documented_historical_flood"]]
    assert len(historical_floods) >= 3  # Aug 2019, Sep 2022, Jul 2023

    # Check that August 2019 reached > 15,000 cumecs inflow
    aug_2019 = next((e for e in episodes if "2019" in e["start_date"]), None)
    assert aug_2019 is not None
    assert aug_2019["peak_upstream_inflow_cumecs"] > 15000.0


def test_missing_dataset_returns_503(monkeypatch, tmp_path):
    """Verify that if files are absent, an explicit 503 is returned instead of fabricated data."""
    empty_dir = tmp_path / "empty_data"
    empty_dir.mkdir()

    from app.api.routes import hydrology as hydrology_route
    broken_service = HydrologyService(data_dir=empty_dir)
    monkeypatch.setattr(hydrology_route, "service", broken_service)

    response_summary = client.get("/api/hydrology/summary")
    assert response_summary.status_code == 503
    assert "unavailable" in response_summary.json()["detail"].lower()

    response_events = client.get("/api/hydrology/events")
    assert response_events.status_code == 503
    assert "unavailable" in response_events.json()["detail"].lower()


def test_health_endpoint_remains_operational():
    """Verify that existing health check continues to function identically."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "PRAVAAH API"
