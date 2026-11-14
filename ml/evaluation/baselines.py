"""
ml/evaluation/baselines.py

Simple Non-Machine-Learning Hydrological Benchmarks for PRAVAAH.
Provides empirical baseline models against which future machine learning
architectures (Random Forest, Gradient Boosting, LSTMs) must be evaluated.

SUPPORTED BASELINES:
1. Persistence Baseline:
   Assumes future flood stage equals current stage.
2. Recent-Trend Baseline:
   Extrapolates linear rate of rise (dH/dt) over forward lead time.
3. Upstream Lag Cross-Correlation Baseline:
   Estimates empirical hydrodynamic travel lag between upstream discharge
   and downstream water level without assuming prior coefficients.

SAFETY RULES:
- Zero machine learning model training (No Random Forest, No Neural Networks).
- Transparent, deterministic mathematical heuristics only.
"""

import math
from typing import Dict, List, Optional, Any, Tuple


class PersistenceBaseline:
    """Predicts future flood state based strictly on current local water level."""

    def __init__(self, danger_threshold_m: float = 205.33):
        self.danger_threshold_m = danger_threshold_m

    def predict_binary(self, current_stage_m: float) -> int:
        """Predict 1 if currently at or above threshold, else 0."""
        return 1 if current_stage_m >= self.danger_threshold_m else 0

    def predict_probability(self, current_stage_m: float, buffer_m: float = 1.0) -> float:
        """
        Estimate pseudo-probability based on proximity to threshold.
        If current_stage >= threshold -> 1.0
        If current_stage <= threshold - buffer -> 0.0
        Linearly interpolated in between.
        """
        if current_stage_m >= self.danger_threshold_m:
            return 1.0
        lower_bound = self.danger_threshold_m - buffer_m
        if current_stage_m <= lower_bound:
            return 0.0
        return round((current_stage_m - lower_bound) / buffer_m, 4)


class RecentTrendBaseline:
    """Extrapolates recent rate of change (dH/dt) forward over the prediction lead time."""

    def __init__(self, danger_threshold_m: float = 205.33, lead_time_hours: float = 48.0):
        self.danger_threshold_m = danger_threshold_m
        self.lead_time_hours = lead_time_hours

    def predict_stage(
        self, stage_t: float, stage_t_minus_dt: float, dt_hours: float
    ) -> float:
        """Linearly extrapolate stage forward: Stage_future = Stage_t + (dH/dt) * lead_time."""
        if dt_hours <= 0:
            return stage_t
        rate_of_rise = (stage_t - stage_t_minus_dt) / dt_hours
        predicted_stage = stage_t + (rate_of_rise * self.lead_time_hours)
        return round(predicted_stage, 3)

    def predict_binary(
        self, stage_t: float, stage_t_minus_dt: float, dt_hours: float
    ) -> int:
        """Predict 1 if extrapolated stage reaches or exceeds danger mark, else 0."""
        pred = self.predict_stage(stage_t, stage_t_minus_dt, dt_hours)
        return 1 if pred >= self.danger_threshold_m else 0


class UpstreamLagAnalyzer:
    """Computes empirical cross-correlation between upstream discharge and downstream stage."""

    @staticmethod
    def compute_lag_correlation(
        upstream_series: List[float],
        downstream_series: List[float],
        max_lag_steps: int = 10,
    ) -> Dict[int, float]:
        """
        Compute Pearson correlation r(k) between upstream[t] and downstream[t + k].
        
        Args:
            upstream_series: Sequence of upstream discharge values.
            downstream_series: Synchronized sequence of downstream stage values.
            max_lag_steps: Maximum discrete steps to shift forward.
        """
        n = min(len(upstream_series), len(downstream_series))
        if n < 5:
            return {}

        results: Dict[int, float] = {}

        for lag in range(0, max_lag_steps + 1):
            if n - lag < 3:
                break
            x = upstream_series[: n - lag]
            y = downstream_series[lag:n]

            # Compute Pearson correlation
            mean_x = sum(x) / len(x)
            mean_y = sum(y) / len(y)

            num = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
            den_x = sum((xi - mean_x) ** 2 for xi in x)
            den_y = sum((yi - mean_y) ** 2 for yi in y)

            if den_x > 0 and den_y > 0:
                r = num / math.sqrt(den_x * den_y)
                results[lag] = round(r, 4)
            else:
                results[lag] = 0.0

        return results

    @staticmethod
    def find_optimal_lag(lag_correlations: Dict[int, float]) -> Tuple[int, float]:
        """Identify discrete lag step yielding highest positive correlation."""
        if not lag_correlations:
            return (0, 0.0)
        best_lag = max(lag_correlations.keys(), key=lambda k: lag_correlations[k])
        return (best_lag, lag_correlations[best_lag])


def compute_binary_classification_metrics(
    y_true: List[int], y_pred: List[int]
) -> Dict[str, float]:
    """Calculate standard verification metrics: Precision, Recall, F1, Accuracy, Specificity."""
    if len(y_true) != len(y_pred) or len(y_true) == 0:
        return {}

    tp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 1 and yp == 1)
    fp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 0 and yp == 1)
    fn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 1 and yp == 0)
    tn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 0 and yp == 0)

    total = len(y_true)
    accuracy = round((tp + tn) / total, 4) if total > 0 else 0.0
    precision = round(tp / (tp + fp), 4) if (tp + fp) > 0 else 0.0
    recall = round(tp / (tp + fn), 4) if (tp + fn) > 0 else 0.0
    f1 = round(2 * precision * recall / (precision + recall), 4) if (precision + recall) > 0 else 0.0
    specificity = round(tn / (tn + fp), 4) if (tn + fp) > 0 else 0.0

    return {
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "true_negatives": tn,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "specificity": specificity,
    }
