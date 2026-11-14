"""
ml/tests/test_hydromet_coupling.py

Unit tests for PRAVAAH Phase 3E.2 Hydrometeorological Feature Coupling:
- Rolling 24h accumulation ending at 08:30 IST.
- Linear unweighted sums vs exponential API (Rule 4).
- Astronomical and seasonal calendar features.
- Discharge and inflow feature extraction.
- Hydromet coupling audit logic and telemetry absence detection.
- 23-feature schema assembly, allowlist ordering, and domain validation.
"""

import math
from datetime import date, datetime, timedelta, timezone
import pytest
import numpy as np

from ml.features.hydromet_adapter import (
    IST_TZ,
    Rolling24hAccumulator,
    HydrometAntecedentCalculator,
    AstronomicalCalendarCalculator,
    DischargeFeatureCalculator,
    HydrometCouplingAuditor,
    HydrometFeatureAdapter,
    TemporalAlignmentError,
    FeatureCompatibilityError,
)
from ml.training.train_discharge_models import OPERATIONAL_FEATURE_ALLOWLIST


# ==============================================================================
# 1. Temporal Alignment Tests (08:30 IST Reporting Window)
# ==============================================================================

def test_parse_iso_to_ist():
    """Verify ISO strings with UTC 'Z' or local offsets are accurately converted to IST."""
    # UTC 03:00Z -> IST 08:30
    utc_str = "2026-07-15T03:00:00Z"
    dt_ist = Rolling24hAccumulator.parse_iso_to_ist(utc_str)
    assert dt_ist.tzinfo == IST_TZ
    assert dt_ist.hour == 8
    assert dt_ist.minute == 30
    assert dt_ist.date() == date(2026, 7, 15)

    # Naive local string (as returned with timezone=Asia/Kolkata)
    local_str = "2026-07-15T08:30"
    dt_local = Rolling24hAccumulator.parse_iso_to_ist(local_str)
    assert dt_local.hour == 8
    assert dt_local.minute == 30


def test_reconstruct_0830_ist_daily_accumulation_complete():
    """Verify exact 24-hour summation between 08:30 IST (D-1) and 08:30 IST (D)."""
    target_d = date(2026, 7, 15)
    prev_d = target_d - timedelta(days=1)

    timestamps = []
    precip = []

    # Generate 48 hours covering D-1 and D (from D-1 00:00 to D 23:00)
    start_dt = datetime.combine(prev_d, datetime.min.time(), tzinfo=IST_TZ)
    for i in range(48):
        current_dt = start_dt + timedelta(hours=i)
        timestamps.append(current_dt.isoformat())
        precip.append(2.0)  # 2.0 mm per hour

    res = Rolling24hAccumulator.reconstruct_0830_ist_daily_accumulation(
        hourly_timestamps=timestamps,
        hourly_precipitation=precip,
        target_date_ist=target_d,
    )

    # Exactly 24 hours fall in (prev_d 08:30, target_d 08:30]
    assert res["is_complete_24h_window"] is True
    assert res["valid_hours_count"] == 24
    assert res["missing_hours_count"] == 0
    assert res["accumulation_24h_mm"] == 48.0  # 24 * 2.0 mm
    assert res["target_date_ist"] == "2026-07-15"


def test_reconstruct_0830_ist_daily_accumulation_detects_incomplete_series():
    """Verify missing hours are flagged and not silently filled with zeros."""
    target_d = date(2026, 7, 15)
    # Provide only 10 hours of observations
    timestamps = [
        (datetime.combine(target_d, datetime.min.time(), tzinfo=IST_TZ) + timedelta(hours=h)).isoformat()
        for h in range(10)
    ]
    precip = [1.5] * 10

    res = Rolling24hAccumulator.reconstruct_0830_ist_daily_accumulation(
        hourly_timestamps=timestamps,
        hourly_precipitation=precip,
        target_date_ist=target_d,
    )

    assert res["is_complete_24h_window"] is False
    assert res["valid_hours_count"] < 24
    assert res["missing_hours_count"] > 0


