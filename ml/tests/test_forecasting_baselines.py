"""
ml/tests/test_forecasting_baselines.py

Automated test suite for PRAVAAH Forecasting Baselines & Metrics Calculator.
Tests persistence, trailing mean, seasonal-naive, and linear OLS benchmarks.
Synthetic fixtures are strictly labeled as synthetic test fixtures.
"""

import pytest
import math
from ml.evaluation.discharge_baselines import (
    ForecastMetricsCalculator,
    DischargePersistenceBaseline,
    DischargeTrailingMeanBaseline,
    DischargeSeasonalNaiveBaseline,
    SimpleLinearDischargeBaseline,
)


def test_metrics_calculator_exact_values():
    """Verify metrics calculator on known synthetic values."""
    y_true = [10.0, 20.0, 30.0, 40.0, 50.0]
    y_pred = [12.0, 18.0, 33.0, 38.0, 50.0]  # errors: +2, -2, +3, -2, 0 -> abs sum = 9, mae = 1.8
    # sq errors: 4 + 4 + 9 + 4 + 0 = 21 -> mse = 4.2 -> rmse = sqrt(4.2) ~= 2.049

    metrics = ForecastMetricsCalculator.evaluate(y_true, y_pred)
    assert metrics["sample_count"] == 5
    assert math.isclose(metrics["mae_cumecs"], 1.8, abs_tol=1e-2)
    assert math.isclose(metrics["rmse_cumecs"], math.sqrt(4.2), abs_tol=1e-2)
    assert metrics["r2_score"] > 0.95


def test_metrics_calculator_empty():
    """Verify metrics calculator handles empty series gracefully."""
    metrics = ForecastMetricsCalculator.evaluate([], [])
    assert metrics["sample_count"] == 0
    assert metrics["mae_cumecs"] == 0.0


def test_persistence_baseline_synthetic():
    """Verify persistence baseline outputs Q(t) for every record."""
    synthetic_rows = [
        {"discharge_current_cumecs": 120.5, "target_discharge_24h_cumecs": 140.0},
        {"discharge_current_cumecs": 250.0, "target_discharge_24h_cumecs": 200.0},
    ]
    model = DischargePersistenceBaseline()
    preds = model.predict(synthetic_rows)
    assert preds == [120.5, 250.0]


def test_trailing_mean_baseline_synthetic():
    """Verify trailing mean baseline uses 3d rolling mean when present."""
    synthetic_rows = [
        {"discharge_current_cumecs": 100.0, "discharge_rolling_mean_3d_cumecs": 80.0},
        {"discharge_current_cumecs": 200.0, "discharge_rolling_mean_3d_cumecs": None},
    ]
    model = DischargeTrailingMeanBaseline()
    preds = model.predict(synthetic_rows)
    assert preds[0] == 80.0
    assert preds[1] == 200.0  # fallback to current when rolling is None


def test_seasonal_naive_baseline_train_fit_synthetic():
    """Verify seasonal-naive baseline fits strictly on train records and looks up DOY."""
    train_rows = [
        {"day_of_year": 180, "target_discharge_24h_cumecs": 500.0},
        {"day_of_year": 180, "target_discharge_24h_cumecs": 700.0},
        {"day_of_year": 200, "target_discharge_24h_cumecs": 100.0},
    ]
    model = DischargeSeasonalNaiveBaseline()
    model.fit(train_rows)

    # Next day DOY for day 180 is 181, which has average (500 + 700) / 2 = 600.0
    test_rows = [{"day_of_year": 180}]
    preds = model.predict(test_rows)
    assert math.isclose(preds[0], 600.0, abs_tol=1e-2)


def test_linear_ols_baseline_fit_and_predict_synthetic():
    """Verify OLS linear baseline computes closed-form coefficients and enforces non-negative output."""
    # Synthetic linear relationship: Q(t+1) = 10.0 + 0.5 * Q(t) + 2.0 * RF(t)
    train_rows = []
    for q in [10.0, 20.0, 50.0, 80.0, 100.0]:
        for rf in [5.0, 25.0, 40.0]:
            y = 10.0 + 0.5 * q + 2.0 * rf
            train_rows.append({
                "discharge_current_cumecs": q,
                "rainfall_accum_3d_prior_mm": rf,
                "target_discharge_24h_cumecs": y,
            })

    model = SimpleLinearDischargeBaseline()
    model.fit(train_rows)

    assert math.isclose(model.beta_0, 10.0, abs_tol=1e-2)
    assert math.isclose(model.beta_1, 0.5, abs_tol=1e-2)
    assert math.isclose(model.beta_2, 2.0, abs_tol=1e-2)

    test_row = [{"discharge_current_cumecs": 50.0, "rainfall_accum_3d_prior_mm": 10.0}]
    # 10 + 0.5*50 + 2*10 = 55.0
    pred = model.predict(test_row)
    assert math.isclose(pred[0], 55.0, abs_tol=1e-2)


def test_linear_ols_unfitted_raises_error():
    """Verify calling predict on unfitted model raises RuntimeError."""
    model = SimpleLinearDischargeBaseline()
    with pytest.raises(RuntimeError, match="must be fitted"):
        model.predict([{"discharge_current_cumecs": 10.0}])
