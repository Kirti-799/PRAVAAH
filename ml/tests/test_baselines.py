"""
ml/tests/test_baselines.py

Automated unit tests for non-machine-learning baselines.
SAFETY WARNING:
All fixtures created in this test file are EXPLICITLY SYNTHETIC and TEMPORARY.
They exist purely to test mathematical calculations of Persistence, Trend, and Lag correlation.
THEY DO NOT REPRESENT REAL-WORLD FLOOD, HYDROLOGICAL, OR METEOROLOGICAL OBSERVATIONS.
"""

import pytest
from ml.evaluation.baselines import (
    PersistenceBaseline,
    RecentTrendBaseline,
    UpstreamLagAnalyzer,
    compute_binary_classification_metrics,
)


def test_persistence_baseline():
    """Verify persistence binary and linear probability predictions."""
    model = PersistenceBaseline(danger_threshold_m=205.33)

    assert model.predict_binary(205.34) == 1
    assert model.predict_binary(205.32) == 0
    assert model.predict_probability(205.33) == 1.0
    assert model.predict_probability(204.33, buffer_m=1.0) == 0.0
    assert model.predict_probability(204.83, buffer_m=1.0) == 0.5


def test_recent_trend_baseline():
    """Verify linear rate-of-rise extrapolation over lead time."""
    model = RecentTrendBaseline(danger_threshold_m=205.33, lead_time_hours=48.0)

    # Rising 0.5m over 24h -> dH/dt = 0.5 / 24 m/h. Over 48h -> rise of 1.0m
    # Current stage: 204.5 -> Extrapolated stage: 205.5 (exceeds 205.33)
    pred_stage = model.predict_stage(stage_t=204.5, stage_t_minus_dt=204.0, dt_hours=24.0)
    assert pred_stage == 205.5
    assert model.predict_binary(stage_t=204.5, stage_t_minus_dt=204.0, dt_hours=24.0) == 1

    # Falling stage -> should predict 0
    assert model.predict_binary(stage_t=204.5, stage_t_minus_dt=205.0, dt_hours=24.0) == 0


def test_upstream_lag_analyzer():
    """Verify cross-correlation lag peak detection on synthetic lagged waves."""
    # Synthetic upstream wave peaking at t=2
    # Downstream wave peaking at t=4 (optimal lag = 2 steps)
    upstream = [10.0, 50.0, 100.0, 50.0, 10.0, 5.0, 5.0, 5.0, 5.0, 5.0]
    downstream = [2.0, 2.0, 10.0, 50.0, 100.0, 50.0, 10.0, 5.0, 5.0, 5.0]

    lag_corrs = UpstreamLagAnalyzer.compute_lag_correlation(upstream, downstream, max_lag_steps=4)
    best_lag, best_r = UpstreamLagAnalyzer.find_optimal_lag(lag_corrs)

    assert best_lag == 2
    assert best_r > 0.95


def test_classification_metrics():
    """Verify calculation of precision, recall, F1, and accuracy."""
    y_true = [1, 1, 0, 0, 1]
    y_pred = [1, 0, 0, 0, 1]

    metrics = compute_binary_classification_metrics(y_true, y_pred)
    assert metrics["true_positives"] == 2
    assert metrics["false_negatives"] == 1
    assert metrics["false_positives"] == 0
    assert metrics["true_negatives"] == 2
    assert metrics["recall"] == round(2 / 3, 4)
    assert metrics["precision"] == 1.0
    assert metrics["accuracy"] == 0.8
