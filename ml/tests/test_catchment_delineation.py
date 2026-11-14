"""
ml/tests/test_catchment_delineation.py

Comprehensive unit tests for PRAVAAH Phase 3D:
1. DEM Acquisition Catalog & Inventory Status.
2. Synthetic Multi-Tile Mosaicking & Terrain Processing.
3. D8 Flow Routing Engine (Flow Direction, Flow Accumulation, Upstream Tracing).
4. Pour-Point Specification & Stream Snapping.
5. Catchment Delineation, Morphometry & Hypsometry Metrics.
6. Drainage Network Extraction & Vectorization.
7. Catchment Spatial Rainfall Ingestion & Aggregation.
8. Antecedent Precipitation Indices (API-3, API-7, API-14) with exponential decay.

SCIENTIFIC INTEGRITY ENFORCEMENT:
Synthetic fixtures are strictly labeled as synthetic test matrices.
Never substitutes synthetic tests for real-world validation.
"""

import math
import tempfile
from pathlib import Path
import numpy as np
import pytest

from ml.spatial.dem_acquisition import (
    DEMAcquisitionManager,
    UPSTREAM_YAMUNA_COPERNICUS_TILES,
    DEMTileCatalogEntry,
)
from ml.spatial.dem import DEMValidator, DEMValidationStatus
from ml.spatial.catchment import (
    D8FlowEngine,
    PourPointSpecification,
    CatchmentDelineator,
    CatchmentMorphometryReport,
)
from ml.spatial.rainfall import (
    CatchmentGridPoint,
    CatchmentRainfallAggregator,
    CatchmentSpatialRainfallSummary,
)


# ==============================================================================
# 1. DEM Acquisition Catalog & Inventory Tests
# ==============================================================================

def test_dem_acquisition_catalog_integrity():
    """Verify Copernicus GLO-30 tile catalog accurately maps the Upper Yamuna basin."""
    mgr = DEMAcquisitionManager()
    catalog = mgr.get_catalog()
    assert len(catalog) == 4

    # Verify tile coverage covers 30°N to 32°N and 77°E to 79°E
    lats_min = min(t.lat_min for t in catalog.values())
    lats_max = max(t.lat_max for t in catalog.values())
    lons_min = min(t.lon_min for t in catalog.values())
    lons_max = max(t.lon_max for t in catalog.values())

    assert lats_min == 30.0
    assert lats_max == 32.0
    assert lons_min == 77.0
    assert lons_max == 79.0

    # Ensure Hathnikund outlet tile is cataloged
    assert "Copernicus_DSM_COG_10_N30_00_E077_00_DEM" in catalog
    assert "https://copernicus-dem-30m.s3.amazonaws.com" in catalog["Copernicus_DSM_COG_10_N30_00_E077_00_DEM"].url


def test_dem_inventory_status_reporting():
    """Verify inventory status dynamically reports acquired tile counts and coverage percentage."""
    mgr = DEMAcquisitionManager()
    inv = mgr.get_inventory_status()
    assert inv["dataset_name"] == "Copernicus DEM GLO-30 (Global 30m DSM)"
    assert inv["tiles_total_required"] == 4
    assert inv["tiles_acquired_count"] in [0, 1, 2, 3, 4]
    assert 0.0 <= inv["coverage_percentage"] <= 100.0


# ==============================================================================
# 2. Synthetic Mosaicking & Terrain Analysis Tests
# ==============================================================================

def test_synthetic_dem_mosaicking():
    """Verify DEMValidator.mosaic_tiles seamlessly combines adjacent synthetic GeoTIFFs."""
    import rasterio
    from rasterio.transform import from_origin
    from rasterio.crs import CRS

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        # Create two adjacent 10x10 synthetic tiles (Tile A: lon 77-78, Tile B: lon 78-79)
        tile_a_path = tmp_path / "tile_a.tif"
        tile_b_path = tmp_path / "tile_b.tif"
        out_mosaic_path = tmp_path / "mosaic.tif"

        data_a = np.full((10, 10), 300.0, dtype=np.float32)
        data_b = np.full((10, 10), 1200.0, dtype=np.float32)

        trans_a = from_origin(77.0, 31.0, 0.1, 0.1)
        trans_b = from_origin(78.0, 31.0, 0.1, 0.1)
        profile = {
            "driver": "GTiff",
            "height": 10,
            "width": 10,
            "count": 1,
            "dtype": "float32",
            "crs": CRS.from_epsg(4326),
            "nodata": -9999.0,
        }

        with rasterio.open(tile_a_path, "w", transform=trans_a, **profile) as dst_a:
            dst_a.write(data_a, 1)
        with rasterio.open(tile_b_path, "w", transform=trans_b, **profile) as dst_b:
            dst_b.write(data_b, 1)

        result_path = DEMValidator.mosaic_tiles([tile_a_path, tile_b_path], out_mosaic_path)
        assert result_path.exists()

        with rasterio.open(result_path) as m_src:
            assert m_src.count == 1
            assert m_src.width == 20
            assert m_src.height == 10
            mosaic_data = m_src.read(1)
            assert np.isclose(mosaic_data[0, 0], 300.0)
            assert np.isclose(mosaic_data[0, 15], 1200.0)


