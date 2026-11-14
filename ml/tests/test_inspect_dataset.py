"""
ml/tests/test_inspect_dataset.py

Automated unit tests for DatasetInspector.
SAFETY WARNING:
All fixtures created in this test file are EXPLICITLY SYNTHETIC and TEMPORARY.
They exist purely to verify parser, statistical, and anomaly logic in DatasetInspector.
THEY DO NOT REPRESENT REAL-WORLD FLOOD, HYDROLOGICAL, OR METEOROLOGICAL OBSERVATIONS.
"""

import json
import pytest
from pathlib import Path
from ml.data_processing.inspect_dataset import DatasetInspector, inspect_file


@pytest.fixture
def synthetic_valid_csv(tmp_path: Path) -> Path:
    """Create a temporary synthetic CSV fixture."""
    file_path = tmp_path / "SYNTHETIC_FIXTURE_valid_data.csv"
    content = (
        "date,rainfall_mm,discharge_cumecs,station_code\n"
        "2023-07-01,12.5,450.0,TEST_01\n"
        "2023-07-02,0.0,420.5,TEST_01\n"
        "2023-07-03,85.2,1250.0,TEST_01\n"
        "2023-07-04,NA,1100.0,TEST_01\n"
        "2023-07-05,-999,980.2,TEST_01\n"
    )
    file_path.write_text(content, encoding="utf-8")
    return file_path


@pytest.fixture
def synthetic_anomaly_csv(tmp_path: Path) -> Path:
    """Create a temporary synthetic CSV fixture containing physical anomalies."""
    file_path = tmp_path / "SYNTHETIC_FIXTURE_anomalies.csv"
    content = (
        "record_date,rainfall_amount,river_discharge\n"
        "2023-07-01,-15.0,300.0\n"  # Negative rainfall anomaly
        "2023-07-02,10.0,-50.0\n"   # Negative discharge anomaly
        "2023-07-02,10.0,-50.0\n"   # Exact duplicate row
    )
    file_path.write_text(content, encoding="utf-8")
    return file_path


@pytest.fixture
def synthetic_geojson(tmp_path: Path) -> Path:
    """Create a temporary synthetic GeoJSON fixture."""
    file_path = tmp_path / "SYNTHETIC_FIXTURE_zones.geojson"
    geojson_data = {
        "type": "FeatureCollection",
        "crs": {
            "type": "name",
            "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}
        },
        "features": [
            {
                "type": "Feature",
                "properties": {"zone_id": "SYNTH_Z1"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [77.10, 28.50],
                            [77.30, 28.50],
                            [77.30, 28.70],
                            [77.10, 28.70],
                            [77.10, 28.50]
                        ]
                    ]
                }
            },
            {
                "type": "Feature",
                "properties": {"station_id": "SYNTH_S1"},
                "geometry": {
                    "type": "Point",
                    "coordinates": [77.25, 28.65]
                }
            }
        ]
    }
    file_path.write_text(json.dumps(geojson_data), encoding="utf-8")
    return file_path


@pytest.fixture
def empty_file(tmp_path: Path) -> Path:
    """Create an empty test file."""
    file_path = tmp_path / "SYNTHETIC_FIXTURE_empty.csv"
    file_path.write_text("", encoding="utf-8")
    return file_path


def test_inspector_valid_csv(synthetic_valid_csv: Path):
    """Verify inspection metrics on valid synthetic CSV."""
    report = inspect_file(synthetic_valid_csv)

    assert report["status"] == "success"
    assert report["file_format"] == "csv"
    assert report["num_rows"] == 5
    assert report["num_columns"] == 4
    assert report["duplicate_row_count"] == 0

    cols = report["column_summary"]
    # Check date column inference
    assert cols["date"]["inferred_type"] == "datetime"
    assert cols["date"]["null_count"] == 0

    # Check rainfall column null sentinels detection ('NA' and '-999')
    assert cols["rainfall_mm"]["inferred_type"] == "numeric"
    assert cols["rainfall_mm"]["null_count"] == 2
    assert cols["rainfall_mm"]["min"] == 0.0
    assert cols["rainfall_mm"]["max"] == 85.2

    # Check discharge column
    assert cols["discharge_cumecs"]["inferred_type"] == "numeric"
    assert cols["discharge_cumecs"]["null_count"] == 0


def test_inspector_detects_anomalies_and_duplicates(synthetic_anomaly_csv: Path):
    """Verify detection of negative physical quantities and duplicates."""
    report = inspect_file(synthetic_anomaly_csv)

    assert report["num_rows"] == 3
    assert report["duplicate_row_count"] == 1
    assert len(report["warnings"]) >= 2

    warning_text = " ".join(report["warnings"])
    assert "rainfall" in warning_text.lower()
    assert "negative" in warning_text.lower()
    assert "discharge" in warning_text.lower()


def test_inspector_geojson(synthetic_geojson: Path):
    """Verify inspection of spatial GeoJSON features and bounding box."""
    report = inspect_file(synthetic_geojson)

    assert report["status"] == "success"
    assert report["file_format"] == "geojson"
    assert report["num_features"] == 2
    assert report["geometry_type_counts"]["Polygon"] == 1
    assert report["geometry_type_counts"]["Point"] == 1

    bbox = report["bbox"]
    assert pytest.approx(bbox["min_lon_or_x"], rel=1e-3) == 77.10
    assert pytest.approx(bbox["max_lon_or_x"], rel=1e-3) == 77.30
    assert pytest.approx(bbox["min_lat_or_y"], rel=1e-3) == 28.50
    assert pytest.approx(bbox["max_lat_or_y"], rel=1e-3) == 28.70


def test_inspector_empty_file(empty_file: Path):
    """Verify graceful handling of 0-byte file."""
    report = inspect_file(empty_file)

    assert report["status"] == "warning"
    assert any("empty" in w.lower() for w in report["warnings"])


def test_inspector_file_not_found():
    """Verify FileNotFoundError for missing path."""
    with pytest.raises(FileNotFoundError):
        DatasetInspector("non_existent_file.csv")
