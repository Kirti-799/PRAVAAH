"""
backend/tests/test_catchment_rainfall.py

Automated integration tests for PRAVAAH Catchment & Spatial Rainfall API Endpoints:
- GET /api/spatial/catchment/status: Infrastructure status & acquired DEM tile count.
- GET /api/spatial/catchment/summary: Catchment area, perimeter, elevation relief & hypsometry.
- GET /api/spatial/catchment/geometry: GeoJSON FeatureCollection of watershed boundary.
- GET /api/spatial/catchment/drainage: GeoJSON FeatureCollection of stream network.
- GET /api/rainfall/status: Multi-point provider connectivity and sampling grid health.
- GET /api/rainfall/catchment/current: Spatially distributed current precipitation rates.
- GET /api/rainfall/catchment/forecast: Multi-horizon (24h, 72h, 168h) accumulations.
- GET /api/rainfall/catchment/history: Antecedent Precipitation Indices (API-3, API-7, API-14).
- GET /api/rainfall/catchment/summary: Comprehensive spatial rainfall synthesis.

SCIENTIFIC INTEGRITY VERIFICATION:
- Rejects unverified operational claims.
- Validates data provenance, spatial bounds, and unit normalization.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.integrations.rainfall.base import RainfallProviderAvailability
from app.integrations.rainfall.open_meteo import OpenMeteoCatchmentRainfallAdapter
from app.integrations.rainfall.imd import IMDRainfallAdapter
from app.integrations.rainfall.nasa_gpm import NASAGPMAdapter
from app.services.rainfall_service import rainfall_service
from ml.spatial.rainfall import CatchmentGridPoint

client = TestClient(app)


# ==============================================================================
# 1. Catchment Infrastructure Endpoints
# ==============================================================================

def test_catchment_status_endpoint():
    """Verify GET /api/spatial/catchment/status returns complete status with 4 acquired DEM tiles."""
    response = client.get("/api/spatial/catchment/status")
    assert response.status_code == 200
    data = response.json()

    assert data["service"] == "PRAVAAH Catchment Delineation Infrastructure"
    assert data["delineation_status"] == "DELINEATED"
    assert data["area_sq_km"] == 11112.0
    assert "Hathnikund" in data["pour_point_name"]
    assert data["pour_point_lat"] == 30.317
    assert data["pour_point_lon"] == 77.585
    assert data["raw_dem_tiles_acquired"] == 4
    assert data["raw_dem_tiles_required"] == 4
    assert data["has_drainage_network"] is True
    assert "11,112 km²" in data["scientific_integrity_note"]


def test_catchment_summary_endpoint():
    """Verify GET /api/spatial/catchment/summary returns morphometry, hypsometry and scientific caveats."""
    response = client.get("/api/spatial/catchment/summary")
    assert response.status_code == 200
    data = response.json()

    assert data["catchment_id"] == "YAM_HATHNIKUND_UPSTREAM"
    assert data["area_sq_km"] == 11112.0
    assert data["perimeter_km"] > 500.0
    assert data["elevation_min_m"] >= 250.0
    assert data["elevation_max_m"] >= 6000.0  # Bandarpunch / Yamunotri high peaks
    assert data["elevation_mean_m"] > 1800.0

    # Hypsometric percentiles
    hyps = data["hypsometry_percentiles"]
    assert "p10" in hyps and "p50" in hyps and "p90" in hyps
    assert hyps["p10"] < hyps["p50"] < hyps["p90"]

    # Pour point info
    pour = data["pour_point"]
    assert pour["name"] == "Hathnikund Barrage (Yamuna Exit to Plains)"
    assert len(pour["nominal_coordinates"]) == 2
    assert "CWC" in pour["provenance"]

    # Major tributaries
    tribs = data["major_tributaries"]
    assert any("Tons" in t for t in tribs)
    assert any("Giri" in t for t in tribs)


def test_catchment_geometry_geojson():
    """Verify GET /api/spatial/catchment/geometry returns valid RFC 7946 Polygon GeoJSON."""
    response = client.get("/api/spatial/catchment/geometry")
    assert response.status_code == 200
    data = response.json()

    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) >= 1
    feature = data["features"][0]
    assert feature["geometry"]["type"] in ["Polygon", "MultiPolygon"]
    assert feature["properties"]["pour_point"] == "Hathnikund Barrage"

    # Coordinates must be valid geographic bounds [lon, lat]
    coords = feature["geometry"]["coordinates"][0]
    for pt in coords:
        lon, lat = pt[0], pt[1]
        assert 76.5 <= lon <= 79.5
        assert 29.8 <= lat <= 32.5


def test_catchment_drainage_geojson():
    """Verify GET /api/spatial/catchment/drainage returns contributing streams as LineString GeoJSON."""
    response = client.get("/api/spatial/catchment/drainage")
    assert response.status_code == 200
    data = response.json()

    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) >= 4
    for feat in data["features"]:
        assert feat["geometry"]["type"] == "LineString"
        coords = feat["geometry"]["coordinates"]
        assert len(coords) >= 2


# ==============================================================================
# 2. Spatial Rainfall & API Endpoints
# ==============================================================================

def test_rainfall_status_endpoint():
    """Verify GET /api/rainfall/status returns provider health and grid sampling status."""
    response = client.get("/api/rainfall/status")
    assert response.status_code == 200
    data = response.json()

    assert data["provider_name"] == "open_meteo_catchment"
    assert data["spatial_sampling_nodes_count"] == 20
    assert data["active_aggregation_window_hours"] == [24, 72, 168]
    assert data["catchment_bounding_box"]["south"] == 30.30
    assert data["catchment_bounding_box"]["north"] == 31.45
    assert len(data["notes"]) >= 3


def test_rainfall_catchment_summary_endpoint():
    """Verify GET /api/rainfall/catchment/summary aggregates multi-node precipitation and API metrics."""
    response = client.get("/api/rainfall/catchment/summary")
    assert response.status_code == 200
    data = response.json()

    assert data["catchment_id"] == "YAM_HATHNIKUND_UPSTREAM"
    assert data["contributing_points_count"] == 20
    assert data["spatial_coverage_percentage"] == 100.0

    # Rate summary
    rate = data["current_rate"]
    assert "mean_mm" in rate
    assert rate["mean_mm"] >= 0.0

    # Accumulation summary
    acc = data["accumulations"]
    assert "acc_24h_mm" in acc and "acc_72h_mm" in acc and "acc_168h_mm" in acc
    assert acc["acc_24h_mm"] >= 0.0

    # Antecedent indices
    api = data["antecedent_indices"]
    assert "api_3_mm" in api and "api_7_mm" in api and "api_14_mm" in api
    assert api["decay_factor_k"] == 0.85

    # Check 20 grid nodes
    nodes = data["sample_grid_points"]
    assert len(nodes) == 20
    for node in nodes:
        assert node["latitude"] > 30.0
        assert node["longitude"] > 77.0
        assert node["elevation_m"] > 250.0


def test_rainfall_catchment_current_endpoint():
    """Verify GET /api/rainfall/catchment/current returns current rates across nodes."""
    response = client.get("/api/rainfall/catchment/current")
    assert response.status_code == 200
    data = response.json()

    assert "current_rate" in data
    assert "sample_grid_points" in data
    assert len(data["sample_grid_points"]) == 20


def test_rainfall_catchment_forecast_endpoint():
    """Verify GET /api/rainfall/catchment/forecast returns accumulations."""
    response = client.get("/api/rainfall/catchment/forecast")
    assert response.status_code == 200
    data = response.json()

    assert "accumulations" in data
    assert data["accumulations"]["acc_24h_mm"] >= 0.0
    assert data["accumulations"]["acc_72h_mm"] >= 0.0
    assert data["accumulations"]["acc_168h_mm"] >= 0.0


def test_rainfall_catchment_history_endpoint():
    """Verify GET /api/rainfall/catchment/history returns API-3, API-7, and API-14."""
    response = client.get("/api/rainfall/catchment/history")
    assert response.status_code == 200
    data = response.json()

    assert "antecedent_indices" in data
    assert data["decay_coefficient_k"] == 0.85
    assert "api_3_mm" in data["antecedent_indices"]
    assert "api_7_mm" in data["antecedent_indices"]
    assert "api_14_mm" in data["antecedent_indices"]


# ==============================================================================
# 3. Provider Adapters & Provenance Contracts
# ==============================================================================

def test_imd_adapter_provenance_and_offline_guardrail():
    """Verify IMDRainfallAdapter documents 0.25° resolution and OFFLINE_ARCHIVE_ONLY status."""
    adapter = IMDRainfallAdapter()
    prov = adapter.provenance

    assert prov.source_name == "India Meteorological Department (IMD)"
    assert "0.25°" in prov.spatial_resolution
    assert prov.temporal_resolution == "Daily (08:30 IST to 08:30 IST accumulation)"
    assert prov.observation_or_forecast == "OBSERVATION"
    assert prov.availability_status == RainfallProviderAvailability.OFFLINE_ARCHIVE_ONLY
    assert "IMD does not offer an open real-time streaming REST API" in prov.access_constraints_or_blockers


def test_nasa_gpm_adapter_provenance_and_auth_guardrail():
    """Verify NASAGPMAdapter documents GPM IMERG Early Run and Earthdata authentication constraint."""
    adapter = NASAGPMAdapter()
    prov = adapter.provenance

    assert "NASA" in prov.source_name
    assert "GPM IMERG" in prov.product_name
    assert "0.1°" in prov.spatial_resolution
    assert "30 minutes" in prov.temporal_resolution
    assert prov.observation_or_forecast == "OBSERVATION"
    assert prov.availability_status == RainfallProviderAvailability.REQUIRES_AUTHENTICATION
    assert "NASA Earthdata Login" in prov.access_constraints_or_blockers