# ==============================================================================
# 3. D8 Flow Routing Engine Tests
# ==============================================================================

def test_d8_flow_direction_computation():
    """Verify D8 flow direction assigns correct steepest descent codes."""
    # Synthetic 5x5 V-shaped valley sloping towards center bottom (row 4, col 2)
    dem = np.array([
        [50, 40, 30, 40, 50],
        [45, 35, 25, 35, 45],
        [40, 30, 20, 30, 40],
        [35, 25, 15, 25, 35],
        [30, 20, 10, 20, 30],
    ], dtype=np.float32)

    flow_dir = D8FlowEngine.compute_flow_direction(dem, dx=100.0, dy=100.0)
    assert flow_dir.shape == (5, 5)

    # Top-center cell (0, 2, elev 30) drops directly South to (1, 2, elev 25)
    # Code 4 = South
    assert flow_dir[0, 2] == 4

    # Top-left cell (0, 0, elev 50) drops South-East to (1, 1, elev 35)
    # Code 2 = South-East
    assert flow_dir[0, 0] == 2

    # Top-right cell (0, 4, elev 50) drops South-West to (1, 3, elev 35)
    # Code 8 = South-West
    assert flow_dir[0, 4] == 8


def test_d8_flow_accumulation_computation():
    """Verify flow accumulation increases monotonically along downstream flow paths."""
    dem = np.array([
        [50, 40, 30, 40, 50],
        [45, 35, 25, 35, 45],
        [40, 30, 20, 30, 40],
        [35, 25, 15, 25, 35],
        [30, 20, 10, 20, 30],
    ], dtype=np.float32)

    flow_dir = D8FlowEngine.compute_flow_direction(dem, dx=100.0, dy=100.0)
    accum = D8FlowEngine.compute_flow_accumulation(flow_dir)

    # The valley floor column 2 should accumulate cells from both flanks
    assert accum[4, 2] > accum[3, 2]
    assert accum[3, 2] > accum[2, 2]
    # Outlet cell at valley bottom must have the highest accumulation
    assert accum[4, 2] == np.max(accum)


def test_d8_upstream_watershed_tracing():
    """Verify upstream watershed tracing correctly extracts all contributing cells."""
    dem = np.array([
        [50, 40, 30, 40, 50],
        [45, 35, 25, 35, 45],
        [40, 30, 20, 30, 40],
        [35, 25, 15, 25, 35],
        [30, 20, 10, 20, 30],
    ], dtype=np.float32)

    flow_dir = D8FlowEngine.compute_flow_direction(dem, dx=100.0, dy=100.0)
    # Trace upstream from outlet (4, 2)
    ws_mask = D8FlowEngine.trace_upstream_watershed(flow_dir, pour_row=4, pour_col=2)

    assert ws_mask.shape == (5, 5)
    assert bool(ws_mask[4, 2]) is True
    # The entire convergent valley should drain into the outlet
    assert np.sum(ws_mask) >= 15


# ==============================================================================
# 4. Pour-Point Specification & Snapping Tests
# ==============================================================================

def test_pour_point_specification():
    """Verify Hathnikund pour-point nominal coordinates and geodetic metadata."""
    spec = PourPointSpecification()
    assert spec.name == "Hathnikund Barrage (Yamuna Exit to Plains)"
    assert spec.latitude == 30.317
    assert spec.longitude == 77.585
    assert spec.elevation_approx_m == 295.0
    assert "CWC" in spec.provenance
    assert spec.snapping_radius_m > 1000.0


# ==============================================================================
# 5. Catchment Delineator & Morphometry Tests
# ==============================================================================

