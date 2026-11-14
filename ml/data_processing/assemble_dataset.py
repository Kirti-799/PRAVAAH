"""
ml/data_processing/assemble_dataset.py

End-to-End Dataset Assembly and Feature-Target Coupling Pipeline for PRAVAAH.
Couples:
1. Historical Upstream Hydrological Discharge (Hathnikund Barrage HKB D/S)
2. Historical Catchment Gridded Rainfall (IMD 0.25-deg regional summary)
3. Downstream Water Level Target Observations (Delhi Old Railway Bridge CWC 028-MDD)

STRICT MODELLING INTEGRITY PRINCIPLES:
- Predictor features at forecast issue time t must ONLY use information from <= t.
- Rainfall gating respects IMD 24h accumulation cut-off (08:30 IST / 03:00 UTC).
- Forward prediction window is strictly [t + 24h, t + 48h].
- If downstream target data is missing or unobserved, is_target_observed=False and
  target_danger_breach=None. Unobserved windows are NEVER treated as negative (0) labels!
- Zero forward-filling across unobserved historical gaps.
- Full compliance verification against ModellingDatasetContractValidator.
"""

import csv
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union

from ml.data_processing.schema_contract import (
    ModellingDatasetContractValidator,
    PREDICTOR_COLUMNS,
    TARGET_COLUMNS,
    METADATA_COLUMNS,
)


