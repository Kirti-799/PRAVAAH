"""
ml/tests/test_target_importer.py

Unit tests for TargetGaugeImporter validating schema adherence, duplicate detection,
missing-value safety, and error handling using temporary synthetic fixtures.
"""

import tempfile
from pathlib import Path
import pytest

from ml.data_processing.import_target_gauge import (
    TargetGaugeImporter,
    SchemaValidationError,
)


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)


def test_import_valid_gauge_csv(temp_dir):
    csv_content = """timestamp_utc,station_id,station_name,water_level_m,unit
2023-07-10T08:00:00Z,028-MDD,Delhi Old Railway Bridge,204.60,m
2023-07-11T08:00:00Z,028-MDD,Delhi Old Railway Bridge,205.45,m
2023-07-12T08:00:00Z,028-MDD,Delhi Old Railway Bridge,207.25,m
2023-07-13T08:00:00Z,028-MDD,Delhi Old Railway Bridge,208.66,m
"""
    file_path = temp_dir / "valid_target.csv"
    file_path.write_text(csv_content, encoding="utf-8")

    importer = TargetGaugeImporter()
    records, summary = importer.import_from_csv(file_path)

    assert len(records) == 4
    assert summary["valid_observed_stages"] == 4
    assert summary["missing_observations_count"] == 0
    assert summary["duplicate_timestamps_count"] == 0
    assert summary["danger_breach_count"] == 3  # 205.45, 207.25, 208.66 >= 205.33
    assert summary["max_observed_stage_m"] == 208.66
    assert records[0]["is_danger_breached"] is False
    assert records[1]["is_danger_breached"] is True
    assert records[3]["water_level_m"] == 208.66


def test_missing_required_columns_raises_error(temp_dir):
    # Missing stage/water level column
    csv_content = """timestamp_utc,station_id,station_name
2023-07-10T08:00:00Z,028-MDD,Delhi Old Railway Bridge
"""
    file_path = temp_dir / "missing_stage.csv"
    file_path.write_text(csv_content, encoding="utf-8")

    importer = TargetGaugeImporter()
    with pytest.raises(SchemaValidationError) as exc_info:
        importer.import_from_csv(file_path)
    assert "Missing required stage/water level column" in str(exc_info.value)


def test_unparseable_timestamp_handling(temp_dir):
    csv_content = """timestamp,water_level_m
2023-07-10T08:00:00Z,204.10
NOT_A_TIMESTAMP,205.50
2023-07-12T08:00:00Z,206.00
"""
    file_path = temp_dir / "bad_timestamp.csv"
    file_path.write_text(csv_content, encoding="utf-8")

    importer = TargetGaugeImporter()
    records, summary = importer.import_from_csv(file_path)

    assert len(records) == 2  # Bad row excluded from records
    assert summary["unparseable_timestamps_count"] == 1
    assert len(summary["errors"]) >= 1


def test_duplicate_timestamps_detected(temp_dir):
    csv_content = """timestamp_utc,water_level_m
2023-07-10T08:00:00Z,204.10
2023-07-10T08:00:00Z,204.15
2023-07-11T08:00:00Z,204.80
"""
    file_path = temp_dir / "duplicate_ts.csv"
    file_path.write_text(csv_content, encoding="utf-8")

    importer = TargetGaugeImporter()
    records, summary = importer.import_from_csv(file_path)

    assert len(records) == 3
    assert summary["duplicate_timestamps_count"] == 1
    assert any("Duplicate timestamp" in w for w in summary["warnings"])


def test_missing_values_preserved_not_zeroed(temp_dir):
    csv_content = """timestamp_utc,water_level_m
2023-07-10T08:00:00Z,204.10
2023-07-11T08:00:00Z,-999.0
2023-07-12T08:00:00Z,
2023-07-13T08:00:00Z,NaN
2023-07-14T08:00:00Z,205.80
"""
    file_path = temp_dir / "missing_vals.csv"
    file_path.write_text(csv_content, encoding="utf-8")

    importer = TargetGaugeImporter()
    records, summary = importer.import_from_csv(file_path)

    assert len(records) == 5
    assert summary["missing_observations_count"] == 3
    assert summary["valid_observed_stages"] == 2

    # Check rows with missing values
    for row_idx in (1, 2, 3):
        assert records[row_idx]["water_level_m"] is None
        assert records[row_idx]["is_missing"] is True
        assert records[row_idx]["is_danger_breached"] is None  # CRITICAL: must NOT be False or 0!


def test_unexpected_unit_warning(temp_dir):
    csv_content = """timestamp_utc,water_level_m,unit
2023-07-10T08:00:00Z,670.5,feet
"""
    file_path = temp_dir / "feet_units.csv"
    file_path.write_text(csv_content, encoding="utf-8")

    importer = TargetGaugeImporter()
    records, summary = importer.import_from_csv(file_path)

    assert len(records) == 1
    assert records[0]["water_level_m"] == 670.5  # Not silently converted
    assert any("Unexpected unit" in w for w in summary["warnings"])
    assert summary["out_of_bounds_count"] == 1
