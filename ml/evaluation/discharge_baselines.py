"""
ml/evaluation/discharge_baselines.py

Empirical Forecasting Baselines and Regression Benchmarks for PRAVAAH Phase 2A.
Evaluates 24h Hathnikund downstream discharge forecasting feasibility against:
1. Persistence Baseline: Q_pred(t+1) = Q(t)
2. Trailing 3-Day Moving Average Baseline: Q_pred(t+1) = mean(Q(t), Q(t-1), Q(t-2))
3. Seasonal-Naive Baseline: Day-of-year mean computed strictly on the TRAIN partition
4. Interpretable OLS Linear Regression Baseline: Fitted strictly on TRAIN (2018–2021)

STRICT EVALUATION SAFEGUARDS:
- Zero data leakage: Parameters/means fitted strictly on the TRAIN partition.
- Chronological evaluation: Evaluates on Validation (2022) and untouched Test (2023–2024).
- Reports MAE, RMSE, R², high-flow subset (Q >= 1,500 cumecs), and seasonal regimes.
"""

import math
from typing import Dict, List, Optional, Any, Tuple


class ForecastMetricsCalculator:
    """Computes standardized continuous regression metrics with sample counts."""

    @staticmethod
    def evaluate(
        y_true: List[float],
        y_pred: List[float],
        baseline_pred_for_skill: Optional[List[float]] = None,
    ) -> Dict[str, Any]:
        n = len(y_true)
        if n == 0 or len(y_pred) != n:
            return {
                "sample_count": 0,
                "mae_cumecs": 0.0,
                "rmse_cumecs": 0.0,
                "r2_score": 0.0,
                "mean_bias_cumecs": 0.0,
            }

        mae = sum(abs(y_true[i] - y_pred[i]) for i in range(n)) / n
        mse = sum((y_true[i] - y_pred[i]) ** 2 for i in range(n)) / n
        rmse = math.sqrt(mse)
        mean_bias = sum(y_pred[i] - y_true[i] for i in range(n)) / n

        mean_y = sum(y_true) / n
        ss_tot = sum((y - mean_y) ** 2 for y in y_true)
        ss_res = sum((y_true[i] - y_pred[i]) ** 2 for i in range(n))
        r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

        res = {
            "sample_count": n,
            "mae_cumecs": round(mae, 2),
            "rmse_cumecs": round(rmse, 2),
            "r2_score": round(r2, 4),
            "mean_bias_cumecs": round(mean_bias, 2),
        }

        # Nash-Sutcliffe Efficiency (NSE) is equivalent to R2 for continuous flow
        res["nse_score"] = round(r2, 4)

        if baseline_pred_for_skill and len(baseline_pred_for_skill) == n:
            mse_base = sum((y_true[i] - baseline_pred_for_skill[i]) ** 2 for i in range(n)) / n
            skill_score = 1.0 - (mse / mse_base) if mse_base > 0 else 0.0
            res["skill_score_vs_persistence"] = round(skill_score, 4)

        return res


class DischargePersistenceBaseline:
    """Predicts tomorrow's discharge equals today's observed discharge: Q(t+1) = Q(t)."""

    def predict(self, rows: List[Dict[str, Any]]) -> List[float]:
        return [float(r["discharge_current_cumecs"]) for r in rows]


class DischargeTrailingMeanBaseline:
    """Predicts tomorrow's discharge equals trailing 3-day average."""

    def predict(self, rows: List[Dict[str, Any]]) -> List[float]:
        preds = []
        for r in rows:
            v = r.get("discharge_rolling_mean_3d_cumecs")
            if v not in (None, ""):
                preds.append(float(v))
            else:
                preds.append(float(r["discharge_current_cumecs"]))
        return preds


