"""
ml/tests/test_align_data.py

Automated unit tests for TemporalDataAligner.
SAFETY WARNING:
All fixtures created in this test file are EXPLICITLY SYNTHETIC and TEMPORARY.
They exist purely to verify alignment mathematics, lag calculations, and leakage prevention.
THEY DO NOT REPRESENT REAL-WORLD FLOOD, HYDROLOGICAL, OR METEOROLOGICAL OBSERVATIONS.
"""

import pytest
from datetime import datetime, timezone, timedelta
from ml.data_processing.align_data import TemporalDataAligner


@pytest.fixture
def synthetic_series():
    """Create a temporary synthetic upstream and downstream daily time series."""
    base_t = datetime(2023, 7, 1, 8, 0, tzinfo=timezone.utc)
    
    # Upstream records: day 1 to day 10
    upstream = []
    for day in range(10):
        t = base_t + timedelta(days=day)
        # Surge on day 3 and 4
        q = 8000.0 if day in (3, 4) else 150.0
        upstream.append({
            "timestamp_utc": t.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "discharge_cumecs": q,
            "station_name": "SYNTH_UPSTREAM_BAR",
        })

    # Downstream records: day 1 to day 10
    downstream = []
    for day in range(10):
        t = base_t + timedelta(days=day)
        # Flood crest on day 5 and 6 (2-day lag after day 3 surge)
        stage = 206.5 if day in (5, 6) else 203.0
        downstream.append({
            "timestamp_utc": t.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "stage_m": stage,
            "station_name": "SYNTH_DOWNSTREAM_ORB",
        })

    return upstream, downstream


def test_aligner_couples_with_lead_time(synthetic_series):
    """Verify that upstream t is coupled to downstream [t+24, t+48]."""
    upstream, downstream = synthetic_series
    aligner = TemporalDataAligner(
        lead_time_hours=48,
        prediction_window_hours=24,
        danger_threshold_m=205.33
    )

    aligned, summary = aligner.align_series(upstream, downstream)

    assert summary["total_aligned_records"] == 10
    # Day 3 (surge at upstream) should predict the downstream breach on day 5
    day_3_record = aligned[3]
    assert day_3_record["feature_discharge_cumecs_t"] == 8000.0
    assert day_3_record["target_danger_breach"] == 1
    assert day_3_record["target_max_stage_m"] == 206.5

    # Day 0 should have normal downstream flow
    day_0_record = aligned[0]
    assert day_0_record["feature_discharge_cumecs_t"] == 150.0
    assert day_0_record["target_danger_breach"] == 0
    assert day_0_record["target_max_stage_m"] == 203.0


def test_aligner_prevents_future_leakage(synthetic_series):
    """Verify that features at time t contain strictly information from <= t."""
    upstream, downstream = synthetic_series
    aligner = TemporalDataAligner(lead_time_hours=48)
    aligned, _ = aligner.align_series(upstream, downstream)

    # For day 1, lag 24h should match day 0, and lag 48h should be None (not yet observed)
    day_1 = aligned[1]
    assert day_1["feature_discharge_cumecs_t_minus_24h"] == 150.0
    assert day_1["feature_discharge_cumecs_t_minus_48h"] is None

    # For day 2, lag 48h should be day 0
    day_2 = aligned[2]
    assert day_2["feature_discharge_cumecs_t_minus_48h"] == 150.0


def test_aligner_handles_unobserved_future(synthetic_series):
    """Verify that last day with no future downstream data sets is_target_observed=False."""
    upstream, downstream = synthetic_series
    aligner = TemporalDataAligner(lead_time_hours=48)
    aligned, _ = aligner.align_series(upstream, downstream)

    # Day 9 cannot observe downstream stage at day 11 (beyond dataset range)
    day_9 = aligned[9]
    assert day_9["is_target_observed"] is False
    assert day_9["target_max_stage_m"] is None
    assert day_9["target_danger_breach"] is None
