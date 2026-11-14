"""
ml/evaluation/run_baseline_evaluation.py

Executes leakage-free comparative evaluation of 24h discharge forecasting baselines.
Evaluates across chronological partitions:
- TRAIN: 2018–2021
- VAL: 2022
- TEST: 2023–2024
Outputs comprehensive evaluation report to:
    data/processed/analysis/phase_2a_baseline_evaluation.json
"""

import csv
import json
from pathlib import Path
from typing import Dict, List, Any

from ml.evaluation.discharge_baselines import (
    ForecastMetricsCalculator,
    DischargePersistenceBaseline,
    DischargeTrailingMeanBaseline,
    DischargeSeasonalNaiveBaseline,
    SimpleLinearDischargeBaseline,
)


def get_default_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


class BaselineEvaluator:
    """Orchestrates comparative benchmarking across partitions and regimes."""

    def __init__(self, repo_root: Optional[Path] = None):
        self.root = repo_root or get_default_repo_root()
        self.dataset_csv = self.root / "data" / "processed" / "modelling" / "hathnikund_discharge_forecasting_24h.csv"
        self.output_json = self.root / "data" / "processed" / "analysis" / "phase_2a_baseline_evaluation.json"

    def run(self) -> Dict[str, Any]:
        if not self.dataset_csv.exists():
            raise FileNotFoundError(f"Dataset missing: {self.dataset_csv}")

        all_rows: List[Dict[str, Any]] = []
        with open(self.dataset_csv, mode="r", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                all_rows.append(r)

        # Filter strictly complete operational rows for fair, uncorrupted comparison
        complete_rows = [r for r in all_rows if r["is_complete_operational_row"] == "True"]

        train_rows = [r for r in complete_rows if r["partition"] == "TRAIN"]
        val_rows = [r for r in complete_rows if r["partition"] == "VAL"]
        test_rows = [r for r in complete_rows if r["partition"] == "TEST"]

        # Instantiate models
        pers_model = DischargePersistenceBaseline()
        trail_model = DischargeTrailingMeanBaseline()
        seas_model = DischargeSeasonalNaiveBaseline()
        linear_model = SimpleLinearDischargeBaseline()

        # Fit models strictly on TRAIN
        seas_model.fit(train_rows)
        linear_model.fit(train_rows)

        models = {
            "persistence": pers_model,
            "trailing_3d_mean": trail_model,
            "seasonal_naive_doy": seas_model,
            "linear_regression_ols": linear_model,
        }

        partitions = {
            "TRAIN": train_rows,
            "VAL": val_rows,
            "TEST": test_rows,
            "FULL": complete_rows,
        }

        results: Dict[str, Any] = {
            "dataset": str(self.dataset_csv.name),
            "partition_sizes": {k: len(v) for k, v in partitions.items()},
            "linear_model_coefficients": {
                "intercept_beta0": round(linear_model.beta_0, 4),
                "q_current_beta1": round(linear_model.beta_1, 4),
                "rf_accum_3d_beta2": round(linear_model.beta_2, 4),
            },
            "evaluations": {},
        }

        for part_name, part_rows in partitions.items():
            results["evaluations"][part_name] = {}
            y_true = [float(r["target_discharge_24h_cumecs"]) for r in part_rows]
            y_pers = pers_model.predict(part_rows)

            for m_name, model in models.items():
                y_pred = model.predict(part_rows)
                # Overall metrics on partition
                base_metrics = ForecastMetricsCalculator.evaluate(y_true, y_pred, y_pers)

                # Regime 1: Monsoon only (Jun-Sep)
                monsoon_indices = [i for i, r in enumerate(part_rows) if r["is_monsoon"] == "1"]
                if monsoon_indices:
                    y_true_m = [y_true[i] for i in monsoon_indices]
                    y_pred_m = [y_pred[i] for i in monsoon_indices]
                    y_pers_m = [y_pers[i] for i in monsoon_indices]
                    m_metrics = ForecastMetricsCalculator.evaluate(y_true_m, y_pred_m, y_pers_m)
                else:
                    m_metrics = {}

                # Regime 2: Non-Monsoon (Oct-May)
                non_monsoon_indices = [i for i, r in enumerate(part_rows) if r["is_monsoon"] == "0"]
                if non_monsoon_indices:
                    y_true_nm = [y_true[i] for i in non_monsoon_indices]
                    y_pred_nm = [y_pred[i] for i in non_monsoon_indices]
                    y_pers_nm = [y_pers[i] for i in non_monsoon_indices]
                    nm_metrics = ForecastMetricsCalculator.evaluate(y_true_nm, y_pred_nm, y_pers_nm)
                else:
                    nm_metrics = {}

                # Regime 3: High-Flow Days (target >= 1,500 cumecs)
                hf_indices = [i for i, y in enumerate(y_true) if y >= 1500.0]
                if hf_indices:
                    y_true_hf = [y_true[i] for i in hf_indices]
                    y_pred_hf = [y_pred[i] for i in hf_indices]
                    y_pers_hf = [y_pers[i] for i in hf_indices]
                    hf_metrics = ForecastMetricsCalculator.evaluate(y_true_hf, y_pred_hf, y_pers_hf)
                else:
                    hf_metrics = {"sample_count": 0, "status": "No high-flow days in this partition"}

                results["evaluations"][part_name][m_name] = {
                    "overall": base_metrics,
                    "monsoon": m_metrics,
                    "non_monsoon": nm_metrics,
                    "high_flow_subset": hf_metrics,
                }

        self.output_json.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_json, mode="w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

        return results
