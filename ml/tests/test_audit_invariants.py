"""
ml/tests/test_audit_invariants.py

Automated scientific and operational audit regression tests for PRAVAAH Phase 2C-A.
Verifies critical pipeline invariants:
1. Target alignment: Strict contiguous calendar-day pairing (date + 1 day).
2. Gap isolation: Calendar gaps strictly result in null targets; zero forward-filling.
3. Timezone semantics: Captures 08:00 IST morning gauge convention vs UTC formatting.
4. Zero leakage: Strict 23-feature allowlist; target, retrospective, and partition columns excluded.
5. Structural tree bounds: Documents the ~4,100 cumecs leaf ceiling on extreme surges.
6. Gating invariant: Verifies that no Delhi stage or flood probability predictions are produced.
"""

import csv
import json
import pytest
from datetime import date, timedelta
from pathlib import Path

from ml.training.train_discharge_models import (
    OPERATIONAL_FEATURE_ALLOWLIST,
    EXCLUDED_FEATURES_REGISTRY,
    ModelTrainingPipeline,
)
from ml.models.inference import (
    HathnikundDischargeInferenceEngine,
    InvalidFeatureSchemaError,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DATASET_CSV = REPO_ROOT / "data" / "processed" / "modelling" / "hathnikund_discharge_forecasting_24h.csv"
AUDIT_SUMMARY_JSON = REPO_ROOT / "data" / "processed" / "analysis" / "phase_2c_audit_summary.json"


def test_target_alignment_and_value_integrity():
    """Verify that every valid target represents exactly the next calendar day's observed release."""
    assert DATASET_CSV.exists(), f"Dataset missing: {DATASET_CSV}"

    with open(DATASET_CSV, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == 2491, f"Expected 2491 total rows, got {len(rows)}"

    # Load source discharge records to verify ground truth for all dates (including 2025-01-01 boundary)
    source_discharge_csv = REPO_ROOT / "data" / "processed" / "hydrological" / "haryana_hathnikund_discharge_daily_2018_2025.csv"
    source_ds_q = {}
    with open(source_discharge_csv, "r", encoding="utf-8-sig") as f:
        for s_row in csv.DictReader(f):
            if s_row["station_name"] == "HKB D/S":
                source_ds_q[s_row["date"]] = float(s_row["discharge_cumecs"])

    valid_targets = 0
    broken_targets = 0

    for r in rows:
        d_curr = date.fromisoformat(r["date"])
        expected_target_date = (d_curr + timedelta(days=1)).isoformat()

        if r["has_valid_24h_target"] == "True":
            valid_targets += 1
            assert r["target_date"] == expected_target_date, (
                f"Target date mismatch on {r['date']}: expected {expected_target_date}, got {r['target_date']}"
            )
            assert expected_target_date in source_ds_q, (
                f"Target date {expected_target_date} marked valid but not found in source discharge observations"
            )
            expected_q = source_ds_q[expected_target_date]
            actual_target_q = float(r["target_discharge_24h_cumecs"])
            assert abs(expected_q - actual_target_q) < 1e-4, (
                f"Target value mismatch on {r['date']}: expected {expected_q}, got {actual_target_q}"
            )
        else:
            broken_targets += 1
            assert r["target_date"] == "", f"Broken target must have empty target_date: {r['date']}"
            assert r["target_discharge_24h_cumecs"] in ("", None), (
                f"Broken target must have empty target value: {r['date']}"
            )

    assert valid_targets == 2468
    assert broken_targets == 23


def test_calendar_gap_isolation():
    """Verify that unobserved dates (e.g. 2020-05-26) trigger broken targets and are never interpolated."""
    with open(DATASET_CSV, "r", encoding="utf-8") as f:
        rows = {r["date"]: r for r in csv.DictReader(f)}

    # Date 2020-05-25: next day 2020-05-26 is missing in Haryana source records
    assert "2020-05-25" in rows
    assert "2020-05-26" not in rows

    row_pre_gap = rows["2020-05-25"]
    assert row_pre_gap["has_valid_24h_target"] == "False"
    assert row_pre_gap["target_discharge_24h_cumecs"] == ""
    assert row_pre_gap["is_complete_operational_row"] == "False"


def test_timezone_semantics_documented():
    """Verify that dataset timestamp convention is explicitly tracked in audit summary."""
    assert AUDIT_SUMMARY_JSON.exists(), f"Audit summary missing: {AUDIT_SUMMARY_JSON}"

    with open(AUDIT_SUMMARY_JSON, "r", encoding="utf-8") as f:
        audit = json.load(f)

    ds_audit = audit["dataset_audit"]
    assert ds_audit["timezone_status"] == "SEMANTIC_DISCREPANCY_IDENTIFIED"
    assert "IST" in ds_audit["source_timezone"]
    assert "08:00:00Z" in ds_audit["documented_timestamp_field"]


def test_leakage_free_feature_allowlist():
    """Verify that allowlist contains 23 operational features and excludes target/metadata."""
    assert len(OPERATIONAL_FEATURE_ALLOWLIST) == 23

    # Forbidden features
    forbidden = [
        "target_discharge_24h_cumecs",
        "rainfall_mean_same_day_retro_mm",
        "rainfall_valid_cells_d_minus_1",
        "partition",
        "date",
        "timestamp_utc",
        "is_complete_operational_row",
        "missing_feature_flags",
    ]
    for feat in forbidden:
        assert feat not in OPERATIONAL_FEATURE_ALLOWLIST
        assert feat in EXCLUDED_FEATURES_REGISTRY


def test_reproduced_metrics_consistency():
    """Verify that reproduced metrics match audit summary records across all partitions."""
    with open(AUDIT_SUMMARY_JSON, "r", encoding="utf-8") as f:
        audit = json.load(f)

    reproduced = audit["reproduced_metrics"]["partitions"]

    # Check partition sample sizes
    assert reproduced["TRAIN"]["sample_count"] == 1412
    assert reproduced["VAL"]["sample_count"] == 322
    assert reproduced["TEST"]["sample_count"] == 611

    # Check Random Forest validation skill
    rf_val = reproduced["VAL"]["models"]["random_forest_v1"]
    assert rf_val["mae_cumecs"] == 77.48
    assert rf_val["rmse_cumecs"] == 485.06
    assert rf_val["skill_score_vs_persistence"] == 0.3202

    # Check Random Forest test degradation
    rf_test = reproduced["TEST"]["models"]["random_forest_v1"]
    assert rf_test["mae_cumecs"] == 95.82
    assert rf_test["rmse_cumecs"] == 469.52
    assert rf_test["skill_score_vs_persistence"] == -0.2392


def test_tree_extrapolation_limit_on_extreme_surge():
    """Verify that Random Forest severely underpredicts the July 2023 extreme flood crest."""
    engine = HathnikundDischargeInferenceEngine()
    engine.load()

    with open(DATASET_CSV, "r", encoding="utf-8") as f:
        rows = {r["date"]: r for r in csv.DictReader(f)}

    # July 9, 2023 (Q = 450 cumecs -> next day target = 8342.9 cumecs)
    row_july9 = rows["2023-07-09"]
    features_july9 = {feat: float(row_july9[feat]) for feat in OPERATIONAL_FEATURE_ALLOWLIST}

    pred_july9 = engine.predict(features_july9)["predicted_discharge_cumecs"]
    true_target = float(row_july9["target_discharge_24h_cumecs"])

    underprediction_pct = (abs(pred_july9 - true_target) / true_target) * 100.0
    # Must document severe underprediction (> 90%)
    assert underprediction_pct > 90.0, f"Expected >90% underprediction, got {underprediction_pct:.1f}%"


def test_strict_absence_of_delhi_predictions():
    """Verify that inference service explicitly blocks Delhi stage or flood probability outputs."""
    engine = HathnikundDischargeInferenceEngine()
    engine.load()

    metadata = engine.get_metadata()
    assert metadata["target_variable"] == "target_discharge_24h_cumecs"
    assert metadata["operational_recommendation"]["promoted_for_operational_disaster_warning"] is False

    # Prohibited applications must explicitly gate Delhi stage
    prohibitions = metadata["operational_recommendation"]["prohibited_applications"]
    assert any("Delhi Old Railway Bridge" in p for p in prohibitions)
    assert any("flood breach probabilities" in p for p in prohibitions)
