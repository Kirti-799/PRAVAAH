"""
backend/tests/test_hydrography.py

Automated integration tests for Phase 3B Hydrography REST API endpoints:
- GET /api/spatial/hydrography/status
- GET /api/spatial/hydrography/layers
- GET /api/spatial/hydrography/summary
- GET /api/spatial/hydrography/network
- GET /api/spatial/hydrography/chainage
- POST /api/spatial/hydrography/inspect
- Directory traversal security rejection.
"""

from pathlib import Path
import json
import pytest
from starlette.testclient import TestClient

from app.main import app
from ml.spatial.hydrography import HydrographyProcessor

client = TestClient(app)


def test_get_hydrography_status_endpoint():
    """Verifies /api/spatial/hydrography/status responds with valid structure."""
    response = client.get("/api/spatial/hydrography/status")
    assert response.status_code == 200
    data = response.json()
    assert "hydrography_availability" in data
    assert "scanned_directories" in data
    assert "scientific_notice" in data
    assert "Phase 3B" in data["milestone"]


def test_get_hydrography_layers_endpoint():
    """Verifies /api/spatial/hydrography/layers endpoint responds cleanly."""
    response = client.get("/api/spatial/hydrography/layers?clip_to_corridor=true")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "layers" in data
    assert "scientific_disclaimer" in data


def test_get_hydrography_summary_endpoint():
    """Verifies /api/spatial/hydrography/summary responds cleanly."""
    response = client.get("/api/spatial/hydrography/summary")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "scientific_disclaimer" in data


def test_get_hydrography_network_endpoint():
    """Verifies /api/spatial/hydrography/network endpoint responds cleanly."""
    response = client.get("/api/spatial/hydrography/network")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "nodes_count" in data
    assert "edges_count" in data


def test_get_hydrography_chainage_endpoint():
    """Verifies /api/spatial/hydrography/chainage endpoint responds cleanly."""
    response = client.get("/api/spatial/hydrography/chainage?interval_km=5.0")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "origin_point_name" in data
    assert "terminus_point_name" in data
    assert "calculation_crs" in data


def test_inspect_hydrography_file_with_synthetic_fixture(tmp_path: Path):
    """
    Creates a temporary synthetic fixture in the hydrography directory
    and verifies POST /api/spatial/hydrography/inspect performs full validation.
    """
    repo_root = Path(__file__).resolve().parents[2]
    hydro_dir = repo_root / "data" / "raw" / "spatial" / "hydrography"
    hydro_dir.mkdir(parents=True, exist_ok=True)

    fixture_name = "test_synthetic_inspect.geojson"
    fixture_path = hydro_dir / fixture_name

    try:
        HydrographyProcessor.create_synthetic_hydrography_fixture(fixture_path, include_gaps=False)

        response = client.post(
            "/api/spatial/hydrography/inspect",
            json={"relative_file_name": fixture_name},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["source_file"] == fixture_name
        assert data["valid_features_count"] > 0
        assert data["metric_crs"] == "EPSG:32643"
        assert "main_river" in data["features_by_class"]
        assert data["main_channel_continuity"] == "CONTINUOUS"
    finally:
        if fixture_path.exists():
            fixture_path.unlink()


def test_inspect_hydrography_directory_traversal_blocked():
    """Verifies directory traversal attempts are blocked with 422 Unprocessable Entity."""
    response = client.post(
        "/api/spatial/hydrography/inspect",
        json={"relative_file_name": "../../secrets.geojson"},
    )
    assert response.status_code == 422


def test_inspect_hydrography_missing_file_returns_404():
    """Verifies querying a nonexistent file returns 404 Not Found."""
    response = client.post(
        "/api/spatial/hydrography/inspect",
        json={"relative_file_name": "does_not_exist_999.geojson"},
    )
    assert response.status_code == 404
