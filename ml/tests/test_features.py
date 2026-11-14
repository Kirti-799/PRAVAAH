"""
ml/tests/test_features.py

Automated test suite for PRAVAAH Feature Engineering & Dataset Generation.
Tests trailing rolling windows, lag calculations, missing day handling,
leakage defense, partition boundaries, and deterministic dataset generation.
Synthetic fixtures are strictly labeled as synthetic test fixtures.
"""

import pytest
import math
from datetime import date, timedelta
from ml.features.feature_pipeline import DischargeFeaturePipeline
from ml.features.feature_manifest import FEATURE_MANIFEST, get_feature_metadata_dict


# ==============================================================================
# 1. Pipeline Feature Extraction on Synthetic Fixture
# ==============================================================================

def test_feature_pipeline_trailing_windows_synthetic():
    """
    Test feature pipeline on an idealized synthetic series.
    Verifies that rolling windows use strictly trailing observations,
    lags match exact calendar offsets, and targets are correctly forward-shifted.
    """
    dates = [f"2021-07-{i:02d}" for i in range(1, 11)]  # 10 days
    # Synthetic discharge series
    synthetic_ds = {
        "2021-07-01": 100.0,
        "2021-07-02": 200.0,
        "2021-07-03": 300.0,
        "2021-07-04": 400.0,
        "2021-07-05": 500.0,
        "2021-07-06": 600.0,
        "2021-07-07": 700.0,
        "2021-07-08": 800.0,
        "2021-07-09": 900.0,
        "2021-07-10": 1000.0,
    }
    synthetic_rf = {
        d: {"mean": 10.0, "max": 25.0, "valid_cells": 91}
        for d in dates
    }

    pipeline = DischargeFeaturePipeline()
    rows, audit = pipeline.process_time_series(dates, synthetic_ds, rf_records=synthetic_rf)

    assert len(rows) == 10

    # Row 0: 2021-07-01
    r0 = rows[0]
    assert r0["discharge_current_cumecs"] == 100.0
    assert r0["discharge_lag_1d_cumecs"] is None  # Prior day 2021-06-30 is not in synthetic dict
    assert r0["discharge_rolling_mean_3d_cumecs"] is None
    assert r0["target_discharge_24h_cumecs"] == 200.0  # Next day 2021-07-02
    assert r0["has_valid_24h_target"] is True

    # Row 2: 2021-07-03
    r2 = rows[2]
    assert r2["discharge_current_cumecs"] == 300.0
    assert r2["discharge_lag_1d_cumecs"] == 200.0
    assert r2["discharge_lag_2d_cumecs"] == 100.0
    assert r2["discharge_delta_1d_cumecs"] == 100.0  # 300 - 200
    # Trailing 3-day mean: (300 + 200 + 100) / 3 = 200.0
    assert math.isclose(r2["discharge_rolling_mean_3d_cumecs"], 200.0, abs_tol=1e-4)

    # Row 6: 2021-07-07 (first row with 7 trailing days)
    r6 = rows[6]
    # Trailing 7-day window: 100, 200, 300, 400, 500, 600, 700 -> mean = 400.0
    assert math.isclose(r6["discharge_rolling_mean_7d_cumecs"], 400.0, abs_tol=1e-4)
    assert r6["discharge_rolling_max_7d_cumecs"] == 700.0

    # Row 9: 2021-07-10 (last row, no next day in synthetic series)
    r9 = rows[9]
    assert r9["target_discharge_24h_cumecs"] is None
    assert r9["has_valid_24h_target"] is False