class DischargeSeasonalNaiveBaseline:
    """
    Predicts tomorrow's discharge equals the historical day-of-year mean
    computed STRICTLY on the TRAIN partition (2018–2021).
    """

    def __init__(self):
        self.doy_means: Dict[int, float] = {}
        self.global_train_mean: float = 0.0

    def fit(self, train_rows: List[Dict[str, Any]]) -> None:
        """Compute average discharge for each day-of-year on training data only."""
        buckets: Dict[int, List[float]] = {}
        all_vals: List[float] = []

        for r in train_rows:
            target_str = r.get("target_discharge_24h_cumecs")
            if target_str not in (None, ""):
                val = float(target_str)
                # target day of year = next day
                doy = int(r["day_of_year"]) + 1
                if doy > 366:
                    doy = 1
                buckets.setdefault(doy, []).append(val)
                all_vals.append(val)

        self.global_train_mean = sum(all_vals) / len(all_vals) if all_vals else 0.0
        for doy, v_list in buckets.items():
            self.doy_means[doy] = sum(v_list) / len(v_list)

    def predict(self, rows: List[Dict[str, Any]]) -> List[float]:
        preds = []
        for r in rows:
            doy = int(r["day_of_year"]) + 1
            if doy > 366:
                doy = 1
            pred = self.doy_means.get(doy, self.global_train_mean)
            preds.append(pred)
        return preds


class SimpleLinearDischargeBaseline:
    """
    Closed-form Ordinary Least Squares (OLS) linear model.
    Fitted STRICTLY on training partition.
    Predicts Q(t+1) from current discharge Q(t) and antecedent rainfall RF_accum_3d.
    Formula: Q_pred(t+1) = beta_0 + beta_1 * Q(t) + beta_2 * RF_3d(t)
    """

    def __init__(self):
        self.beta_0: float = 0.0
        self.beta_1: float = 0.0
        self.beta_2: float = 0.0
        self.is_fitted: bool = False

    def fit(self, train_rows: List[Dict[str, Any]]) -> None:
        """Fit bivariate linear regression via closed-form normal equations."""
        X1 = []  # Q(t)
        X2 = []  # RF_accum_3d
        Y = []   # Q(t+1)

        for r in train_rows:
            y_str = r.get("target_discharge_24h_cumecs")
            q_str = r.get("discharge_current_cumecs")
            rf_str = r.get("rainfall_accum_3d_prior_mm")
            if (
                y_str not in (None, "")
                and q_str not in (None, "")
                and rf_str not in (None, "")
            ):
                Y.append(float(y_str))
                X1.append(float(q_str))
                X2.append(float(rf_str))

        n = len(Y)
        if n < 10:
            raise ValueError(f"Insufficient training records ({n}) to fit linear model.")

        # Means
        m_x1 = sum(X1) / n
        m_x2 = sum(X2) / n
        m_y = sum(Y) / n

        # Centered sums of squares and cross-products
        s_11 = sum((X1[i] - m_x1) ** 2 for i in range(n))
        s_22 = sum((X2[i] - m_x2) ** 2 for i in range(n))
        s_12 = sum((X1[i] - m_x1) * (X2[i] - m_x2) for i in range(n))

        s_1y = sum((X1[i] - m_x1) * (Y[i] - m_y) for i in range(n))
        s_2y = sum((X2[i] - m_x2) * (Y[i] - m_y) for i in range(n))

        # Determinant of 2x2 covariance
        det = s_11 * s_22 - (s_12 ** 2)
        if abs(det) < 1e-12:
            # Fallback to univariate regression on Q(t)
            self.beta_1 = s_1y / s_11 if s_11 > 0 else 1.0
            self.beta_2 = 0.0
            self.beta_0 = m_y - self.beta_1 * m_x1
        else:
            self.beta_1 = (s_22 * s_1y - s_12 * s_2y) / det
            self.beta_2 = (s_11 * s_2y - s_12 * s_1y) / det
            self.beta_0 = m_y - (self.beta_1 * m_x1 + self.beta_2 * m_x2)

        self.is_fitted = True

    def predict(self, rows: List[Dict[str, Any]]) -> List[float]:
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before predict.")
        preds = []
        for r in rows:
            q = float(r["discharge_current_cumecs"])
            rf_str = r.get("rainfall_accum_3d_prior_mm")
            rf = float(rf_str) if rf_str not in (None, "") else 0.0
            p = self.beta_0 + self.beta_1 * q + self.beta_2 * rf
            # Non-negative discharge guarantee
            preds.append(max(0.0, p))
        return preds
