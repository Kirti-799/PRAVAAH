"""
ml/tests/test_river.py

Unit test suite for PRAVAAH River Network & Hydrography Engine (Phase 3B).
Tests vector ingestion, CRS enforcement, topology validation, UTM Zone 43N metric length
computation, spatial clipping, and repository scanning without relying on fabricated data.
"""

import tempfile
import json
import pytest
from pathlib import Path
import geopandas as gpd
from shapely.geometry import LineString, mapping

from ml.spatial.river import (
    RiverNetworkValidator,
    RiverValidationStatus,
    WaterwayType,
    RiverNetworkReport,
)
from ml.spatial.study_area import StudyAreaCatalog


def test_river_validator_synthetic_fixture():
    """
    Generate synthetic corridor-aligned river fixture and verify:
    - 3 features ingested (river, canal, drain)
    - Projected metric length in EPSG:32643 is strictly positive
    - Spatial bounds intersect the Yamuna study corridor
    - Categorization by waterway type is accurate
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir) / "synthetic_yamuna.geojson"
        RiverNetworkValidator.create_synthetic_river_fixture(
            output_path=tmp_path,
            crs_epsg=4326,
            corridor_aligned=True,
        )

        assert tmp_path.exists()
        report = RiverNetworkValidator.validate_file(tmp_path)

        assert report.total_features == 3
        assert report.valid_features_count == 3
        assert report.invalid_features_count == 0
        assert report.empty_features_count == 0

        # Total metric length should be ~400 km across main stem + canal + drain
        assert 350.0 <= report.total_length_km <= 450.0

        # Channel types
        assert "river" in report.features_by_type
        assert "canal" in report.features_by_type
        assert "drain" in report.features_by_type
        assert report.features_by_type["river"] == 1
        assert report.features_by_type["canal"] == 1
        assert report.features_by_type["drain"] == 1

        # Projected metric CRS
        assert report.projected_metric_crs == "EPSG:32643"
        assert "4326" in report.native_crs

        # Study area containment
        assert report.intersects_study_area is True
        assert report.study_area_containment_ratio == 1.0
        assert report.validation_status == RiverValidationStatus.VALID


def test_river_validator_load_features_geojson():
    """Verify conversion of vector river dataset into RFC 7946 GeoJSON FeatureCollection."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir) / "synthetic_yamuna.geojson"
        RiverNetworkValidator.create_synthetic_river_fixture(tmp_path)

        geojson_data = RiverNetworkValidator.load_features_geojson(tmp_path, clip_to_study_corridor=True)

        assert geojson_data["type"] == "FeatureCollection"
        assert len(geojson_data["features"]) == 3

        feat = geojson_data["features"][0]
        assert feat["type"] == "Feature"
        assert "geometry" in feat
        assert feat["geometry"]["type"] in ["LineString", "MultiLineString"]
        assert "properties" in feat
        assert "name" in feat["properties"]
        assert "waterway_type" in feat["properties"]
        assert feat["properties"]["length_km"] > 0.0


def test_river_validator_rejects_missing_file():
    """Verify missing file raises FileNotFoundError."""
    missing = Path("data/raw/spatial/hydrography/non_existent_river.geojson")
    with pytest.raises(FileNotFoundError):
        RiverNetworkValidator.validate_file(missing)


def test_river_validator_rejects_unsupported_format():
    """Verify non-vector or unsupported extensions raise ValueError."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        bad_file = Path(tmp_dir) / "invalid_format.txt"
        bad_file.write_text("not a geojson or shapefile", encoding="utf-8")
        with pytest.raises(ValueError, match="Unsupported format"):
            RiverNetworkValidator.validate_file(bad_file)


def test_river_validator_handles_empty_collection():
    """Verify empty vector dataset returns EMPTY status with warning."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        empty_file = Path(tmp_dir) / "empty.geojson"
        empty_fc = {"type": "FeatureCollection", "features": []}
        with open(empty_file, "w", encoding="utf-8") as f:
            json.dump(empty_fc, f)

        report = RiverNetworkValidator.validate_file(empty_file)
        assert report.validation_status == RiverValidationStatus.EMPTY
        assert report.total_features == 0
        assert report.total_length_km == 0.0
        assert any("zero features" in w for w in report.warnings)


def test_river_validator_out_of_bounds_detection():
    """Verify features outside the Yamuna corridor are flagged with warning."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        out_file = Path(tmp_dir) / "out_of_bounds.geojson"
        RiverNetworkValidator.create_synthetic_river_fixture(out_file, corridor_aligned=False)

        report = RiverNetworkValidator.validate_file(out_file)
        assert report.intersects_study_area is False
        assert report.study_area_containment_ratio == 0.0
        assert report.validation_status == RiverValidationStatus.VALID_WITH_WARNINGS
        assert any("do not intersect" in w for w in report.warnings)


def test_scan_repository_river_status_when_empty():
    """Verify scanning empty hydrography directory returns explicit UNAVAILABLE without error."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        fake_data_dir = Path(tmp_dir)
        status_res = RiverNetworkValidator.scan_repository_river_status(fake_data_dir)

        assert status_res["river_data_availability"] == "UNAVAILABLE"
        assert status_res["total_files_found"] == 0
        assert status_res["active_river_file"] is None
        assert status_res["validation_report"] is None
        assert "acquisition_guide" in status_res
        assert "strictly refuses to fabricate" in status_res["scientific_notice"]