def test_catchment_delineator_authoritative_model():
    """Verify CatchmentDelineator produces validated morphometric report and GeoJSONs."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        delineator = CatchmentDelineator(output_dir=Path(tmp_dir))
        report, c_geo, d_geo = delineator._build_authoritative_catchment_model()

        assert report.catchment_id == "YAM_HATHNIKUND_UPSTREAM"
        assert report.area_sq_km == 11112.0
        assert report.elevation_min_m == 295.0
        assert report.elevation_max_m == 6387.0
        assert report.elevation_mean_m == 2180.0
        assert len(report.major_tributaries) >= 4
        assert "Tons River (~60%)" in report.major_tributaries

        # Verify GeoJSON structure
        assert c_geo["type"] == "FeatureCollection"
        assert len(c_geo["features"]) == 1
        feat = c_geo["features"][0]
        assert feat["geometry"]["type"] == "Polygon"
        assert feat["properties"]["drainage_area_sq_km"] == 11112.0

        # Verify drainage lines
        assert d_geo["type"] == "FeatureCollection"
        assert len(d_geo["features"]) == 5
        for d_f in d_geo["features"]:
            assert d_f["geometry"]["type"] == "LineString"


# ==============================================================================
# 6. Spatial Rainfall Aggregation & API Engine Tests
# ==============================================================================

def test_rainfall_aggregator_uniform_field():
    """Verify CatchmentRainfallAggregator computes exact spatial mean on uniform precipitation."""
    aggregator = CatchmentRainfallAggregator()
    points = [
        CatchmentGridPoint(
            point_id=f"pt_{i}",
            latitude=30.5 + i * 0.1,
            longitude=77.5 + i * 0.1,
            elevation_approx_m=1000.0 + i * 100.0,
            location_name=f"Station_{i}",
            is_inside_catchment=True,
            current_precipitation_mm=5.0,
            precipitation_forecast_24h_mm=25.0,
            precipitation_forecast_72h_mm=60.0,
            precipitation_forecast_168h_mm=100.0,
            daily_history_mm=[5.0] * 14,
        )
        for i in range(10)
    ]

    summary = aggregator.aggregate_catchment_rainfall(points)
    assert summary.catchment_id == "YAM_HATHNIKUND_UPSTREAM"
    assert summary.contributing_points_count == 10
    assert summary.spatial_coverage_percentage == 100.0
    assert summary.missing_data_percentage == 0.0

    assert np.isclose(summary.mean_precipitation_mm, 5.0)
    assert np.isclose(summary.min_precipitation_mm, 5.0)
    assert np.isclose(summary.max_precipitation_mm, 5.0)
    assert np.isclose(summary.std_precipitation_mm, 0.0)

    assert np.isclose(summary.accumulation_24h_mm, 25.0)
    assert np.isclose(summary.accumulation_72h_mm, 60.0)
    assert np.isclose(summary.accumulation_168h_mm, 100.0)


def test_antecedent_precipitation_index_decay():
    """
    Verify API calculation: API_N = sum_{i=1}^N (k^i * P_{t-i}) with k=0.85.
    Verifies that API monotonically increases with window length (API-3 <= API-7 <= API-14).
    """
    aggregator = CatchmentRainfallAggregator()

    # 10 mm rain each day for 14 days
    daily_history = [10.0] * 14
    point = CatchmentGridPoint(
        point_id="pt_test",
        latitude=30.5,
        longitude=77.5,
        elevation_approx_m=1200.0,
        location_name="Test Gauge",
        current_precipitation_mm=2.0,
        daily_history_mm=daily_history,
    )

    summary = aggregator.aggregate_catchment_rainfall([point])
    api3 = summary.api_3_day_mm
    api7 = summary.api_7_day_mm
    api14 = summary.api_14_day_mm

    # Expected analytical API values:
    # API-3 = 10 * (0.85^1 + 0.85^2 + 0.85^3) = 10 * (0.85 + 0.7225 + 0.614125) = 21.866 mm
    expected_api3 = 10.0 * (0.85 + 0.85**2 + 0.85**3)
    assert np.isclose(api3, round(expected_api3, 2), atol=0.1)

    # Strict monotonicity check: older rain contributes positively to longer indices
    assert api3 < api7
    assert api7 < api14


def test_rainfall_missing_data_handling():
    """Verify CatchmentRainfallAggregator rejects empty inputs and handles missing nodes cleanly."""
    aggregator = CatchmentRainfallAggregator()
    with pytest.raises(ValueError, match="No grid points found"):
        aggregator.aggregate_catchment_rainfall([])

    # Points with zero or outside catchment
    pt_outside = CatchmentGridPoint(
        point_id="pt_out",
        latitude=28.0,
        longitude=76.0,
        elevation_approx_m=200.0,
        location_name="Outside Basin",
        is_inside_catchment=False,
    )
    pt_inside = CatchmentGridPoint(
        point_id="pt_in",
        latitude=30.8,
        longitude=77.8,
        elevation_approx_m=1800.0,
        location_name="Inside Basin",
        is_inside_catchment=True,
        current_precipitation_mm=4.0,
    )

    summary = aggregator.aggregate_catchment_rainfall([pt_outside, pt_inside])
    assert summary.contributing_points_count == 1
    assert summary.mean_precipitation_mm == 4.0
    assert summary.spatial_coverage_percentage == 50.0
