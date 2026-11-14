"""
backend/tests/test_spatial.py

Integration test suite for PRAVAAH Spatial Data Infrastructure & Terrain API:
- GET /api/spatial/inventory
- GET /api/spatial/study-area
- GET /api/spatial/dem/status
- POST /api/spatial/dem/inspect
- GET /api/spatial/terrain/summary
"""

import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from ml.spatial.dem import DEMValidator

client = TestClient(app)


def test_get_spatial_inventory():
    """Verify inventory endpoint returns candidate spatial datasets and provenance."""
    response = client.get("/api/spatial/inventory")
    assert response.status_code == 200
    data = response.json()

    assert data["service"] == "PRAVAAH Spatial Data Infrastructure"
    assert data["total_datasets"] >= 5

    dataset_ids = [d["dataset_id"] for d in data["datasets"]]
    assert "SRTM_30M_GLOBAL" in dataset_ids
    assert "COPERNICUS_GLO30" in dataset_ids
    assert "BHUVAN_CARTODEM_30M" in dataset_ids
    assert "OSM_YAMUNA_HYDROGRAPHY" in dataset_ids
    assert "DDA_O_ZONE_FLOODPLAIN" in dataset_ids

    # Verify unacquired status is explicit
    for ds in data["datasets"]:
        assert ds["current_status"] == "UNAVAILABLE_IN_REPOSITORY"
        assert ds["actual_local_path"] is None


def test_get_study_area_metadata():
    """Verify study-area endpoint returns verified rectangular bounds and CRS definitions."""
    response = client.get("/api/spatial/study-area")
    assert response.status_code == 200
    data = response.json()

    assert data["geometry_type"] == "Rectangular Bounding Box"
    assert "EPSG:4326" in data["geographic_crs"]
    assert "EPSG:32643" in data["projected_crs"]
    assert data["reach_length_km"] == 220.0

    bounds = data["bounds"]
    assert bounds["west_lon"] == 76.85
    assert bounds["south_lat"] == 28.50
    assert bounds["east_lon"] == 77.60
    assert bounds["north_lat"] == 30.40

    # Verify GeoJSON polygon format
    geojson = data["geojson"]
    assert geojson["type"] == "Polygon"
    assert len(geojson["coordinates"][0]) == 5

    # Verify limitations are explicit
    assert any("RECTANGULAR BOUNDING EXTENT" in lim for lim in data["scientific_limitations"])


def test_get_dem_status():
    """Verify dem/status returns structured availability and directory scanning result."""
    response = client.get("/api/spatial/dem/status")
    assert response.status_code == 200
    data = response.json()

    assert "dem_availability" in data
    assert data["scanned_directory"].endswith("data\\raw\\spatial\\dem") or data["scanned_directory"].endswith("data/raw/spatial/dem")
    assert "acquisition_guide" in data or data["dem_availability"] == "AVAILABLE"
    assert "scientific_notice" in data


def test_inspect_dem_blocks_directory_traversal():
    """Verify security guard: directory traversal payloads are rejected with HTTP 422."""
    payloads = [
        "../../etc/passwd",
        "../secret.tif",
        "/etc/shadow",
        "nested/sub/raster.tif",
    ]
    for p in payloads:
        response = client.post("/api/spatial/dem/inspect", json={"relative_file_name": p})
        assert response.status_code == 422
        assert "Directory traversal" in response.json()["detail"]


def test_inspect_dem_blocks_invalid_extension():
    """Verify files without .tif or .tiff are rejected with HTTP 422."""
    response = client.post("/api/spatial/dem/inspect", json={"relative_file_name": "data_dump.csv"})
    assert response.status_code == 422
    assert "Invalid file extension" in response.json()["detail"]


def test_inspect_dem_missing_file_returns_404():
    """Verify non-existent raster file inside dem directory returns HTTP 404."""
    response = client.post("/api/spatial/dem/inspect", json={"relative_file_name": "non_existent_srtm.tif"})
    assert response.status_code == 404
    assert "does not exist" in response.json()["detail"]


def test_inspect_dem_valid_synthetic_fixture(tmp_path_factory):
    """
    Test DEM inspection by temporarily placing a synthetic fixture inside data/raw/spatial/dem/.
    Cleans up fixture after test to avoid polluting repository state.
    """
    repo_dem_dir = Path("data/raw/spatial/dem").resolve()
    repo_dem_dir.mkdir(parents=True, exist_ok=True)
    fixture_name = "_test_synthetic_fixture.tif"
    fixture_path = repo_dem_dir / fixture_name

    try:
        DEMValidator.create_synthetic_dem_fixture(
            output_path=fixture_path,
            width=30,
            height=30,
            crs_epsg=4326,
            west=77.0,
            south=28.5,
            east=77.5,
            north=29.0,
        )

        response = client.post("/api/spatial/dem/inspect", json={"relative_file_name": fixture_name})
        assert response.status_code == 200
        data = response.json()

        assert data["file_name"] == fixture_name
        assert data["dimensions"]["width"] == 30
        assert data["dimensions"]["height"] == 30
        assert data["crs_epsg"] == 4326
        assert data["intersects_study_area"] is True
        assert data["min_elevation_m"] is not None
        assert data["max_elevation_m"] is not None

    finally:
        if fixture_path.exists():
            fixture_path.unlink()


def test_get_terrain_summary():
    """Verify terrain/summary returns structured response with explicit caveats."""
    response = client.get("/api/spatial/terrain/summary")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] in ["AVAILABLE", "UNAVAILABLE"]
    assert "scientific_disclaimer" in data
    assert len(data["scientific_caveats"]) > 0
