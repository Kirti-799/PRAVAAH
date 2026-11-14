"""
ml/tests/test_assemble_dataset.py

Unit tests for DatasetAssembler and IMDGriddedRainfallExtractor verifying:
- Temporal causality and target separation
- IMD 08:30 IST / 03:00 UTC observation cut-off gating
- Target missingness handling (no negative class conversion for unobserved windows)
- Gridded rainfall bounding box coordinates and extraction
- ModellingDatasetContractValidator enforcement
"""

import tempfile
import struct
from pathlib import Path
from datetime import date, timedelta
import pytest

from ml.data_processing.assemble_dataset import DatasetAssembler
from ml.data_processing.extract_gridded_rainfall import IMDGriddedRainfallExtractor
from ml.data_processing.schema_contract import ModellingDatasetContractValidator


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)


def test_gridded_rainfall_extractor_coordinates():
    extractor = IMDGriddedRainfallExtractor(
        min_lat=28.0,
        max_lat=31.0,
        min_lon=76.5,
        max_lon=78.0,
    )
    # Lat: (31.0 - 28.0)/0.25 + 1 = 13
    # Lon: (78.0 - 76.5)/0.25 + 1 = 7
    # Total: 13 * 7 = 91
    assert extractor.total_bbox_cells == 91
    assert extractor.lat_start_idx == 86
    assert extractor.lat_end_idx == 98
    assert extractor.lon_start_idx == 40
    assert extractor.lon_end_idx == 46

    # Verify first and last cell coordinates
    assert extractor.cell_metadata[0]["latitude"] == 28.0
    assert extractor.cell_metadata[0]["longitude"] == 76.5
    assert extractor.cell_metadata[-1]["latitude"] == 31.0
    assert extractor.cell_metadata[-1]["longitude"] == 78.0


def test_gridded_rainfall_extraction_synthetic_file(temp_dir):
    extractor = IMDGriddedRainfallExtractor()
    year = 2021  # Non-leap year: 365 days
    n_days = 365
    floats_per_day = 129 * 135
    total_floats = n_days * floats_per_day

    # Create synthetic binary file with known rainfall on day 10
    synth_path = temp_dir / "ind2021_rfp25.grd"
    # Fill with missing sentinel -999.0
    day_slice = [-999.0] * floats_per_day

    # On day 10, set specific cells in bounding box to 45.0 mm
    # lat_idx 90 (29.0N), lon_idx 42 (77.0E)
    day_slice[90 * 135 + 42] = 45.0
    day_slice[95 * 135 + 44] = 25.0

    # Pack into binary
    packed_empty = struct.pack(f"<{floats_per_day}f", *([-999.0] * floats_per_day))
    packed_day10 = struct.pack(f"<{floats_per_day}f", *day_slice)

    with open(synth_path, "wb") as f:
        for d in range(n_days):
            if d == 9:  # Day 10 (0-indexed 9)
                f.write(packed_day10)
            else:
                f.write(packed_empty)

    cell_records, summary_records = extractor.extract_year(synth_path, year)
    assert len(summary_records) == 365
    assert len(cell_records) == 365 * 91

    # On empty day (day 1)
    assert summary_records[0]["valid_cells_count"] == 0
    assert summary_records[0]["rainfall_spatial_mean_mm"] is None

    # On day 10
    day10_summary = summary_records[9]
    assert day10_summary["valid_cells_count"] == 2
    assert day10_summary["rainfall_spatial_max_mm"] == 45.0
    assert day10_summary["rainfall_spatial_min_mm"] == 25.0
    assert day10_summary["rainfall_spatial_mean_mm"] == 35.0


