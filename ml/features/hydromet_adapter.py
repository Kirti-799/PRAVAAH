"""
ml/features/hydromet_adapter.py

PRAVAAH Phase 3E.2: Hydrometeorological Feature Adapter & Coupling Engine.
Establishes a scientifically sound connection between live catchment meteorological feeds,
historical/operator hydrometric observations, and the existing Hathnikund discharge model (hathnikund_rf_v1).

SCIENTIFIC INTEGRITY ENFORCEMENT & STRICT CONSTRAINTS:
1. Model Preservation: Does NOT retrain or overwrite hathnikund_rf_v1.
2. Training Set Preservation: Does NOT modify original training sets.
3. Zero Invention: Never fabricates missing discharge telemetry or rainfall observations.
4. Mathematical Precision: Antecedent linear sums (sum P_{t-i}) are strictly differentiated
   from exponentially decayed Antecedent Precipitation Indices (API_t = sum k^i * P_{t-i}).
5. Temporal Alignment: Explicitly defines the 24h rolling accumulation ending at 08:30 IST
   (03:00 UTC) and resolves the 8.5h phase shift from midnight-to-midnight (00:00-24:00 IST) products.
6. Covariate Shift Auditing: Documents the spatial footprint discrepancy between the 91-cell
   IMD regional bounding box ([28°N-31°N, 76.5°E-78°E]) and the 20-node orographic catchment grid.
7. Operational Governance: Prohibits labeling predictions as autonomous flood warnings.
"""

import math
from datetime import datetime, date, time, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
import numpy as np

from ml.training.train_discharge_models import OPERATIONAL_FEATURE_ALLOWLIST
from ml.features.feature_manifest import FEATURE_MANIFEST


# IST is UTC + 05:30
IST_OFFSET = timedelta(hours=5, minutes=30)
IST_TZ = timezone(IST_OFFSET, name="IST")


class TemporalAlignmentError(ValueError):
    """Raised when timestamp series cannot be aligned to the 08:30 IST reporting window."""
    pass


class FeatureCompatibilityError(ValueError):
    """Raised when an attempt is made to force an invalid feature conversion."""
    pass