# ==============================================================================
# 2. Antecedent Features & Mathematical Inequality with API (Rule 4)
# ==============================================================================

def test_linear_unweighted_sums():
    """Verify linear accumulation sums match D-1, 3-day sum, 7-day sum, and max cell."""
    daily_history = [10.0, 20.0, 30.0, 5.0, 15.0, 25.0, 35.0, 40.0]

    sums = HydrometAntecedentCalculator.compute_unweighted_linear_accumulations(daily_history)

    assert sums["rainfall_mean_d_minus_1_mm"] == 10.0
    assert sums["rainfall_accum_3d_prior_mm"] == 60.0  # 10 + 20 + 30
    assert sums["rainfall_accum_7d_prior_mm"] == 140.0  # 10+20+30+5+15+25+35
    assert sums["rainfall_max_cell_3d_prior_mm"] == 30.0


def test_linear_sum_is_not_equal_to_exponential_api():
    """Rule 4: Explicitly prove linear sums != exponential API indices."""
    daily_history = [20.0, 20.0, 20.0, 20.0, 20.0, 20.0, 20.0]

    comparison = HydrometAntecedentCalculator.compare_linear_sum_vs_api(daily_history)

    assert comparison["are_features_equivalent"] is False
    assert comparison["linear_accum_3d_mm"] == 60.0
    # API-3 = 0.85*20 + 0.85^2*20 + 0.85^3*20 = 17.0 + 14.45 + 12.2825 = 43.73 mm
    assert comparison["exponential_api_3_mm"] < comparison["linear_accum_3d_mm"]
    assert comparison["discrepancy_3d_mm"] > 10.0
    assert comparison["linear_accum_7d_mm"] == 140.0
    assert comparison["exponential_api_7_mm"] < comparison["linear_accum_7d_mm"]


# ==============================================================================
# 3. Calendar & Astronomical Predictors
# ==============================================================================

def test_astronomical_calendar_features():
    """Verify astronomical and seasonal calendar transformations."""
    # July 15 (Monsoon)
    july_date = date(2026, 7, 15)
    cal_july = AstronomicalCalendarCalculator.compute_calendar_features(july_date)
    assert cal_july["month"] == 7.0
    assert cal_july["is_monsoon"] == 1.0
    assert -1.0 <= cal_july["sin_doy"] <= 1.0
    assert -1.0 <= cal_july["cos_doy"] <= 1.0

    # January 15 (Non-monsoon)
    jan_date = date(2026, 1, 15)
    cal_jan = AstronomicalCalendarCalculator.compute_calendar_features(jan_date)
    assert cal_jan["month"] == 1.0
    assert cal_jan["is_monsoon"] == 0.0


# ==============================================================================
# 4. Discharge Feature Calculator
# ==============================================================================

def test_discharge_feature_calculator():
    """Verify 13 discharge and inflow features computed from daily history."""
    # History [Q(t), Q(t-1), Q(t-2), Q(t-3), Q(t-4), Q(t-5), Q(t-6), Q(t-7)]
    q_history = [100.0, 80.0, 60.0, 40.0, 30.0, 20.0, 10.0, 5.0]
    q_inflow = 150.0

    df = DischargeFeatureCalculator.compute_discharge_features(
        discharge_history_cumecs=q_history,
        inflow_current_cumecs=q_inflow,
    )

    assert df["discharge_current_cumecs"] == 100.0
    assert df["discharge_lag_1d_cumecs"] == 80.0
    assert df["discharge_lag_2d_cumecs"] == 60.0
    assert df["discharge_lag_3d_cumecs"] == 40.0
    assert df["discharge_lag_7d_cumecs"] == 5.0
    assert df["discharge_delta_1d_cumecs"] == 20.0  # 100 - 80
    assert df["discharge_delta_ratio_1d"] == round(20.0 / 81.0, 4)
    assert df["discharge_rolling_mean_3d_cumecs"] == round((100 + 80 + 60) / 3.0, 2)
    assert df["inflow_current_cumecs"] == 150.0
    assert df["inflow_release_ratio_current"] == round(150.0 / 101.0, 4)


