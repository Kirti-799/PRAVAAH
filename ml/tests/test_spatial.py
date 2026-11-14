"""
ml/tests/test_spatial.py

Unit test suite for PRAVAAH Spatial Data Infrastructure & Terrain Engine.
Tests study area bounds, CRS validation, synthetic DEM inspection, slope analysis,
and repository scanning without relying on fabricated production rasters.
"""

import math
import tempfile
import pytest
from pathlib import Path

from ml.spatial.study_area import (
    StudyAreaCatalog,
    StudyAreaBounds,
    GeometryType,
    validate_spatial_bounds,
)
from ml.spatial.dem import (
    DEMValidator,
    DEMValidationStatus,
    DEMMetadataReport,
    TerrainSlopeSummary,
)
from ml.spatial.inventory import (
    SpatialInventoryCatalog,
    SpatialDataStatus,
    SpatialDatasetCategory,
)


# ==============================================================================
# 1. Study Area Bounds & CRS Contract Tests
# ==============================================================================

def test_authoritative_study_area_metadata():
    """Verify study area adheres to rectangular extent contract and CRS standards."""
    sa = StudyAreaCatalog.get_authoritative_study_area()
    assert sa.geometry_type == GeometryType.RECTANGULAR_EXTENT
    assert "EPSG:4326" in sa.geographic_crs
    assert "EPSG:32643" in sa.projected_crs
    assert sa.reach_length_km == 220.0

    # Verify bounds
    b = sa.bounds
    assert b.west_lon == 76.85
    assert b.south_lat == 28.50
    assert b.east_lon == 77.60
    assert b.north_lat == 30.40

    # Verify GeoJSON polygon format [lon, lat]
    geojson = sa.to_dict()["geojson"]
    assert geojson["type"] == "Polygon"
    ring = geojson["coordinates"][0]
    assert len(ring) == 5  # Closed 5-point ring
    assert ring[0] == ring[-1]  # First and last coordinates match

    # Verify explicit limitations
    assert any("RECTANGULAR BOUNDING EXTENT" in lim for lim in sa.scientific_limitations)
    assert any("NOT A VERIFIED WATERSHED" in lim for lim in sa.scientific_limitations)


def test_study_area_bounds_validation():
    """Verify coordinate bounds validator rejects reversed or out-of-range bounds."""
    # Valid bounds
    ok, err = validate_spatial_bounds(76.85, 28.50, 77.60, 30.40)
    assert ok is True
    assert err is None

    # Reversed longitude (west > east)
    ok, err = validate_spatial_bounds(78.0, 28.50, 76.0, 30.40)
    assert ok is False
    assert "Reversed longitudinal bounds" in err

    # Reversed latitude (south > north)
    ok, err = validate_spatial_bounds(76.85, 31.0, 77.60, 28.0)
    assert ok is False
    assert "Reversed latitudinal bounds" in err

    # Out of latitude range (> 90 deg)
    ok, err = validate_spatial_bounds(76.85, 28.50, 77.60, 95.0)
    assert ok is False
    assert "Invalid north_lat" in err


# ==============================================================================
# 2. Synthetic DEM Fixture & Validation Tests
# ==============================================================================

def test_dem_validator_synthetic_fixture():
    """
    Generate a miniature synthetic GeoTIFF fixture to test geodetic and numerical validation.
    Verifies dimensions, CRS, NoData masking, and elevation statistics.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir) / "synthetic_dem_fixture.tif"
        DEMValidator.create_synthetic_dem_fixture(
            output_path=tmp_path,
            width=40,
            height=40,
            crs_epsg=4326,
            west=77.0,
            south=28.5,
            east=77.5,
            north=29.0,
            nodata_val=-9999.0,
            with_nodata_patch=True,
        )

        assert tmp_path.exists()
        report = DEMValidator.validate_file(tmp_path)

        assert report.dimensions["width"] == 40
        assert report.dimensions["height"] == 40
        assert report.dimensions["bands"] == 1
        assert report.crs_epsg == 4326
        assert report.is_geographic is True
        assert report.nodata_value == -9999.0
        assert report.intersects_study_area is True

        # Total cells = 1600; 5x5 corner = 25 missing cells
        assert report.total_cells == 1600
        assert report.missing_cells == 25
        assert math.isclose(report.missing_cells_percentage, (25 / 1600) * 100, rel_tol=1e-2)
        assert report.has_non_finite_values is False

        # Elevation values: sloping ~205m to ~280m
        assert report.min_elevation_m is not None
        assert report.max_elevation_m is not None
        assert 200.0 <= report.min_elevation_m <= 215.0
        assert 270.0 <= report.max_elevation_m <= 285.0
        assert report.plausible_yamuna_range_check is True


def test_dem_validator_computes_slope():
    """Verify slope computation on synthetic DEM using metric scaling."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir) / "synthetic_slope_test.tif"
        DEMValidator.create_synthetic_dem_fixture(
            output_path=tmp_path,
            width=30,
            height=30,
            crs_epsg=4326,
            west=77.0,
            south=28.5,
            east=77.5,
            north=29.0,
            with_nodata_patch=False,
        )

        slope = DEMValidator.compute_slope(tmp_path)
        assert slope.min_slope_deg >= 0.0
        assert slope.max_slope_deg <= 90.0
        assert slope.mean_slope_deg > 0.0
        assert slope.horizontal_resolution_m > 1000.0  # Approx pixel size in meters
        assert slope.vertical_units == "meters"
        assert "Horn's" in slope.computation_method


def test_dem_validator_rejects_missing_file():
    """Verify missing file raises FileNotFoundError."""
    missing = Path("data/raw/spatial/dem/non_existent_file.tif")
    with pytest.raises(FileNotFoundError):
        DEMValidator.validate_file(missing)


# ==============================================================================
# 3. Spatial Inventory Catalog & Repository Scanning Tests
# ==============================================================================

def test_spatial_inventory_catalog_entries():
    """Verify standard candidate datasets are cataloged with UNAVAILABLE_IN_REPOSITORY status."""
    entries = SpatialInventoryCatalog.get_catalog()
    assert len(entries) >= 5

    ds_ids = [e.dataset_id for e in entries]
    assert "SRTM_30M_GLOBAL" in ds_ids
    assert "COPERNICUS_GLO30" in ds_ids
    assert "BHUVAN_CARTODEM_30M" in ds_ids
    assert "OSM_YAMUNA_HYDROGRAPHY" in ds_ids
    assert "DDA_O_ZONE_FLOODPLAIN" in ds_ids

    # Every uncommitted candidate must be explicitly UNAVAILABLE
    for e in entries:
        assert e.current_status == SpatialDataStatus.UNAVAILABLE_IN_REPOSITORY
        assert e.actual_local_path is None
        assert len(e.acquisition_blockers) > 0
        assert len(e.scientific_limitations) > 0


def test_scan_repository_dem_status_when_empty():
    """Verify scanning an empty directory returns explicit UNAVAILABLE status without error."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        fake_data_dir = Path(tmp_dir)
        status_res = SpatialInventoryCatalog.scan_repository_dem_status(fake_data_dir)

        assert status_res["dem_availability"] == "UNAVAILABLE"
        assert status_res["total_files_found"] == 0
        assert status_res["active_dem_file"] is None
        assert status_res["validation_report"] is None
        assert "acquisition_guide" in status_res
        assert "strictly refuses to fabricate" in status_res["scientific_notice"]
