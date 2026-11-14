"""
backend/tests/test_river.py

Integration test suite for PRAVAAH River Network & Hydrography API (Phase 3B):
- GET /api/spatial/river/status
- GET /api/spatial/river/features
- POST /api/spatial/river/inspect
"""

from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from ml.spatial.river import RiverNetworkValidator

client = TestClient(app)


def test_get_river_status_unacquired():
    """Verify river/status returns structured availability and directory scanning result when unacquired."""
    response = client.get("/api/spatial/river/status")
    assert response.status_code == 200
    data = response.json()

    assert data["service"] == "PRAVAAH River Network & Hydrography Inspector"
    assert data["milestone"] == "Phase 3B — River Network & Geospatial Layer Integration"
    assert "river_data_availability" in data
    assert data["scanned_directory"].endswith("data\\raw\\spatial\\hydrography") or data["scanned_directory"].endswith("data/raw/spatial/hydrography")
    assert "scientific_notice" in data


def test_get_river_features_unacquired_returns_empty_fc():
    """Verify river/features returns empty FeatureCollection with status UNAVAILABLE when unacquired."""
    response = client.get("/api/spatial/river/features")
    assert response.status_code == 200
    data = response.json()

    assert data["type"] == "FeatureCollection"
    assert "features" in data
    assert "properties" in data
    if data["properties"].get("status") == "UNAVAILABLE":
        assert len(data["features"]) == 0
        assert "strictly refuses to fabricate" in data["properties"]["disclaimer"]


def test_inspect_river_blocks_directory_traversal():
    """Verify security guard: directory traversal payloads are rejected with HTTP 422."""
    payloads = [
        "../../etc/passwd",
        "../secret.geojson",
        "/etc/shadow",
        "nested/sub/network.geojson",
    ]
    for p in payloads:
        response = client.post("/api/spatial/river/inspect", json={"relative_file_name": p})
        assert response.status_code == 422
        assert "Directory traversal" in response.json()["detail"]


def test_inspect_river_blocks_invalid_extension():
    """Verify non-vector extensions are rejected with HTTP 422."""
    response = client.post("/api/spatial/river/inspect", json={"relative_file_name": "network.csv"})
    assert response.status_code == 422
    assert "Invalid file extension" in response.json()["detail"]


def test_inspect_river_missing_file_returns_404():
    """Verify non-existent vector file inside hydrography directory returns HTTP 404."""
    response = client.post("/api/spatial/river/inspect", json={"relative_file_name": "non_existent.geojson"})
    assert response.status_code == 404
    assert "does not exist" in response.json()["detail"]


def test_inspect_river_valid_synthetic_fixture():
    """
    Test river dataset inspection by temporarily placing a synthetic fixture in data/raw/spatial/hydrography/.
    Cleans up fixture immediately after test.
    """
    hydro_dir = Path("data/raw/spatial/hydrography").resolve()
    hydro_dir.mkdir(parents=True, exist_ok=True)
    fixture_name = "_test_synthetic_river.geojson"
    fixture_path = hydro_dir / fixture_name

    try:
        RiverNetworkValidator.create_synthetic_river_fixture(
            output_path=fixture_path,
            crs_epsg=4326,
            corridor_aligned=True,
        )

        response = client.post("/api/spatial/river/inspect", json={"relative_file_name": fixture_name})
        assert response.status_code == 200
        data = response.json()

        assert data["dataset_file"] == fixture_name
        assert data["total_features"] == 3
        assert data["valid_features_count"] == 3
        assert data["projected_metric_crs"] == "EPSG:32643"
        assert data["intersects_study_area"] is True
        assert data["total_length_km"] > 0.0

    finally:
        if fixture_path.exists():
            fixture_path.unlink()
