"""
ml/features/eda_analysis.py

Reproducible Exploratory Data Analysis (EDA) Engine for PRAVAAH Phase 2A.
Computes distributional statistics, seasonal regimes, autocorrelations,
lag associations, and feature-target relationships for 24h Hathnikund discharge forecasting.
Outputs results to:
    data/processed/analysis/phase_2a_eda_summary.json
"""

import csv
import json
import math
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple


def get_default_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


class ExploratoryDataAnalyzer:
    """Performs empirical statistical analysis on the forecasting dataset."""

    def __init__(self, repo_root: Optional[Path] = None):
        self.root = repo_root or get_default_repo_root()
        self.dataset_csv = self.root / "data" / "processed" / "modelling" / "hathnikund_discharge_forecasting_24h.csv"
        self.output_json = self.root / "data" / "processed" / "analysis" / "phase_2a_eda_summary.json"

    @staticmethod
    def _percentile(sorted_vals: List[float], p: float) -> float:
        if not sorted_vals:
            return 0.0
        idx = int(p * (len(sorted_vals) - 1))
        return sorted_vals[idx]

    @staticmethod
    def _stats(values: List[float]) -> Dict[str, float]:
        n = len(values)
        if n == 0:
            return {"count": 0, "mean": 0.0, "std": 0.0, "p50": 0.0, "p90": 0.0, "p95": 0.0, "p99": 0.0, "max": 0.0, "min": 0.0}
        s = sorted(values)
        mean_v = sum(s) / n
        var_v = sum((x - mean_v) ** 2 for x in s) / (n - 1) if n > 1 else 0.0
        std_v = math.sqrt(var_v)
        return {
            "count": n,
            "mean": round(mean_v, 2),
            "std": round(std_v, 2),
            "min": round(s[0], 2),
            "p50": round(ExploratoryDataAnalyzer._percentile(s, 0.50), 2),
            "p90": round(ExploratoryDataAnalyzer._percentile(s, 0.90), 2),
            "p95": round(ExploratoryDataAnalyzer._percentile(s, 0.95), 2),
            "p99": round(ExploratoryDataAnalyzer._percentile(s, 0.99), 2),
            "max": round(s[-1], 2),
        }

    @staticmethod
    def _pearson_and_spearman(x: List[float], y: List[float]) -> Tuple[Optional[float], Optional[float]]:
        n = len(x)
        if n < 3:
            return None, None
        mx = sum(x) / n
        my = sum(y) / n
        cov = sum((x[i] - mx) * (y[i] - my) for i in range(n))
        var_x = sum((x[i] - mx) ** 2 for i in range(n))
        var_y = sum((y[i] - my) ** 2 for i in range(n))
        if var_x == 0 or var_y == 0:
            return None, None
        r = cov / math.sqrt(var_x * var_y)

        # Spearman rank
        sorted_x = sorted((val, idx) for idx, val in enumerate(x))
        sorted_y = sorted((val, idx) for idx, val in enumerate(y))
        rx = [0.0] * n
        ry = [0.0] * n
        for rank, (_, idx) in enumerate(sorted_x):
            rx[idx] = rank + 1
        for rank, (_, idx) in enumerate(sorted_y):
            ry[idx] = rank + 1
        m_r = (n + 1) / 2.0
        cov_r = sum((rx[i] - m_r) * (ry[i] - m_r) for i in range(n))
        var_r = sum((rx[i] - m_r) ** 2 for i in range(n))
        rho = cov_r / var_r if var_r > 0 else 0.0

        return round(r, 4), round(rho, 4)

    def run_analysis(self) -> Dict[str, Any]:
        """Load dataset, perform full EDA calculations, and save summary JSON."""
        if not self.dataset_csv.exists():
            raise FileNotFoundError(f"Forecasting dataset not found at: {self.dataset_csv}")

        rows: List[Dict[str, Any]] = []
        with open(self.dataset_csv, mode="r", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                rows.append(r)

        # Filter complete operational rows with valid target
        complete_rows = [r for r in rows if r["is_complete_operational_row"] == "True"]
        target_rows = [r for r in rows if r["has_valid_24h_target"] == "True"]

        # 1. Overall Discharge Distribution
        q_current_all = [float(r["discharge_current_cumecs"]) for r in rows]
        q_target_all = [float(r["target_discharge_24h_cumecs"]) for r in target_rows]
        overall_stats_current = self._stats(q_current_all)
        overall_stats_target = self._stats(q_target_all)

        # 2. Delta Distribution Q(t+1) - Q(t)
        deltas = [
            float(r["target_discharge_24h_cumecs"]) - float(r["discharge_current_cumecs"])
            for r in target_rows
        ]
        delta_stats = self._stats(deltas)

        # 3. Seasonal Regimes: Monsoon (Jun-Sep) vs Non-Monsoon (Oct-May)
        q_monsoon = [float(r["discharge_current_cumecs"]) for r in rows if r["is_monsoon"] == "1"]
        q_non_monsoon = [float(r["discharge_current_cumecs"]) for r in rows if r["is_monsoon"] == "0"]
        monsoon_stats = self._stats(q_monsoon)
        non_monsoon_stats = self._stats(q_non_monsoon)

        # 4. By-Year Breakdown
        years = sorted(list({r["date"][:4] for r in rows}))
        by_year: Dict[str, Any] = {}
        for yr in years:
            yr_rows = [r for r in rows if r["date"].startswith(yr)]
            yr_q = [float(r["discharge_current_cumecs"]) for r in yr_rows]
            by_year[yr] = {
                "observed_days": len(yr_rows),
                "missing_days": (366 if yr in ["2020", "2024"] else 365) - len(yr_rows),
                "mean_cumecs": round(sum(yr_q) / len(yr_q), 2) if yr_q else 0.0,
                "max_cumecs": round(max(yr_q), 2) if yr_q else 0.0,
                "high_flow_days_above_1500": sum(1 for q in yr_q if q >= 1500.0),
            }

        # 5. Autocorrelation Function (ACF) from Lag 1 to Lag 14
        # Compute across continuous calendar segments
        acf_results: Dict[str, float] = {}
        q_by_date = {r["date"]: float(r["discharge_current_cumecs"]) for r in rows}
        sorted_dates = sorted(list(q_by_date.keys()))

        mean_q = overall_stats_current["mean"]
        var_q = sum((q_by_date[d] - mean_q) ** 2 for d in sorted_dates)

        for k in range(1, 15):
            paired_dev = []
            for d in sorted_dates:
                d_curr = date.fromisoformat(d)
                d_lag = (d_curr - timedelta(days=k)).isoformat()
                if d_lag in q_by_date:
                    paired_dev.append((q_by_date[d] - mean_q) * (q_by_date[d_lag] - mean_q))
            if var_q > 0 and paired_dev:
                # normalize by total variance
                r_k = sum(paired_dev) / var_q
                acf_results[f"lag_{k}d"] = round(r_k, 4)

        # 6. Feature-Target Associations (All, Monsoon, Non-Monsoon)
        candidate_predictors = [
            ("discharge_current_cumecs", "Current Discharge Q(t)"),
            ("discharge_lag_1d_cumecs", "Lag 1 Discharge Q(t-1)"),
            ("discharge_lag_2d_cumecs", "Lag 2 Discharge Q(t-2)"),
            ("discharge_lag_3d_cumecs", "Lag 3 Discharge Q(t-3)"),
            ("discharge_rolling_mean_3d_cumecs", "Trailing 3d Mean Discharge"),
            ("discharge_rolling_mean_7d_cumecs", "Trailing 7d Mean Discharge"),
            ("discharge_delta_1d_cumecs", "Discharge 24h Delta"),
            ("rainfall_mean_d_minus_1_mm", "Catchment Rainfall D-1 Mean"),
            ("rainfall_accum_3d_prior_mm", "Catchment Rainfall 3d Accum"),
            ("rainfall_accum_7d_prior_mm", "Catchment Rainfall 7d Accum"),
            ("rainfall_mean_same_day_retro_mm", "Same-Day Rainfall (Retro Only)"),
            ("sin_doy", "Cyclical Sine Day-of-Year"),
            ("cos_doy", "Cyclical Cosine Day-of-Year"),
        ]

        def compute_assoc(row_subset: List[Dict[str, Any]]) -> Dict[str, Any]:
            res: Dict[str, Any] = {}
            y_vals = [float(r["target_discharge_24h_cumecs"]) for r in row_subset]
            for col_name, label in candidate_predictors:
                x_vals = []
                paired_y = []
                for i, r in enumerate(row_subset):
                    v = r.get(col_name)
                    if v not in (None, ""):
                        try:
                            x_vals.append(float(v))
                            paired_y.append(y_vals[i])
                        except ValueError:
                            pass
                r_val, rho_val = self._pearson_and_spearman(x_vals, paired_y)
                res[col_name] = {
                    "label": label,
                    "count": len(x_vals),
                    "pearson_r": r_val,
                    "spearman_rho": rho_val,
                }
            return res

        assoc_all = compute_assoc(complete_rows)
        assoc_monsoon = compute_assoc([r for r in complete_rows if r["is_monsoon"] == "1"])
        assoc_non_monsoon = compute_assoc([r for r in complete_rows if r["is_monsoon"] == "0"])

        # 7. Persistence Baseline Benchmark (Theoretical)
        # Error metrics of persistence: pred(t+1) = Q(t) on complete rows
        y_true = [float(r["target_discharge_24h_cumecs"]) for r in complete_rows]
        y_pers = [float(r["discharge_current_cumecs"]) for r in complete_rows]
        n_c = len(y_true)

        mae_pers = sum(abs(y_true[i] - y_pers[i]) for i in range(n_c)) / n_c
        rmse_pers = math.sqrt(sum((y_true[i] - y_pers[i]) ** 2 for i in range(n_c)) / n_c)
        var_y = sum((y - (sum(y_true) / n_c)) ** 2 for y in y_true)
        ss_res = sum((y_true[i] - y_pers[i]) ** 2 for i in range(n_c))
        r2_pers = 1.0 - (ss_res / var_y) if var_y > 0 else 0.0

        eda_summary = {
            "dataset_file": str(self.dataset_csv.name),
            "total_records": len(rows),
            "complete_operational_records": len(complete_rows),
            "valid_target_records": len(target_rows),
            "discharge_current_stats": overall_stats_current,
            "target_discharge_24h_stats": overall_stats_target,
            "discharge_delta_24h_stats": delta_stats,
            "monsoon_stats": monsoon_stats,
            "non_monsoon_stats": non_monsoon_stats,
            "by_year_summary": by_year,
            "autocorrelation_acf": acf_results,
            "correlations_all_days": assoc_all,
            "correlations_monsoon": assoc_monsoon,
            "correlations_non_monsoon": assoc_non_monsoon,
            "overall_persistence_benchmark": {
                "sample_count": n_c,
                "mae_cumecs": round(mae_pers, 2),
                "rmse_cumecs": round(rmse_pers, 2),
                "r2_score": round(r2_pers, 4),
            },
        }

        self.output_json.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_json, mode="w", encoding="utf-8") as f:
            json.dump(eda_summary, f, indent=2)

        return eda_summary
