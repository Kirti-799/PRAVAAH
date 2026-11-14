"""
ml/data_processing/schema_contract.py

Modelling Dataset Schema Contract and Verification Validator for PRAVAAH.
Defines the formal data contract that any feature-engineered table must satisfy
before being passed to future statistical or machine-learning models.

DESIGN PRINCIPLES:
- Strict segregation of Predictor, Target, and Metadata columns.
- Temporal causality assertion: prediction_timestamp < target_window_start <= target_window_end.
- Target consistency: if target is unobserved, breach label cannot be 0 (must be null/None).
- No silent corruption or type coercion.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple, Union


# Formal Column Categorisation
PREDICTOR_COLUMNS = [
    "feature_upstream_discharge_cumecs_t",
    "feature_upstream_discharge_cumecs_t_minus_24h",
    "feature_upstream_discharge_cumecs_t_minus_48h",
    "feature_upstream_discharge_change_24h",
    "feature_catchment_rainfall_actual_mm_t",
    "feature_local_stage_m_t",  # Only if local stage at time <= t is available
]

TARGET_COLUMNS = [
    "target_window_start_utc",
    "target_window_end_utc",
    "target_max_stage_m",
    "target_danger_breach",
    "is_target_observed",
]

METADATA_COLUMNS = [
    "prediction_timestamp_utc",
    "upstream_station_name",
    "downstream_station_name",
    "lead_time_hours",
    "prediction_window_hours",
    "danger_threshold_m",
    "data_source_upstream",
    "data_source_downstream",
]

ALL_CONTRACT_COLUMNS = PREDICTOR_COLUMNS + TARGET_COLUMNS + METADATA_COLUMNS


class ModellingDatasetContractValidator:
    """Validates records and tables against the formal PRAVAAH ML dataset contract."""

    @staticmethod
    def _parse_utc_iso(ts_str: Any) -> Optional[datetime]:
        if not ts_str or not isinstance(ts_str, str):
            return None
        try:
            dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            return dt.astimezone(timezone.utc)
        except ValueError:
            return None

    def validate_record(self, record: Dict[str, Any], record_idx: int = 0) -> List[str]:
        """Validate a single record against schema rules, returning list of violations."""
        errors: List[str] = []

        # 1. Required Metadata & Timestamps
        p_ts_str = record.get("prediction_timestamp_utc")
        p_dt = self._parse_utc_iso(p_ts_str)
        if p_dt is None:
            errors.append(f"Row {record_idx}: 'prediction_timestamp_utc' is missing or not a valid ISO 8601 UTC string.")

        tw_start_str = record.get("target_window_start_utc")
        tw_start_dt = self._parse_utc_iso(tw_start_str)
        if tw_start_dt is None:
            errors.append(f"Row {record_idx}: 'target_window_start_utc' is missing or not a valid ISO 8601 UTC string.")

        tw_end_str = record.get("target_window_end_utc")
        tw_end_dt = self._parse_utc_iso(tw_end_str)
        if tw_end_dt is None:
            errors.append(f"Row {record_idx}: 'target_window_end_utc' is missing or not a valid ISO 8601 UTC string.")

        # 2. Temporal Causality Check
        if p_dt and tw_start_dt and tw_end_dt:
            if not (p_dt < tw_start_dt <= tw_end_dt):
                errors.append(
                    f"Row {record_idx}: Temporal causality violation. "
                    f"Expected prediction_ts ({p_dt}) < window_start ({tw_start_dt}) <= window_end ({tw_end_dt})."
                )

        # 3. Predictor Range and Causality Validations
        q_t = record.get("feature_upstream_discharge_cumecs_t")
        if q_t is not None:
            if not isinstance(q_t, (int, float)) or q_t < 0:
                errors.append(f"Row {record_idx}: 'feature_upstream_discharge_cumecs_t' must be non-negative numeric (found {q_t}).")

        q_24h = record.get("feature_upstream_discharge_cumecs_t_minus_24h")
        if q_24h is not None:
            if not isinstance(q_24h, (int, float)) or q_24h < 0:
                errors.append(f"Row {record_idx}: 'feature_upstream_discharge_cumecs_t_minus_24h' must be non-negative numeric.")

        rain_t = record.get("feature_catchment_rainfall_actual_mm_t")
        if rain_t is not None:
            if not isinstance(rain_t, (int, float)) or rain_t < 0:
                errors.append(f"Row {record_idx}: 'feature_catchment_rainfall_actual_mm_t' must be non-negative numeric (found {rain_t}).")

        # 4. Target Consistency Checks
        is_observed = record.get("is_target_observed")
        if is_observed is None or not isinstance(is_observed, bool):
            errors.append(f"Row {record_idx}: 'is_target_observed' must be an explicit boolean (True or False).")

        breach = record.get("target_danger_breach")
        max_stage = record.get("target_max_stage_m")

        if is_observed is False:
            # If target was unobserved, breach must NOT be 0 (must be None/null)
            if breach is not None:
                errors.append(
                    f"Row {record_idx}: Target leakage / distortion. "
                    f"'is_target_observed' is False but 'target_danger_breach' is {breach} (must be None)."
                )
            if max_stage is not None:
                errors.append(
                    f"Row {record_idx}: 'is_target_observed' is False but 'target_max_stage_m' is {max_stage} (must be None)."
                )
        elif is_observed is True:
            if breach not in (0, 1):
                errors.append(f"Row {record_idx}: 'target_danger_breach' must be 0 or 1 when target is observed (found {breach}).")
            if max_stage is None or not isinstance(max_stage, (int, float)):
                errors.append(f"Row {record_idx}: 'target_max_stage_m' must be a valid float when target is observed.")

        return errors

    def validate_dataset(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate an entire collection of records against the contract."""
        if not records:
            return {
                "is_valid": False,
                "total_rows": 0,
                "error_count": 1,
                "errors": ["Dataset is empty."],
            }

        all_errors: List[str] = []
        for idx, row in enumerate(records):
            row_errors = self.validate_record(row, record_idx=idx)
            all_errors.extend(row_errors)

        return {
            "is_valid": len(all_errors) == 0,
            "total_rows": len(records),
            "error_count": len(all_errors),
            "errors": all_errors[:25],  # Cap output at first 25 violations
        }
