"""
ml/data_processing/align_data.py

Reproducible Temporal Alignment and Feature Coupling Pipeline for PRAVAAH.
Couples upstream hydrological observations (Hathnikund Barrage) with
downstream target stage observations (Delhi Old Railway Bridge) and
catchment precipitation indices.

STRICT TARGET LEAKAGE SAFEGUARDS:
- At prediction time t, no feature may contain information from time > t.
- Target labels represent conditions strictly within the forward-looking prediction horizon: [t + lead_time_min, t + lead_time_max].
- No interpolation or forward-filling across unobserved historical gaps.
"""

import csv
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union


class TemporalDataAligner:
    """Aligns multi-source hydrological and meteorological time-series without target leakage."""

    COMMON_NULL_SENTINELS = {"", "na", "n/a", "nan", "null", "none", "-999", "-999.0", "-9999"}

    def __init__(
        self,
        lead_time_hours: int = 48,
        prediction_window_hours: int = 24,
        danger_threshold_m: float = 205.33,
    ):
        """
        Args:
            lead_time_hours: Forward lead time (e.g. 48 hours for Hathnikund-to-Delhi lag).
            prediction_window_hours: Horizon duration after lead time (e.g. [t+24, t+48]).
            danger_threshold_m: Official CWC Danger Mark at target cross-section.
        """
        self.lead_time_hours = lead_time_hours
        self.prediction_window_hours = prediction_window_hours
        self.danger_threshold_m = danger_threshold_m

    @staticmethod
    def parse_iso_or_custom_timestamp(ts_str: str) -> Optional[datetime]:
        """Parse various date/datetime string formats to timezone-aware UTC datetime."""
        clean = ts_str.strip()
        if not clean or clean.lower() in TemporalDataAligner.COMMON_NULL_SENTINELS:
            return None

        try:
            dt = datetime.fromisoformat(clean.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except ValueError:
            pass

        formats = [
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%d-%m-%Y %H:%M",
            "%d/%m/%Y %H:%M",
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

    def align_series(
        self,
        upstream_records: List[Dict[str, Any]],
        downstream_records: List[Dict[str, Any]],
        rainfall_records: Optional[List[Dict[str, Any]]] = None,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Align upstream predictor time series with downstream target time series.

        Each record in upstream_records must have:
            - 'timestamp' or 'timestamp_utc': string/datetime
            - 'discharge_cumecs': float (upstream flow)

        Each record in downstream_records must have:
            - 'timestamp' or 'timestamp_utc': string/datetime
            - 'stage_m': float (water level in metres)
        """
        # 1. Parse and index downstream observations by rounded UTC timestamp
        downstream_by_time: Dict[datetime, float] = {}
        duplicate_downstream = 0
        for r in downstream_records:
            ts = r.get("timestamp_utc") or r.get("timestamp") or r.get("date")
            dt = ts if isinstance(ts, datetime) else self.parse_iso_or_custom_timestamp(str(ts))
            if dt is None:
                continue

            stage_val = r.get("stage_m") or r.get("water_level") or r.get("river_stage_orb")
            if stage_val is None or str(stage_val).strip().lower() in self.COMMON_NULL_SENTINELS:
                continue
            try:
                stage_f = float(stage_val)
            except ValueError:
                continue

            if dt in downstream_by_time:
                duplicate_downstream += 1
            downstream_by_time[dt] = stage_f

        # 2. Parse rainfall records by date if provided
        rainfall_by_date: Dict[str, float] = {}
        if rainfall_records:
            for r in rainfall_records:
                d_str = r.get("date") or r.get("timestamp")
                dt = d_str if isinstance(d_str, datetime) else self.parse_iso_or_custom_timestamp(str(d_str))
                if dt is None:
                    continue
                date_key = dt.strftime("%Y-%m-%d")
                rain_val = r.get("rainfall_actual_mm") or r.get("rainfall_daily") or r.get("rainfall_amount")
                if rain_val is not None and str(rain_val).strip().lower() not in self.COMMON_NULL_SENTINELS:
                    try:
                        rainfall_by_date[date_key] = float(rain_val)
                    except ValueError:
                        pass

        # 3. Iterate through upstream records at prediction time t
        aligned_dataset: List[Dict[str, Any]] = []
        upstream_sorted = []
        for r in upstream_records:
            ts = r.get("timestamp_utc") or r.get("timestamp") or r.get("date")
            dt = ts if isinstance(ts, datetime) else self.parse_iso_or_custom_timestamp(str(ts))
            if dt is None:
                continue
            q_val = r.get("discharge_cumecs") or r.get("discharge") or r.get("Manual Daily River Water Discharge (m3/sec)")
            if q_val is None or str(q_val).strip().lower() in self.COMMON_NULL_SENTINELS:
                continue
            try:
                q_f = float(q_val)
            except ValueError:
                continue
            upstream_sorted.append((dt, q_f, r))

        upstream_sorted.sort(key=lambda x: x[0])

        missing_target_count = 0
        target_positive_events = 0

        for idx, (t, q_current, raw_meta) in enumerate(upstream_sorted):
            # Compute past lag features (strictly past or current t)
            # t_minus_1_day: look for upstream record 24h prior
            q_lag_24h: Optional[float] = None
            q_lag_48h: Optional[float] = None

            t_24h_prior = t - timedelta(hours=24)
            t_48h_prior = t - timedelta(hours=48)

            for past_t, past_q, _ in upstream_sorted[max(0, idx - 10):idx]:
                if abs((past_t - t_24h_prior).total_seconds()) <= 3600:
                    q_lag_24h = past_q
                if abs((past_t - t_48h_prior).total_seconds()) <= 3600:
                    q_lag_48h = past_q

            # Rainfall at t: Respect IMD 24h accumulation cut-off (08:30 IST == 03:00 UTC).
            # If prediction time t is before 03:00 UTC on date D, the observation window
            # for date D is not yet complete; the latest available completed rainfall is date D-1.
            if t.hour < 3:
                effective_rain_date = (t - timedelta(days=1)).strftime("%Y-%m-%d")
            else:
                effective_rain_date = t.strftime("%Y-%m-%d")
            rain_t = rainfall_by_date.get(effective_rain_date)

            # Define forward target window: [t + lead_time - window, t + lead_time]
            # e.g., lead_time=48, window=24 => [t + 24h, t + 48h]
            target_start = t + timedelta(hours=max(0, self.lead_time_hours - self.prediction_window_hours))
            target_end = t + timedelta(hours=self.lead_time_hours)

            # Query downstream observations in the forward target window
            future_stages = [
                stage for ds_t, stage in downstream_by_time.items()
                if target_start <= ds_t <= target_end
            ]

            if not future_stages:
                # No target ground truth available in future window
                missing_target_count += 1
                target_stage_max = None
                target_flood_breach = None
            else:
                target_stage_max = max(future_stages)
                target_flood_breach = 1 if target_stage_max >= self.danger_threshold_m else 0
                if target_flood_breach == 1:
                    target_positive_events += 1

            aligned_record = {
                "prediction_timestamp_utc": t.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "upstream_station": raw_meta.get("station_name", "HKB"),
                "feature_discharge_cumecs_t": q_current,
                "feature_discharge_cumecs_t_minus_24h": q_lag_24h,
                "feature_discharge_cumecs_t_minus_48h": q_lag_48h,
                "feature_rainfall_actual_mm_t": rain_t,
                "target_window_start_utc": target_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "target_window_end_utc": target_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "target_max_stage_m": target_stage_max,
                "target_danger_breach": target_flood_breach,
                "is_target_observed": target_flood_breach is not None,
            }
            aligned_dataset.append(aligned_record)

        summary = {
            "total_aligned_records": len(aligned_dataset),
            "observed_targets_count": len(aligned_dataset) - missing_target_count,
            "missing_targets_count": missing_target_count,
            "target_positive_breaches": target_positive_events,
            "duplicate_downstream_timestamps": duplicate_downstream,
            "lead_time_hours": self.lead_time_hours,
            "prediction_window_hours": self.prediction_window_hours,
            "danger_threshold_m": self.danger_threshold_m,
        }

        return aligned_dataset, summary


def align_datasets_to_csv(
    upstream_csv_path: Union[str, Path],
    downstream_csv_path: Union[str, Path],
    output_csv_path: Union[str, Path],
    rainfall_csv_path: Optional[Union[str, Path]] = None,
    lead_time_hours: int = 48,
    danger_threshold_m: float = 205.33,
) -> Dict[str, Any]:
    """Load, align, and serialize coupled observations to processed CSV."""
    up_path = Path(upstream_csv_path)
    down_path = Path(downstream_csv_path)
    out_path = Path(output_csv_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    upstream_records = []
    with open(up_path, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            upstream_records.append(row)

    downstream_records = []
    with open(down_path, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            downstream_records.append(row)

    rainfall_records = []
    if rainfall_csv_path and Path(rainfall_csv_path).exists():
        with open(rainfall_csv_path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rainfall_records.append(row)

    aligner = TemporalDataAligner(
        lead_time_hours=lead_time_hours,
        danger_threshold_m=danger_threshold_m
    )
    aligned_data, summary = aligner.align_series(
        upstream_records,
        downstream_records,
        rainfall_records
    )

    if aligned_data:
        fieldnames = list(aligned_data[0].keys())
        with open(out_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(aligned_data)

    summary["output_csv_path"] = str(out_path)
    return summary