class Rolling24hAccumulator:
    """
    Constructs rolling 24-hour precipitation accumulation ending at 08:30 IST (03:00 UTC).
    """

    @staticmethod
    def parse_iso_to_ist(iso_str: str) -> datetime:
        """
        Parses an ISO datetime string and normalizes to IST (Asia/Kolkata, UTC+05:30).
        Handles both UTC 'Z' strings and naive/local timestamp formats.
        """
        # Replace 'Z' with +00:00 for fromisoformat
        cleaned = iso_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(cleaned)
        if dt.tzinfo is None:
            # Assume local Open-Meteo IST if naive and returned with timezone=Asia/Kolkata
            dt = dt.replace(tzinfo=IST_TZ)
        else:
            dt = dt.astimezone(IST_TZ)
        return dt

    @classmethod
    def reconstruct_0830_ist_daily_accumulation(
        cls,
        hourly_timestamps: List[str],
        hourly_precipitation: List[float],
        target_date_ist: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Reconstructs the official 24-hour IMD rainfall window:
        Window = (target_date - 1 day, 08:30:00 IST) to (target_date, 08:30:00 IST].
        In discrete hourly observations, this corresponds to the 24 hourly values
        from 09:00 IST on date D-1 up to 08:00 IST (inclusive) on date D.
        """
        if len(hourly_timestamps) != len(hourly_precipitation):
            raise TemporalAlignmentError(
                f"Mismatch between timestamp count ({len(hourly_timestamps)}) and precipitation count ({len(hourly_precipitation)})"
            )

        if not hourly_timestamps:
            return {
                "accumulation_24h_mm": 0.0,
                "valid_hours_count": 0,
                "is_complete_24h_window": False,
                "missing_hours_count": 24,
                "window_start_ist": None,
                "window_end_ist": None,
                "target_date_ist": str(target_date_ist) if target_date_ist else None,
            }

        # Parse all timestamps to IST
        parsed_entries = []
        for ts_str, p_val in zip(hourly_timestamps, hourly_precipitation):
            parsed_dt = cls.parse_iso_to_ist(ts_str)
            parsed_entries.append((parsed_dt, float(p_val) if p_val is not None else np.nan))

        # Sort by timestamp
        parsed_entries.sort(key=lambda x: x[0])

        if target_date_ist is None:
            # Default to the target date of the latest available timestamp
            latest_dt = parsed_entries[-1][0]
            # If latest is after 08:30, target date is today; if before, target date is today (incomplete)
            target_date_ist = latest_dt.date()

        # Define exact IMD window boundaries
        # Start: D - 1 day at 08:30:00 IST
        # End: D at 08:30:00 IST
        prev_date = target_date_ist - timedelta(days=1)
        window_start = datetime.combine(prev_date, time(8, 30), tzinfo=IST_TZ)
        window_end = datetime.combine(target_date_ist, time(8, 30), tzinfo=IST_TZ)

        # Filter entries falling strictly within (window_start, window_end]
        window_precip = []
        for dt, val in parsed_entries:
            if window_start < dt <= window_end:
                window_precip.append(val)

        valid_vals = [v for v in window_precip if not np.isnan(v)]
        missing_count = 24 - len(valid_vals)

        if len(valid_vals) == 24:
            total_acc = sum(valid_vals)
            is_complete = True
        elif len(valid_vals) > 0:
            # Incomplete window: sum available but flag incompleteness
            total_acc = sum(valid_vals)
            is_complete = False
        else:
            total_acc = 0.0
            is_complete = False

        return {
            "accumulation_24h_mm": round(float(total_acc), 2),
            "valid_hours_count": len(valid_vals),
            "is_complete_24h_window": is_complete,
            "missing_hours_count": max(0, missing_count),
            "window_start_ist": window_start.isoformat(),
            "window_end_ist": window_end.isoformat(),
            "target_date_ist": str(target_date_ist),
        }


class HydrometAntecedentCalculator:
    """
    Computes antecedent precipitation features matching the original model schema.
    Strictly contrasts linear sums against exponentially decayed API indices.
    """

    @staticmethod
    def compute_unweighted_linear_accumulations(daily_history_mm: List[float]) -> Dict[str, float]:
        """
        Computes exact training-schema antecedent linear sums:
        - rainfall_accum_3d_prior_mm = P_{D-1} + P_{D-2} + P_{D-3}
        - rainfall_accum_7d_prior_mm = sum_{k=1}^7 P_{D-k}
        - rainfall_max_cell_3d_prior_mm = max(P_{D-1}, P_{D-2}, P_{D-3})
        Where daily_history_mm is ordered [D-1, D-2, ..., D-N].
        """
        if not daily_history_mm:
            return {
                "rainfall_mean_d_minus_1_mm": 0.0,
                "rainfall_accum_3d_prior_mm": 0.0,
                "rainfall_accum_7d_prior_mm": 0.0,
                "rainfall_max_cell_3d_prior_mm": 0.0,
            }

        p_d1 = max(0.0, float(daily_history_mm[0])) if len(daily_history_mm) >= 1 else 0.0
        p_3d = sum(max(0.0, float(v)) for v in daily_history_mm[:3])
        p_7d = sum(max(0.0, float(v)) for v in daily_history_mm[:7])
        max_3d = max(max(0.0, float(v)) for v in daily_history_mm[:3])

        return {
            "rainfall_mean_d_minus_1_mm": round(p_d1, 2),
            "rainfall_accum_3d_prior_mm": round(p_3d, 2),
            "rainfall_accum_7d_prior_mm": round(p_7d, 2),
            "rainfall_max_cell_3d_prior_mm": round(max_3d, 2),
        }

    @staticmethod
    def compute_exponential_api(daily_history_mm: List[float], days: int, k: float = 0.85) -> float:
        """
        Computes Antecedent Precipitation Index with recession factor k:
        API_N = sum_{i=1}^N (k^i * P_{t-i})
        Where daily_history_mm is ordered [D-1, D-2, ..., D-N].
        """
        if not daily_history_mm:
            return 0.0
        n = min(days, len(daily_history_mm))
        api_val = 0.0
        for i in range(n):
            val = max(0.0, float(daily_history_mm[i]))
            decay = k ** (i + 1)
            api_val += decay * val
        return round(api_val, 2)

    @classmethod
    def compare_linear_sum_vs_api(cls, daily_history_mm: List[float]) -> Dict[str, Any]:
        """
        Explicitly demonstrates mathematical inequality between linear accumulation
        and exponential API indices (Rule 4).
        """
        linear_3d = sum(daily_history_mm[:3]) if len(daily_history_mm) >= 3 else sum(daily_history_mm)
        linear_7d = sum(daily_history_mm[:7]) if len(daily_history_mm) >= 7 else sum(daily_history_mm)
        api_3 = cls.compute_exponential_api(daily_history_mm, 3, k=0.85)
        api_7 = cls.compute_exponential_api(daily_history_mm, 7, k=0.85)

        return {
            "linear_accum_3d_mm": round(float(linear_3d), 2),
            "exponential_api_3_mm": api_3,
            "discrepancy_3d_mm": round(float(linear_3d - api_3), 2),
            "linear_accum_7d_mm": round(float(linear_7d), 2),
            "exponential_api_7_mm": api_7,
            "discrepancy_7d_mm": round(float(linear_7d - api_7), 2),
            "mathematical_rule": "Linear sum >= Exponential API for all non-negative daily rainfalls when k < 1.0",
            "are_features_equivalent": False,
        }


class AstronomicalCalendarCalculator:
    """Computes deterministic astronomical and calendar features."""

    @staticmethod
    def compute_calendar_features(target_date: Optional[date] = None) -> Dict[str, float]:
        """
        Calculates:
        - day_of_year: 1 to 366
        - month: 1 to 12
        - sin_doy: sin(2 * pi * doy / 365.25)
        - cos_doy: cos(2 * pi * doy / 365.25)
        - is_monsoon: 1.0 if month in [6, 7, 8, 9] else 0.0
        """
        d = target_date or datetime.now(IST_TZ).date()
        doy = float(d.timetuple().tm_yday)
        month_val = float(d.month)
        angle = 2.0 * math.pi * doy / 365.25

        return {
            "day_of_year": doy,
            "month": month_val,
            "sin_doy": round(math.sin(angle), 4),
            "cos_doy": round(math.cos(angle), 4),
            "is_monsoon": 1.0 if d.month in [6, 7, 8, 9] else 0.0,
        }


class DischargeFeatureCalculator:
    """
    Computes the 13 discharge and inflow features from historical or operator-supplied time series.
    """

    @staticmethod
    def compute_discharge_features(
        discharge_history_cumecs: List[float],
        inflow_current_cumecs: Optional[float] = None,
    ) -> Dict[str, Optional[float]]:
        """
        Takes daily downstream discharge history [Q(t), Q(t-1), Q(t-2), ..., Q(t-7)] in m³/s.
        Computes:
        - discharge_current_cumecs: Q(t)
        - discharge_lag_1d_cumecs: Q(t-1)
        - discharge_lag_2d_cumecs: Q(t-2)
        - discharge_lag_3d_cumecs: Q(t-3)
        - discharge_lag_7d_cumecs: Q(t-7)
        - discharge_delta_1d_cumecs: Q(t) - Q(t-1)
        - discharge_delta_ratio_1d: (Q(t) - Q(t-1)) / (Q(t-1) + 1.0)
        - discharge_rolling_mean_3d_cumecs: mean(Q(t), Q(t-1), Q(t-2))
        - discharge_rolling_mean_7d_cumecs: mean(Q(t), ..., Q(t-6))
        - discharge_rolling_max_7d_cumecs: max(Q(t), ..., Q(t-6))
        - discharge_rolling_std_7d_cumecs: sample_std(Q(t), ..., Q(t-6))
        - inflow_current_cumecs: Q_us(t)
        - inflow_release_ratio_current: Q_us(t) / (Q(t) + 1.0)
        """
        if not discharge_history_cumecs:
            return {
                "discharge_current_cumecs": None,
                "discharge_lag_1d_cumecs": None,
                "discharge_lag_2d_cumecs": None,
                "discharge_lag_3d_cumecs": None,
                "discharge_lag_7d_cumecs": None,
                "discharge_delta_1d_cumecs": None,
                "discharge_delta_ratio_1d": None,
                "discharge_rolling_mean_3d_cumecs": None,
                "discharge_rolling_mean_7d_cumecs": None,
                "discharge_rolling_max_7d_cumecs": None,
                "discharge_rolling_std_7d_cumecs": None,
                "inflow_current_cumecs": inflow_current_cumecs,
                "inflow_release_ratio_current": None,
            }

        q0 = float(discharge_history_cumecs[0])
        q1 = float(discharge_history_cumecs[1]) if len(discharge_history_cumecs) > 1 else None
        q2 = float(discharge_history_cumecs[2]) if len(discharge_history_cumecs) > 2 else None
        q3 = float(discharge_history_cumecs[3]) if len(discharge_history_cumecs) > 3 else None
        q7 = float(discharge_history_cumecs[7]) if len(discharge_history_cumecs) > 7 else None

        delta_1d = (q0 - q1) if q1 is not None else None
        delta_ratio_1d = (delta_1d / (q1 + 1.0)) if (delta_1d is not None and q1 is not None) else None

        # 3-day rolling
        if len(discharge_history_cumecs) >= 3:
            r3 = discharge_history_cumecs[:3]
            mean_3d = float(np.mean(r3))
        else:
            mean_3d = None

        # 7-day rolling
        if len(discharge_history_cumecs) >= 7:
            r7 = discharge_history_cumecs[:7]
            mean_7d = float(np.mean(r7))
            max_7d = float(np.max(r7))
            std_7d = float(np.std(r7, ddof=1))
        else:
            mean_7d = None
            max_7d = None
            std_7d = None

        q_us = float(inflow_current_cumecs) if inflow_current_cumecs is not None else None
        inflow_ratio = (q_us / (q0 + 1.0)) if q_us is not None else None

        return {
            "discharge_current_cumecs": round(q0, 2),
            "discharge_lag_1d_cumecs": round(q1, 2) if q1 is not None else None,
            "discharge_lag_2d_cumecs": round(q2, 2) if q2 is not None else None,
            "discharge_lag_3d_cumecs": round(q3, 2) if q3 is not None else None,
            "discharge_lag_7d_cumecs": round(q7, 2) if q7 is not None else None,
            "discharge_delta_1d_cumecs": round(delta_1d, 2) if delta_1d is not None else None,
            "discharge_delta_ratio_1d": round(delta_ratio_1d, 4) if delta_ratio_1d is not None else None,
            "discharge_rolling_mean_3d_cumecs": round(mean_3d, 2) if mean_3d is not None else None,
            "discharge_rolling_mean_7d_cumecs": round(mean_7d, 2) if mean_7d is not None else None,
            "discharge_rolling_max_7d_cumecs": round(max_7d, 2) if max_7d is not None else None,
            "discharge_rolling_std_7d_cumecs": round(std_7d, 2) if std_7d is not None else None,
            "inflow_current_cumecs": round(q_us, 2) if q_us is not None else None,
            "inflow_release_ratio_current": round(inflow_ratio, 4) if inflow_ratio is not None else None,
        }


class HydrometCouplingAuditor:
    """
    Audits the scientific compatibility of connecting live meteorological feeds
    with the existing hathnikund_rf_v1 model.
    """

    @classmethod
    def audit_coupling(
        cls,
        has_live_discharge_telemetry: bool = False,
        has_operator_discharge_inputs: bool = False,
        rainfall_provider_type: str = "NWP_FORECAST_DOWNSCALED",
        spatial_sampling_node_count: int = 20,
    ) -> Dict[str, Any]:
        """
        Evaluates operational feasibility and identifies data/governance barriers.
        """
        missing_inputs: List[str] = []
        covariate_shift_warnings: List[str] = []
        governance_caveats: List[str] = []

        # 1. Telemetry Audit
        if not has_live_discharge_telemetry and not has_operator_discharge_inputs:
            missing_inputs.append(
                "Live Hathnikund Barrage discharge telemetry (HKB D/S and HKB U/S) is UNAVAILABLE in repository."
            )
            missing_inputs.append(
                "Discharge predictors constitute >77% of Random Forest permutation feature importance."
            )

        # 2. Spatial Footprint Audit
        covariate_shift_warnings.append(
            "SPATIAL EXTENT MISMATCH: hathnikund_rf_v1 was trained on 91 IMD grid cells across "
            "[28.0°N–31.0°N, 76.5°E–78.0°E] (including downstream plains). The live grid samples 20 nodes "
            "concentrated in the authentic mountainous catchment [30.3°N–31.45°N, 77.25°E–78.55°E]."
        )
        covariate_shift_warnings.append(
            "OROGRAPHIC BIAS: High-altitude precipitation peaks in the 20-node grid may lead to out-of-distribution "
            "inputs when fed into features trained on regional 91-cell averages."
        )

        # 3. Temporal Alignment Audit
        covariate_shift_warnings.append(
            "TEMPORAL PHASE SHIFT: Open-Meteo daily sums represent 00:00 to 24:00 IST (midnight to midnight). "
            "IMD hydrometric training features strictly represent 08:30 IST to 08:30 IST (8.5-hour phase lead)."
        )

        # 4. Governance Audit
        governance_caveats.append(
            "EXPERIMENTAL BENCHMARK ONLY: Model is strictly gated under Phase 2B Decision Gate."
        )
        governance_caveats.append(
            "Under no circumstances should discharge predictions be labeled as flood warnings or used for Delhi evacuation."
        )

        # Final decision
        if not has_live_discharge_telemetry and not has_operator_discharge_inputs:
            decision = "DISCONNECTED_FOR_AUTONOMOUS_OPERATIONS"
            decision_rationale = (
                "Autonomous live execution is blocked: Hathnikund discharge telemetry is unavailable in real-time, "
                "and substituting median values nullifies 77% of predictive importance. Model may only be evaluated "
                "in research mode with user-provided discharge observations or historical replays."
            )
        else:
            decision = "COUPLED_RESEARCH_BENCHMARK_ONLY"
            decision_rationale = (
                "Operator/telemetry discharge provided. Meteorological inputs can be prepared via non-destructive "
                "adapter. Model evaluation is permitted for research benchmark analysis with explicit covariate shift warnings."
            )

        return {
            "coupling_status": decision,
            "decision_rationale": decision_rationale,
            "has_live_discharge_telemetry": has_live_discharge_telemetry,
            "has_operator_discharge_inputs": has_operator_discharge_inputs,
            "missing_inputs": missing_inputs,
            "covariate_shift_warnings": covariate_shift_warnings,
            "governance_caveats": governance_caveats,
            "promoted_for_operational_disaster_warning": False,
        }


class HydrometFeatureAdapter:
    """
    Non-destructive feature assembly adapter.
    Constructs the exact 23-feature vector conforming to the hathnikund_rf_v1 schema.
    """

    def __init__(self):
        self.allowlist = OPERATIONAL_FEATURE_ALLOWLIST
        self.rolling_acc = Rolling24hAccumulator()
        self.antecedent_calc = HydrometAntecedentCalculator()
        self.calendar_calc = AstronomicalCalendarCalculator()
        self.discharge_calc = DischargeFeatureCalculator()

    def assemble_feature_vector(
        self,
        discharge_features: Dict[str, Optional[float]],
        rainfall_features: Dict[str, Optional[float]],
        calendar_features: Optional[Dict[str, float]] = None,
        target_date: Optional[date] = None,
    ) -> Tuple[Dict[str, float], Dict[str, Any]]:
        """
        Merges discharge, rainfall, and calendar features into the exact 23-feature schema.
        Validates feature order, non-negativity, and returns metadata audit.
        """
        cal = calendar_features or self.calendar_calc.compute_calendar_features(target_date)

        merged: Dict[str, Any] = {}
        merged.update(discharge_features)
        merged.update(rainfall_features)
        merged.update(cal)

        ordered_vector: Dict[str, float] = {}
        missing_flags: List[str] = []

        for feat_name in self.allowlist:
            val = merged.get(feat_name)
            if val is None or (isinstance(val, float) and np.isnan(val)):
                ordered_vector[feat_name] = None
                missing_flags.append(feat_name)
            else:
                f_val = float(val)
                # Validation rules
                if "cumecs" in feat_name and f_val < 0.0:
                    raise FeatureCompatibilityError(f"Discharge feature '{feat_name}' cannot be negative: {f_val}")
                if "rainfall" in feat_name and f_val < 0.0:
                    raise FeatureCompatibilityError(f"Rainfall feature '{feat_name}' cannot be negative: {f_val}")
                ordered_vector[feat_name] = f_val

        audit_meta = {
            "total_feature_count": len(self.allowlist),
            "complete_feature_count": len(self.allowlist) - len(missing_flags),
            "missing_feature_count": len(missing_flags),
            "missing_feature_names": missing_flags,
            "has_missing_features": len(missing_flags) > 0,
        }

        return ordered_vector, audit_meta