class DatasetAssembler:
    """Assembles decoupled predictor and target datasets into a contract-compliant modelling matrix."""

    COMMON_NULLS = {"", "na", "n/a", "nan", "null", "none", "-999", "-999.0", "-9999", "-9999.0"}

    def __init__(
        self,
        lead_time_hours: int = 48,
        prediction_window_hours: int = 24,
        danger_threshold_m: float = 205.33,
    ):
        """
        Args:
            lead_time_hours: Maximum forward prediction horizon (e.g. 48h).
            prediction_window_hours: Target window duration (e.g. 24h, yielding [t+24h, t+48h]).
            danger_threshold_m: Official CWC Danger Mark at Delhi Old Railway Bridge.
        """
        self.lead_time_hours = lead_time_hours
        self.prediction_window_hours = prediction_window_hours
        self.danger_threshold_m = danger_threshold_m
        self.validator = ModellingDatasetContractValidator()

    @staticmethod
    def parse_utc_timestamp(ts_str: Any) -> Optional[datetime]:
        """Parse varied date/time strings to timezone-aware UTC datetime."""
        if ts_str is None:
            return None
        clean = str(ts_str).strip()
        if not clean or clean.lower() in DatasetAssembler.COMMON_NULLS:
            return None

        try:
            dt = datetime.fromisoformat(clean.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except ValueError:
            pass

        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%d-%m-%Y %H:%M",
            "%d/%m/%Y %H:%M",
            "%Y-%m-%d",
            "%d-%m-%Y",
            "%d/%m/%Y",
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(clean, fmt)
                return dt.replace(tzinfo=timezone.utc)
            except ValueError:
                pass
        return None

    def assemble(
        self,
        upstream_records: List[Dict[str, Any]],
        rainfall_records: Optional[List[Dict[str, Any]]] = None,
        downstream_records: Optional[List[Dict[str, Any]]] = None,
        upstream_role_filter: str = "downstream_release",
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Assemble coupled predictor and target records from raw/processed component lists.

        Returns:
            Tuple of (assembled_records, assembly_audit_summary).
        """
        # 1. Parse and index downstream observations by UTC timestamp
        downstream_by_time: Dict[datetime, float] = {}
        downstream_duplicates = 0
        if downstream_records:
            for r in downstream_records:
                ts = r.get("timestamp_utc") or r.get("timestamp") or r.get("date")
                dt = self.parse_utc_timestamp(ts)
                if dt is None:
                    continue

                stage_val = r.get("water_level_m") or r.get("stage_m") or r.get("water_level")
                if stage_val is None or str(stage_val).strip().lower() in self.COMMON_NULLS:
                    continue
                try:
                    stage_f = float(stage_val)
                except ValueError:
                    continue

                if dt in downstream_by_time:
                    downstream_duplicates += 1
                downstream_by_time[dt] = stage_f

        # 2. Parse and index rainfall records by date string YYYY-MM-DD
        rainfall_by_date: Dict[str, float] = {}
        if rainfall_records:
            for r in rainfall_records:
                d_val = r.get("date") or r.get("timestamp_utc")
                dt = self.parse_utc_timestamp(d_val)
                if dt is None:
                    continue
                date_key = dt.strftime("%Y-%m-%d")

                rain_val = (
                    r.get("rainfall_spatial_mean_mm")
                    or r.get("rainfall_actual_mm")
                    or r.get("rainfall_daily")
                )
                if rain_val is not None and str(rain_val).strip().lower() not in self.COMMON_NULLS:
                    try:
                        rainfall_by_date[date_key] = float(rain_val)
                    except ValueError:
                        pass

        # 3. Filter and chronologically sort upstream discharge records
        upstream_sorted: List[Tuple[datetime, float, Dict[str, Any]]] = []
        for r in upstream_records:
            role = r.get("role", "")
            if upstream_role_filter and role and role != upstream_role_filter:
                continue

            ts = r.get("timestamp_utc") or r.get("timestamp") or r.get("date")
            dt = self.parse_utc_timestamp(ts)
            if dt is None:
                continue

            q_val = (
                r.get("discharge_cumecs")
                or r.get("discharge")
                or r.get("Manual Daily River Water Discharge (m3/sec)")
            )
            if q_val is None or str(q_val).strip().lower() in self.COMMON_NULLS:
                continue
            try:
                q_f = float(q_val)
            except ValueError:
                continue

            upstream_sorted.append((dt, q_f, r))

        upstream_sorted.sort(key=lambda x: x[0])

        assembled_records: List[Dict[str, Any]] = []
        observed_target_count = 0
        unobserved_target_count = 0
        positive_breaches = 0
        validation_errors: List[str] = []

        for idx, (t, q_current, raw_meta) in enumerate(upstream_sorted):
            # Compute past lag features at t - 24h and t - 48h (strictly past <= t)
            q_lag_24h: Optional[float] = None
            q_lag_48h: Optional[float] = None

            t_24h_prior = t - timedelta(hours=24)
            t_48h_prior = t - timedelta(hours=48)

            for past_t, past_q, _ in upstream_sorted[max(0, idx - 10) : idx]:
                if abs((past_t - t_24h_prior).total_seconds()) <= 3600:
                    q_lag_24h = past_q
                if abs((past_t - t_48h_prior).total_seconds()) <= 3600:
                    q_lag_48h = past_q

            q_change_24h = round(q_current - q_lag_24h, 2) if q_lag_24h is not None else None

            # Rainfall at t: Respect IMD 08:30 IST (03:00 UTC) observation cut-off
            if t.hour < 3:
                effective_rain_date = (t - timedelta(days=1)).strftime("%Y-%m-%d")
            else:
                effective_rain_date = t.strftime("%Y-%m-%d")
            rain_t = rainfall_by_date.get(effective_rain_date)

            # Local downstream stage at t (only if available at or before t)
            local_stage_t = downstream_by_time.get(t)

            # Define forward target window: [t + 24h, t + 48h]
            target_start = t + timedelta(hours=max(0, self.lead_time_hours - self.prediction_window_hours))
            target_end = t + timedelta(hours=self.lead_time_hours)

            # Downstream observations in target window
            future_stages = [
                stage for ds_t, stage in downstream_by_time.items()
                if target_start <= ds_t <= target_end
            ]

            if not future_stages:
                is_observed = False
                unobserved_target_count += 1
                target_max_stage = None
                target_danger_breach = None
            else:
                is_observed = True
                observed_target_count += 1
                target_max_stage = round(max(future_stages), 2)
                target_danger_breach = 1 if target_max_stage >= self.danger_threshold_m else 0
                if target_danger_breach == 1:
                    positive_breaches += 1

            record: Dict[str, Any] = {
                # Predictors
                "feature_upstream_discharge_cumecs_t": q_current,
                "feature_upstream_discharge_cumecs_t_minus_24h": q_lag_24h,
                "feature_upstream_discharge_cumecs_t_minus_48h": q_lag_48h,
                "feature_upstream_discharge_change_24h": q_change_24h,
                "feature_catchment_rainfall_actual_mm_t": rain_t,
                "feature_local_stage_m_t": local_stage_t,
                # Targets
                "target_window_start_utc": target_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "target_window_end_utc": target_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "target_max_stage_m": target_max_stage,
                "target_danger_breach": target_danger_breach,
                "is_target_observed": is_observed,
                # Metadata
                "prediction_timestamp_utc": t.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "upstream_station_name": raw_meta.get("station_name", "HKB D/S"),
                "downstream_station_name": "Delhi Old Railway Bridge (028-MDD)",
                "lead_time_hours": self.lead_time_hours,
                "prediction_window_hours": self.prediction_window_hours,
                "danger_threshold_m": self.danger_threshold_m,
                "data_source_upstream": "Haryana I&WRD (Hathnikund Barrage)",
                "data_source_downstream": "CWC / Delhi I&FC (Station 028-MDD)",
            }

            # Enforce schema contract
            row_errors = self.validator.validate_record(record, record_idx=idx)
            if row_errors:
                validation_errors.extend(row_errors)

            assembled_records.append(record)

        is_production_ready = (
            len(assembled_records) > 0
            and len(validation_errors) == 0
            and observed_target_count > 0
        )

        readiness_status = (
            "READY_FOR_SUPERVISED_TRAINING"
            if is_production_ready
            else "INCOMPLETE_PENDING_TARGET_GROUND_TRUTH"
        )

        summary = {
            "total_assembled_records": len(assembled_records),
            "observed_target_windows": observed_target_count,
            "unobserved_target_windows": unobserved_target_count,
            "positive_danger_breaches": positive_breaches,
            "duplicate_downstream_timestamps": downstream_duplicates,
            "contract_validation_errors_count": len(validation_errors),
            "contract_validation_errors": validation_errors[:20],
            "dataset_readiness_status": readiness_status,
            "is_ready_for_ml_training": is_production_ready,
            "start_prediction_utc": assembled_records[0]["prediction_timestamp_utc"] if assembled_records else None,
            "end_prediction_utc": assembled_records[-1]["prediction_timestamp_utc"] if assembled_records else None,
        }

        return assembled_records, summary

    def assemble_to_csv(
        self,
        upstream_csv_path: Union[str, Path],
        rainfall_csv_path: Optional[Union[str, Path]],
        downstream_csv_path: Optional[Union[str, Path]],
        output_csv_path: Union[str, Path],
        upstream_role_filter: str = "downstream_release",
    ) -> Dict[str, Any]:
        """Load component CSV files, assemble matrix, and export verified table."""
        up_path = Path(upstream_csv_path)
        out_path = Path(output_csv_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        upstream_records = []
        with open(up_path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                upstream_records.append(row)

        rainfall_records = []
        if rainfall_csv_path and Path(rainfall_csv_path).exists():
            with open(rainfall_csv_path, mode="r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    rainfall_records.append(row)

        downstream_records = []
        if downstream_csv_path and Path(downstream_csv_path).exists():
            with open(downstream_csv_path, mode="r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    downstream_records.append(row)

        assembled, summary = self.assemble(
            upstream_records=upstream_records,
            rainfall_records=rainfall_records,
            downstream_records=downstream_records,
            upstream_role_filter=upstream_role_filter,
        )

        if assembled:
            fieldnames = list(assembled[0].keys())
            with open(out_path, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(assembled)

        summary["output_csv_path"] = str(out_path)
        return summary