def test_dataset_assembler_missing_target_no_leakage():
    assembler = DatasetAssembler(lead_time_hours=48, prediction_window_hours=24)

    upstream = [
        {"timestamp_utc": "2023-07-08T08:00:00Z", "discharge_cumecs": 1200.0, "role": "downstream_release"},
        {"timestamp_utc": "2023-07-09T08:00:00Z", "discharge_cumecs": 3500.0, "role": "downstream_release"},
        {"timestamp_utc": "2023-07-10T08:00:00Z", "discharge_cumecs": 8343.0, "role": "downstream_release"},
    ]
    rainfall = [
        {"date": "2023-07-08", "rainfall_spatial_mean_mm": 15.0},
        {"date": "2023-07-09", "rainfall_spatial_mean_mm": 59.7},
        {"date": "2023-07-10", "rainfall_spatial_mean_mm": 65.5},
    ]

    # No downstream target data provided (simulating current production state)
    records, summary = assembler.assemble(upstream, rainfall, downstream_records=None)

    assert len(records) == 3
    assert summary["observed_target_windows"] == 0
    assert summary["unobserved_target_windows"] == 3
    assert summary["dataset_readiness_status"] == "INCOMPLETE_PENDING_TARGET_GROUND_TRUTH"
    assert summary["is_ready_for_ml_training"] is False
    assert summary["contract_validation_errors_count"] == 0

    # Ensure unobserved windows are NOT marked 0
    for r in records:
        assert r["is_target_observed"] is False
        assert r["target_danger_breach"] is None
        assert r["target_max_stage_m"] is None


def test_dataset_assembler_observed_target_and_breach():
    assembler = DatasetAssembler(lead_time_hours=48, prediction_window_hours=24, danger_threshold_m=205.33)

    upstream = [
        {"timestamp_utc": "2023-07-10T08:00:00Z", "discharge_cumecs": 8343.0, "role": "downstream_release"},
    ]
    rainfall = [
        {"date": "2023-07-10", "rainfall_spatial_mean_mm": 65.5},
    ]
    # Downstream observations: prediction at 2023-07-10 08:00 UTC
    # Forward target window: [t+24h, t+48h] -> 2023-07-11 08:00 UTC to 2023-07-12 08:00 UTC
    downstream = [
        {"timestamp_utc": "2023-07-11T12:00:00Z", "water_level_m": 205.80},  # In window, breach!
        {"timestamp_utc": "2023-07-12T04:00:00Z", "water_level_m": 206.50},  # In window, breach!
    ]

    records, summary = assembler.assemble(upstream, rainfall, downstream)
    assert len(records) == 1
    r = records[0]

    assert r["is_target_observed"] is True
    assert r["target_max_stage_m"] == 206.50
    assert r["target_danger_breach"] == 1
    assert summary["positive_danger_breaches"] == 1
    assert summary["dataset_readiness_status"] == "READY_FOR_SUPERVISED_TRAINING"
    assert summary["is_ready_for_ml_training"] is True


def test_rainfall_gating_at_0830_ist():
    assembler = DatasetAssembler()

    # Prediction issued at 02:00 UTC (07:30 IST) -> before 08:30 IST cut-off
    upstream_early = [
        {"timestamp_utc": "2023-07-10T02:00:00Z", "discharge_cumecs": 2000.0, "role": "downstream_release"}
    ]
    # Prediction issued at 04:00 UTC (09:30 IST) -> after 08:30 IST cut-off
    upstream_late = [
        {"timestamp_utc": "2023-07-10T04:00:00Z", "discharge_cumecs": 2500.0, "role": "downstream_release"}
    ]
    rainfall = [
        {"date": "2023-07-09", "rainfall_spatial_mean_mm": 25.0},
        {"date": "2023-07-10", "rainfall_spatial_mean_mm": 80.0},
    ]

    records_early, _ = assembler.assemble(upstream_early, rainfall)
    records_late, _ = assembler.assemble(upstream_late, rainfall)

    # Early record should receive July 9 rainfall (25.0)
    assert records_early[0]["feature_catchment_rainfall_actual_mm_t"] == 25.0

    # Late record should receive July 10 rainfall (80.0)
    assert records_late[0]["feature_catchment_rainfall_actual_mm_t"] == 80.0