def test_missing_calendar_day_broken_target():
    """
    Verify that if day D+1 is missing, day D does NOT get assigned a target from day D+2.
    Silent gap-skipping is strictly prevented.
    """
    dates = ["2021-07-01", "2021-07-03"]  # 2021-07-02 is missing!
    synthetic_ds = {
        "2021-07-01": 150.0,
        "2021-07-03": 250.0,
    }

    pipeline = DischargeFeaturePipeline()
    rows, audit = pipeline.process_time_series(dates, synthetic_ds)

    r0 = rows[0]  # 2021-07-01
    assert r0["target_discharge_24h_cumecs"] is None
    assert r0["has_valid_24h_target"] is False
    assert "target_discharge_24h_missing" in r0["missing_feature_flags"]

    r1 = rows[1]  # 2021-07-03
    # Lag 1 for 2021-07-03 is 2021-07-02, which is missing. Must NOT be 2021-07-01!
    assert r1["discharge_lag_1d_cumecs"] is None
    assert r1["discharge_lag_2d_cumecs"] == 150.0


def test_rainfall_antecedent_isolation():
    """
    Verify that rainfall predictors strictly use dates ending on or before D-1.
    Verify that same-day rainfall is isolated and tagged retrospective.
    """
    dates = ["2021-07-05"]
    synthetic_ds = {"2021-07-05": 300.0, "2021-07-06": 350.0}
    synthetic_rf = {
        "2021-07-01": {"mean": 5.0, "max": 10.0, "valid_cells": 91},
        "2021-07-02": {"mean": 10.0, "max": 20.0, "valid_cells": 91},
        "2021-07-03": {"mean": 15.0, "max": 30.0, "valid_cells": 91},
        "2021-07-04": {"mean": 20.0, "max": 40.0, "valid_cells": 91},  # D-1
        "2021-07-05": {"mean": 50.0, "max": 100.0, "valid_cells": 91}, # Day D
    }

    pipeline = DischargeFeaturePipeline()
    rows, _ = pipeline.process_time_series(dates, synthetic_ds, rf_records=synthetic_rf)

    r = rows[0]
    # D-1 rainfall must be 20.0, NOT 50.0
    assert r["rainfall_mean_d_minus_1_mm"] == 20.0
    assert r["rainfall_max_cell_d_minus_1_mm"] == 40.0
    # 3-day antecedent: D-3 (15.0) + D-2 (10.0) + D-1 (20.0) = 45.0
    assert r["rainfall_accum_3d_prior_mm"] == 45.0
    # Same-day retrospective rainfall
    assert r["rainfall_mean_same_day_retro_mm"] == 50.0


def test_partition_tagging():
    """Verify chronological partition boundaries."""
    pipeline = DischargeFeaturePipeline()
    test_dates = ["2018-05-10", "2021-12-31", "2022-01-01", "2022-12-31", "2023-01-01", "2024-07-15"]
    synthetic_ds = {d: 50.0 for d in test_dates}

    rows, _ = pipeline.process_time_series(test_dates, synthetic_ds)
    partitions = [r["partition"] for r in rows]

    assert partitions[0] == "TRAIN"  # 2018
    assert partitions[1] == "TRAIN"  # 2021
    assert partitions[2] == "VAL"    # 2022-01-01
    assert partitions[3] == "VAL"    # 2022-12-31
    assert partitions[4] == "TEST"   # 2023-01-01
    assert partitions[5] == "TEST"   # 2024-07-15


def test_feature_manifest_completeness():
    """Verify feature manifest defines all key schema fields without omission."""
    manifest = get_feature_metadata_dict()
    assert "target_discharge_24h_cumecs" in manifest
    assert "discharge_current_cumecs" in manifest
    assert "discharge_lag_1d_cumecs" in manifest
    assert "rainfall_accum_3d_prior_mm" in manifest
    assert "rainfall_mean_same_day_retro_mm" in manifest

    target_meta = manifest["target_discharge_24h_cumecs"]
    assert target_meta["classification"] == "TARGET"

    retro_meta = manifest["rainfall_mean_same_day_retro_mm"]
    assert retro_meta["classification"] == "RETROSPECTIVE_ANALYSIS_ONLY"
    assert "OPERATIONAL LEAKAGE RISK" in retro_meta["leakage_risk"]
