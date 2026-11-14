"""
ml/tests/test_schema_contract.py

Automated unit tests for ModellingDatasetContractValidator and split integrity.
SAFETY WARNING:
All fixtures created in this test file are EXPLICITLY SYNTHETIC and TEMPORARY.
They exist purely to test contract assertions, causality validation, and split integrity.
THEY DO NOT REPRESENT REAL-WORLD FLOOD, HYDROLOGICAL, OR METEOROLOGICAL OBSERVATIONS.
"""

import pytest
from datetime import datetime, timezone, timedelta
from ml.data_processing.schema_contract import ModellingDatasetContractValidator
from ml.data_processing.align_data import TemporalDataAligner


@pytest.fixture
def valid_synthetic_modelling_record():
    """Create a temporary valid synthetic modelling record."""
    return {
        "prediction_timestamp_utc": "2023-07-10T08:00:00Z",
        "upstream_station_name": "HKB U/S",
        "downstream_station_name": "Delhi Old Railway Bridge",
        "feature_upstream_discharge_cumecs_t": 8342.9,
        "feature_upstream_discharge_cumecs_t_minus_24h": 450.0,
        "feature_upstream_discharge_cumecs_t_minus_48h": 220.0,
        "feature_upstream_discharge_change_24h": 7892.9,
        "feature_catchment_rainfall_actual_mm_t": 85.4,
        "feature_local_stage_m_t": 204.63,
        "target_window_start_utc": "2023-07-11T08:00:00Z",
        "target_window_end_utc": "2023-07-12T08:00:00Z",
        "target_max_stage_m": 207.49,
        "target_danger_breach": 1,
        "is_target_observed": True,
        "lead_time_hours": 48,
        "prediction_window_hours": 24,
        "danger_threshold_m": 205.33,
        "data_source_upstream": "Haryana I&WRD",
        "data_source_downstream": "CWC 028-MDD",
    }


def test_validator_accepts_valid_record(valid_synthetic_modelling_record):
    """Verify that a compliant record passes validation with zero errors."""
    validator = ModellingDatasetContractValidator()
    errors = validator.validate_record(valid_synthetic_modelling_record)
    assert len(errors) == 0


def test_validator_detects_temporal_causality_violation(valid_synthetic_modelling_record):
    """Verify detection when prediction timestamp is after target window start."""
    bad_record = dict(valid_synthetic_modelling_record)
    # Leakage: prediction timestamp set AFTER target window start
    bad_record["prediction_timestamp_utc"] = "2023-07-12T12:00:00Z"

    validator = ModellingDatasetContractValidator()
    errors = validator.validate_record(bad_record)
    assert any("causality" in e.lower() for e in errors)


def test_validator_detects_unobserved_target_leakage(valid_synthetic_modelling_record):
    """Verify that if is_target_observed is False, target_danger_breach cannot be 0."""
    bad_record = dict(valid_synthetic_modelling_record)
    bad_record["is_target_observed"] = False
    bad_record["target_danger_breach"] = 0  # Should be None!

    validator = ModellingDatasetContractValidator()
    errors = validator.validate_record(bad_record)
    assert any("leakage" in e.lower() or "none" in e.lower() for e in errors)


def test_validator_detects_negative_physical_quantities(valid_synthetic_modelling_record):
    """Verify detection of negative discharge or rainfall."""
    bad_record = dict(valid_synthetic_modelling_record)
    bad_record["feature_upstream_discharge_cumecs_t"] = -100.0

    validator = ModellingDatasetContractValidator()
    errors = validator.validate_record(bad_record)
    assert any("non-negative" in e.lower() for e in errors)


def test_rainfall_cutoff_safeguard():
    """Verify that predictions made before 03:00 UTC (08:30 IST) do not leak date D rainfall."""
    aligner = TemporalDataAligner(lead_time_hours=48)
    
    # Prediction at 01:00 UTC on 2023-07-10 (which is 06:30 IST, before 08:30 IST cutoff)
    t_early = datetime(2023, 7, 10, 1, 0, tzinfo=timezone.utc)
    upstream = [{"timestamp_utc": t_early.isoformat(), "discharge_cumecs": 500.0}]
    downstream = [{"timestamp_utc": (t_early + timedelta(hours=48)).isoformat(), "stage_m": 204.0}]
    
    # Rainfall records for date D-1 (2023-07-09) and date D (2023-07-10)
    rainfall = [
        {"date": "2023-07-09", "rainfall_actual_mm": 12.0},
        {"date": "2023-07-10", "rainfall_actual_mm": 95.0},  # Not finished at 01:00 UTC!
    ]

    aligned, _ = aligner.align_series(upstream, downstream, rainfall)
    record = aligned[0]

    # Effective rainfall must be 12.0 (from 2023-07-09), NOT 95.0!
    assert record["feature_rainfall_actual_mm_t"] == 12.0