# ==============================================================================
# 5. Hydromet Coupling Auditor
# ==============================================================================

def test_coupling_auditor_reports_disconnected_when_telemetry_missing():
    """Verify coupling auditor blocks autonomous live operations when discharge telemetry is absent."""
    audit = HydrometCouplingAuditor.audit_coupling(
        has_live_discharge_telemetry=False,
        has_operator_discharge_inputs=False,
    )

    assert audit["coupling_status"] == "DISCONNECTED_FOR_AUTONOMOUS_OPERATIONS"
    assert audit["promoted_for_operational_disaster_warning"] is False
    assert len(audit["missing_inputs"]) >= 2
    assert any("telemetry" in m.lower() for m in audit["missing_inputs"])
    assert len(audit["covariate_shift_warnings"]) >= 3


def test_coupling_auditor_allows_research_when_operator_provides_discharge():
    """Verify coupling auditor permits research benchmark evaluation with operator inputs."""
    audit = HydrometCouplingAuditor.audit_coupling(
        has_live_discharge_telemetry=False,
        has_operator_discharge_inputs=True,
    )

    assert audit["coupling_status"] == "COUPLED_RESEARCH_BENCHMARK_ONLY"
    assert audit["promoted_for_operational_disaster_warning"] is False


# ==============================================================================
# 6. Hydromet Feature Adapter (Schema Validation & Allowlist Ordering)
# ==============================================================================

def test_feature_adapter_assembles_exact_23_feature_allowlist():
    """Verify feature adapter constructs the complete 23-feature vector in exact allowlist order."""
    adapter = HydrometFeatureAdapter()

    q_feats = {
        "discharge_current_cumecs": 50.0,
        "discharge_lag_1d_cumecs": 45.0,
        "discharge_lag_2d_cumecs": 40.0,
        "discharge_lag_3d_cumecs": 35.0,
        "discharge_lag_7d_cumecs": 30.0,
        "discharge_delta_1d_cumecs": 5.0,
        "discharge_delta_ratio_1d": 0.1,
        "discharge_rolling_mean_3d_cumecs": 45.0,
        "discharge_rolling_mean_7d_cumecs": 38.0,
        "discharge_rolling_max_7d_cumecs": 50.0,
        "discharge_rolling_std_7d_cumecs": 5.0,
        "inflow_current_cumecs": 60.0,
        "inflow_release_ratio_current": 1.2,
    }

    rf_feats = {
        "rainfall_mean_d_minus_1_mm": 5.0,
        "rainfall_max_cell_d_minus_1_mm": 15.0,
        "rainfall_accum_3d_prior_mm": 25.0,
        "rainfall_accum_7d_prior_mm": 55.0,
        "rainfall_max_cell_3d_prior_mm": 30.0,
    }

    cal_feats = {
        "day_of_year": 200.0,
        "month": 7.0,
        "sin_doy": -0.2,
        "cos_doy": -0.9,
        "is_monsoon": 1.0,
    }

    vec, meta = adapter.assemble_feature_vector(
        discharge_features=q_feats,
        rainfall_features=rf_feats,
        calendar_features=cal_feats,
    )

    assert len(vec) == 23
    assert list(vec.keys()) == OPERATIONAL_FEATURE_ALLOWLIST
    assert meta["total_feature_count"] == 23
    assert meta["complete_feature_count"] == 23
    assert meta["missing_feature_count"] == 0


def test_feature_adapter_rejects_negative_discharge_or_rainfall():
    """Verify adapter enforces physical constraints and rejects negative discharge/rainfall."""
    adapter = HydrometFeatureAdapter()

    invalid_q = {"discharge_current_cumecs": -25.0}  # Physically impossible

    with pytest.raises(FeatureCompatibilityError):
        adapter.assemble_feature_vector(
            discharge_features=invalid_q,
            rainfall_features={},
        )
