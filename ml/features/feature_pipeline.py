"""
ml/features/feature_pipeline.py

Feature Engineering and Temporal Lag Construction Pipeline for PRAVAAH.
Transforms raw/processed hydrological time series and gridded rainfall summaries
into a strictly leakage-free tabular feature matrix for 24-hour ahead discharge forecasting.

LEAKAGE DEFENSE GUARANTEES:
1. Rolling Windows: Strictly trailing observations [t - W, t]. Never centered, never forward-looking.
2. Lag Construction: Uses exact calendar-day offsets (t - 1d, t - 2d, etc.).
   Calendar gaps result in explicit Nulls (NaN); zero forward-filling across unobserved days.
3. Target Definition: Strictly Q_ds(date + 1 day). If date + 1 day was not observed,
   has_valid_24h_target is False; target is NEVER fabricated from multi-day gaps.
4. Rainfall Gating: Operational rainfall predictors strictly end on date - 1 day (~23.5h prior).
   Same-day rainfall is isolated and tagged as RETROSPECTIVE_ANALYSIS_ONLY.
"""

import math
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Tuple


class DischargeFeaturePipeline:
    """Computes leakage-resistant predictors and targets for 24h discharge forecasting."""

    @staticmethod
    def compute_cyclical_doy(doy: int) -> Tuple[float, float]:
        """Convert day-of-year into continuous cyclical coordinates (sin, cos)."""
        angle = 2.0 * math.pi * (doy / 365.25)
        return round(math.sin(angle), 6), round(math.cos(angle), 6)

    def process_time_series(
        self,
        dates: List[str],
        ds_records: Dict[str, float],
        us_records: Optional[Dict[str, float]] = None,
        rf_records: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Process chronological list of dates into aligned feature-target dictionaries.

        Args:
            dates: Chronologically sorted list of ISO date strings ('YYYY-MM-DD').
            ds_records: Dict mapping date -> downstream release discharge (HKB D/S in cumecs).
            us_records: Optional dict mapping date -> upstream inflow discharge (HKB U/S in cumecs).
            rf_records: Optional dict mapping date -> {'mean': float, 'max': float, 'valid_cells': int}.

        Returns:
            Tuple of (feature_rows, audit_statistics).
        """
        us_map = us_records or {}
        rf_map = rf_records or {}

        feature_rows: List[Dict[str, Any]] = []

        total_input_dates = len(dates)
        valid_target_count = 0
        broken_target_count = 0
        complete_operational_count = 0
        missing_lag_count = 0
        missing_rf_count = 0

        for d_str in dates:
            d_curr = date.fromisoformat(d_str)
            d_prev_1 = (d_curr - timedelta(days=1)).isoformat()
            d_prev_2 = (d_curr - timedelta(days=2)).isoformat()
            d_prev_3 = (d_curr - timedelta(days=3)).isoformat()
            d_prev_7 = (d_curr - timedelta(days=7)).isoformat()
            d_next_1 = (d_curr + timedelta(days=1)).isoformat()

            q_curr = ds_records.get(d_str)
            if q_curr is None:
                continue

            # ------------------------------------------------------------------
            # 1. TARGET VARIABLE (t + 24h)
            # ------------------------------------------------------------------
            has_valid_target = d_next_1 in ds_records
            target_q = ds_records[d_next_1] if has_valid_target else None

            if has_valid_target:
                valid_target_count += 1
            else:
                broken_target_count += 1

            # ------------------------------------------------------------------
            # 2. DISCHARGE PREDICTORS (Strictly Trailing)
            # ------------------------------------------------------------------
            q_lag_1 = ds_records.get(d_prev_1)
            q_lag_2 = ds_records.get(d_prev_2)
            q_lag_3 = ds_records.get(d_prev_3)
            q_lag_7 = ds_records.get(d_prev_7)

            if q_lag_1 is None:
                missing_lag_count += 1

            q_delta_1 = (q_curr - q_lag_1) if q_lag_1 is not None else None
            q_delta_ratio_1 = ((q_curr - q_lag_1) / (q_lag_1 + 1.0)) if q_lag_1 is not None else None

            # Trailing 3-day window [t - 2d, t - 1d, t]
            window_3d = [ds_records.get((d_curr - timedelta(days=k)).isoformat()) for k in range(3)]
            if all(v is not None for v in window_3d):
                q_rolling_mean_3 = sum(window_3d) / 3.0
            else:
                q_rolling_mean_3 = None

            # Trailing 7-day window [t - 6d, ..., t]
            window_7d = [ds_records.get((d_curr - timedelta(days=k)).isoformat()) for k in range(7)]
            if all(v is not None for v in window_7d):
                q_rolling_mean_7 = sum(window_7d) / 7.0
                q_rolling_max_7 = max(window_7d)
                var_7 = sum((v - q_rolling_mean_7) ** 2 for v in window_7d) / 6.0
                q_rolling_std_7 = math.sqrt(var_7)
            else:
                q_rolling_mean_7 = None
                q_rolling_max_7 = None
                q_rolling_std_7 = None

            q_us_curr = us_map.get(d_str)
            inflow_ratio = (q_us_curr / (q_curr + 1.0)) if q_us_curr is not None else None

            # ------------------------------------------------------------------
            # 3. ANTECEDENT RAINFALL PREDICTORS (Ending on or before date - 1)
            # ------------------------------------------------------------------
            rf_d_minus_1 = rf_map.get(d_prev_1)
            if rf_d_minus_1 is not None:
                rf_mean_1 = rf_d_minus_1.get("mean")
                rf_max_1 = rf_d_minus_1.get("max")
                rf_valid_cells = rf_d_minus_1.get("valid_cells")
            else:
                rf_mean_1 = None
                rf_max_1 = None
                rf_valid_cells = None
                missing_rf_count += 1

            # 3-day antecedent rainfall: dates [D-3, D-2, D-1]
            rf_window_3 = [rf_map.get((d_curr - timedelta(days=k)).isoformat()) for k in [1, 2, 3]]
            if all(r is not None and r.get("mean") is not None for r in rf_window_3):
                rf_accum_3 = sum(r["mean"] for r in rf_window_3)
                rf_max_cell_3 = max(r.get("max", 0.0) for r in rf_window_3)
            else:
                rf_accum_3 = None
                rf_max_cell_3 = None

            # 7-day antecedent rainfall: dates [D-7, ..., D-1]
            rf_window_7 = [rf_map.get((d_curr - timedelta(days=k)).isoformat()) for k in range(1, 8)]
            if all(r is not None and r.get("mean") is not None for r in rf_window_7):
                rf_accum_7 = sum(r["mean"] for r in rf_window_7)
            else:
                rf_accum_7 = None

            # Retrospective concurrent rainfall on date t
            rf_same_day = rf_map.get(d_str)
            rf_same_day_retro = rf_same_day.get("mean") if rf_same_day is not None else None

            # ------------------------------------------------------------------
            # 4. SEASONAL & TEMPORAL METADATA
            # ------------------------------------------------------------------
            doy = d_curr.timetuple().tm_yday
            month = d_curr.month
            sin_doy, cos_doy = self.compute_cyclical_doy(doy)
            is_monsoon = 1 if month in [6, 7, 8, 9] else 0

            # Chronological partition tagging
            if d_curr.year <= 2021:
                partition = "TRAIN"
            elif d_curr.year == 2022:
                partition = "VAL"
            else:
                partition = "TEST"  # 2023-2024

            # ------------------------------------------------------------------
            # 5. COMPLETENESS & QUALITY AUDITING
            # ------------------------------------------------------------------
            core_operational_features = [
                q_curr,
                q_lag_1,
                q_lag_2,
                q_lag_3,
                q_rolling_mean_3,
                q_rolling_mean_7,
                rf_mean_1,
                rf_accum_3,
                rf_accum_7,
                sin_doy,
                cos_doy,
            ]
            is_complete = has_valid_target and all(f is not None for f in core_operational_features)

            missing_flags = []
            if not has_valid_target:
                missing_flags.append("target_discharge_24h_missing")
            if q_lag_1 is None:
                missing_flags.append("q_lag_1d_missing")
            if q_rolling_mean_7 is None:
                missing_flags.append("q_rolling_mean_7d_incomplete_history")
            if rf_mean_1 is None:
                missing_flags.append("rainfall_d_minus_1_missing")
            if rf_accum_7 is None:
                missing_flags.append("rainfall_accum_7d_incomplete_history")

            if is_complete:
                complete_operational_count += 1

            row: Dict[str, Any] = {
                # Identifiers & Timestamps
                "date": d_str,
                "timestamp_utc": f"{d_str}T08:00:00Z",
                "partition": partition,
                "is_monsoon": is_monsoon,
                "day_of_year": doy,
                "month": month,
                "sin_doy": sin_doy,
                "cos_doy": cos_doy,

                # Target
                "target_date": d_next_1 if has_valid_target else "",
                "target_discharge_24h_cumecs": round(target_q, 4) if target_q is not None else None,
                "has_valid_24h_target": has_valid_target,

                # Discharge Predictors (Operational)
                "discharge_current_cumecs": round(q_curr, 4),
                "discharge_lag_1d_cumecs": round(q_lag_1, 4) if q_lag_1 is not None else None,
                "discharge_lag_2d_cumecs": round(q_lag_2, 4) if q_lag_2 is not None else None,
                "discharge_lag_3d_cumecs": round(q_lag_3, 4) if q_lag_3 is not None else None,
                "discharge_lag_7d_cumecs": round(q_lag_7, 4) if q_lag_7 is not None else None,
                "discharge_delta_1d_cumecs": round(q_delta_1, 4) if q_delta_1 is not None else None,
                "discharge_delta_ratio_1d": round(q_delta_ratio_1, 6) if q_delta_ratio_1 is not None else None,
                "discharge_rolling_mean_3d_cumecs": round(q_rolling_mean_3, 4) if q_rolling_mean_3 is not None else None,
                "discharge_rolling_mean_7d_cumecs": round(q_rolling_mean_7, 4) if q_rolling_mean_7 is not None else None,
                "discharge_rolling_max_7d_cumecs": round(q_rolling_max_7, 4) if q_rolling_max_7 is not None else None,
                "discharge_rolling_std_7d_cumecs": round(q_rolling_std_7, 4) if q_rolling_std_7 is not None else None,
                "inflow_current_cumecs": round(q_us_curr, 4) if q_us_curr is not None else None,
                "inflow_release_ratio_current": round(inflow_ratio, 4) if inflow_ratio is not None else None,

                # Antecedent Rainfall Predictors (Operational)
                "rainfall_mean_d_minus_1_mm": round(rf_mean_1, 4) if rf_mean_1 is not None else None,
                "rainfall_max_cell_d_minus_1_mm": round(rf_max_1, 4) if rf_max_1 is not None else None,
                "rainfall_accum_3d_prior_mm": round(rf_accum_3, 4) if rf_accum_3 is not None else None,
                "rainfall_accum_7d_prior_mm": round(rf_accum_7, 4) if rf_accum_7 is not None else None,
                "rainfall_max_cell_3d_prior_mm": round(rf_max_cell_3, 4) if rf_max_cell_3 is not None else None,
                "rainfall_valid_cells_d_minus_1": rf_valid_cells,

                # Retrospective Only (Forbidden in operational real-time forecasting)
                "rainfall_mean_same_day_retro_mm": round(rf_same_day_retro, 4) if rf_same_day_retro is not None else None,

                # Quality Flags
                "is_complete_operational_row": is_complete,
                "missing_feature_flags": ";".join(missing_flags),
            }

            feature_rows.append(row)

        audit_summary = {
            "total_input_dates": total_input_dates,
            "generated_rows": len(feature_rows),
            "valid_target_rows": valid_target_count,
            "broken_target_rows": broken_target_count,
            "complete_operational_rows": complete_operational_count,
            "incomplete_rows": len(feature_rows) - complete_operational_count,
            "missing_lag1_count": missing_lag_count,
            "missing_rf_d_minus_1_count": missing_rf_count,
            "date_range_start": dates[0] if dates else None,
            "date_range_end": dates[-1] if dates else None,
        }

        return feature_rows, audit_summary
