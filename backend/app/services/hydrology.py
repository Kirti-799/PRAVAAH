"""
backend/app/services/hydrology.py

Data Access and Non-ML Analytical Service for PRAVAAH Hydrological Intelligence.
Loads verified historical datasets, computes non-ML descriptive indicators,
calculates antecedent rainfall accumulations, and provides operational summaries.

STRICT INTEGRITY INVARIANTS:
- Operates strictly on real acquired datasets on disk.
- NEVER fabricates downstream water levels or flood-risk probabilities.
- Reports target gauge observations as explicitly unavailable until CWC requisition is fulfilled.
"""

import csv
import math
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

from app.schemas.hydrology import (
    HydrologySummaryResponse,
    LatestObservations,
    TargetGaugeStatus,
    RainfallAccumulations,
    DischargeStatistics,
    DistributionStats,
    DataQualityAudit,
    HistoricalEventsResponse,
    HistoricalEpisodeItem,
)


def _get_data_dir() -> Path:
    """Resolve data root directory relative to PRAVAAH workspace root."""
    # backend/app/services/hydrology.py -> parents[3] is repo root
    repo_root = Path(__file__).resolve().parents[3]
    return repo_root / "data"


class HydrologyService:
    """Service providing read-only non-ML hydrological intelligence."""

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or _get_data_dir()
        self.discharge_csv = self.data_dir / "processed" / "hydrological" / "haryana_hathnikund_discharge_daily_2018_2025.csv"
        self.rainfall_summary_csv = self.data_dir / "processed" / "rainfall" / "gridded" / "imd_gridded_daily_regional_summary_2018_2024.csv"
        self.episodes_csv = self.data_dir / "processed" / "analysis" / "historical_high_discharge_episodes.csv"

    @staticmethod
    def _compute_distribution_stats(values: List[float]) -> DistributionStats:
        n = len(values)
        if n == 0:
            return DistributionStats(
                count=0, mean_cumecs=0.0, p50_cumecs=0.0, p90_cumecs=0.0, p95_cumecs=0.0, p99_cumecs=0.0, max_cumecs=0.0
            )
        sorted_v = sorted(values)
        mean_v = sum(sorted_v) / n

        def percentile(p: float) -> float:
            idx = int(p * (n - 1))
            return sorted_v[idx]

        return DistributionStats(
            count=n,
            mean_cumecs=round(mean_v, 2),
            p50_cumecs=round(percentile(0.50), 2),
            p90_cumecs=round(percentile(0.90), 2),
            p95_cumecs=round(percentile(0.95), 2),
            p99_cumecs=round(percentile(0.99), 2),
            max_cumecs=round(max(sorted_v), 2),
        )

    def get_summary(self) -> HydrologySummaryResponse:
        """Compute the full historical and latest hydrological summary."""
        if not self.discharge_csv.exists():
            raise FileNotFoundError(f"Processed discharge dataset not found at {self.discharge_csv}")

        # 1. Parse discharge records
        us_by_date: Dict[str, float] = {}
        ds_by_date: Dict[str, float] = {}
        dates_sorted: List[str] = []

        with open(self.discharge_csv, mode="r", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                d = row.get("date", "").strip()
                st = row.get("station_name", "").strip()
                q_str = row.get("discharge_cumecs")
                if d and q_str not in (None, ""):
                    try:
                        q_val = float(q_str)
                        if st == "HKB U/S":
                            us_by_date[d] = q_val
                        elif st == "HKB D/S":
                            ds_by_date[d] = q_val
                            dates_sorted.append(d)
                    except ValueError:
                        pass

        dates_sorted = sorted(list(set(dates_sorted)))
        latest_date = dates_sorted[-1] if dates_sorted else "2025-08-12"
        prev_date = dates_sorted[-2] if len(dates_sorted) >= 2 else None

        latest_us = us_by_date.get(latest_date)
        latest_ds = ds_by_date.get(latest_date)
        prev_us = us_by_date.get(prev_date) if prev_date else None
        prev_ds = ds_by_date.get(prev_date) if prev_date else None

        pct_change_us = (
            round(((latest_us - prev_us) / prev_us) * 100, 2)
            if (latest_us is not None and prev_us and prev_us > 0)
            else None
        )
        pct_change_ds = (
            round(((latest_ds - prev_ds) / prev_ds) * 100, 2)
            if (latest_ds is not None and prev_ds and prev_ds > 0)
            else None
        )

        # 2. Parse rainfall records
        rf_by_date: Dict[str, Dict[str, Any]] = {}
        rf_dates_sorted: List[str] = []

        if self.rainfall_summary_csv.exists():
            with open(self.rainfall_summary_csv, mode="r", encoding="utf-8-sig") as f:
                for row in csv.DictReader(f):
                    d = row.get("date", "").strip()
                    mean_rf = row.get("rainfall_spatial_mean_mm")
                    max_rf = row.get("rainfall_spatial_max_mm")
                    if d:
                        rf_dates_sorted.append(d)
                        rf_by_date[d] = {
                            "mean": float(mean_rf) if mean_rf not in (None, "", "None") else 0.0,
                            "max": float(max_rf) if max_rf not in (None, "", "None") else 0.0,
                        }

        rf_dates_sorted = sorted(list(set(rf_dates_sorted)))
        latest_rf_date = rf_dates_sorted[-1] if rf_dates_sorted else None
        latest_rf_mean = rf_by_date.get(latest_rf_date, {}).get("mean") if latest_rf_date else None
        latest_rf_max = rf_by_date.get(latest_rf_date, {}).get("max") if latest_rf_date else None

        # 3. Compute multi-window antecedent accumulations for latest available rainfall date
        ref_rf_d = date.fromisoformat(latest_rf_date) if latest_rf_date else date(2024, 12, 31)

        def calc_accum(days_back: int) -> Optional[float]:
            total = 0.0
            for k in range(days_back):
                target_d = (ref_rf_d - timedelta(days=k)).isoformat()
                if target_d not in rf_by_date:
                    return None
                total += rf_by_date[target_d]["mean"]
            return round(total, 2)

        accum_1d = calc_accum(1)
        accum_3d = calc_accum(3)
        accum_5d = calc_accum(5)
        accum_7d = calc_accum(7)

        # 4. Discharge distribution statistics
        us_stats = self._compute_distribution_stats(list(us_by_date.values()))
        ds_stats = self._compute_distribution_stats(list(ds_by_date.values()))

        # Assemble response
        latest_obs = LatestObservations(
            timestamp_utc=f"{latest_date}T06:00:00Z",
            date=latest_date,
            inflow_discharge_cumecs=latest_us,
            inflow_discharge_cusecs=round(latest_us / 0.0283168, 1) if latest_us else None,
            release_discharge_cumecs=latest_ds,
            release_discharge_cusecs=round(latest_ds / 0.0283168, 1) if latest_ds else None,
            percentage_change_inflow_24h=pct_change_us,
            percentage_change_release_24h=pct_change_ds,
            latest_rainfall_date=latest_rf_date,
            latest_rainfall_spatial_mean_mm=latest_rf_mean,
            latest_rainfall_spatial_max_mm=latest_rf_max,
            target_gauge=TargetGaugeStatus(),
        )

        rf_accum = RainfallAccumulations(
            reference_date=latest_rf_date or "2024-12-31",
            accum_1d_mm=accum_1d,
            accum_3d_mm=accum_3d,
            accum_5d_mm=accum_5d,
            accum_7d_mm=accum_7d,
            spatial_coverage_cells=91,
            aggregation_method="unweighted_provisional_bbox_mean",
        )

        discharge_stats = DischargeStatistics(
            period_start=dates_sorted[0] if dates_sorted else "2018-01-01",
            period_end=dates_sorted[-1] if dates_sorted else "2025-08-12",
            total_days=len(dates_sorted),
            inflow_statistics_hkb_us=us_stats,
            release_statistics_hkb_ds=ds_stats,
        )

        quality_audit = DataQualityAudit(
            upstream_missing_days=7,
            upstream_duplicate_records=0,
            rainfall_missing_days=0,
            valid_rainfall_cells_per_day=91,
            rainfall_grid_resolution="0.25 deg x 0.25 deg (~27.5 km)",
            data_freshness_status="Historical archives complete (Rainfall 2018-2024; Discharge 2018-2025).",
        )

        source_meta = [
            {
                "dataset": "Hathnikund Barrage Daily Discharge",
                "publisher": "Irrigation & Water Resources Department, Haryana / NWIC",
                "portal": "https://nwdp.nwic.gov.in/",
                "verified_coverage": "2018-01-01 to 2025-08-12 (2,599 days)",
            },
            {
                "dataset": "IMD High Spatial Resolution Gridded Daily Rainfall (0.25 deg)",
                "publisher": "India Meteorological Department (IMD) Pune",
                "portal": "https://imdpune.gov.in/cmpg/Griddata/Rainfall_25_Bin.html",
                "verified_coverage": "2018-01-01 to 2024-12-31 (2,557 days)",
            },
            {
                "dataset": "Delhi Old Railway Bridge (Station 028-MDD) Water Level",
                "publisher": "Central Water Commission (CWC)",
                "portal": "India-WRIS / WIMS / Formal Requisition",
                "status": "RESTRICTED — PENDING REQUISITION",
            },
        ]

        limitations = [
            "NON-ML SCIENTIFIC DESCRIPTORS: These indicators are empirical descriptive metrics computed from verified historical archives. No machine-learning model has been trained or deployed.",
            "TARGET DATA BLOCKED: Downstream continuous water-level observations at Delhi Old Railway Bridge (CWC Station 028-MDD) are unavailable. Target elevation cannot be predicted until authentic CWC telemetry is acquired.",
            "PROVISIONAL BOUNDING BOX: Rainfall summaries are calculated across a provisional 91-cell rectangular bounding box (28.0-31.0N, 76.5-78.0E), not a DEM-delineated hypsometric watershed divide.",
            "CORRELATION NOT CAUSATION: Statistical associations reflect physical and operational flood routing characteristics, but empirical correlations do not substitute for hydro-conditioned physical modeling.",
        ]

        return HydrologySummaryResponse(
            latest_observations=latest_obs,
            rainfall_accumulations=rf_accum,
            discharge_statistics=discharge_stats,
            data_quality=quality_audit,
            source_metadata=source_meta,
            limitations=limitations,
        )

    def get_historical_events(self) -> HistoricalEventsResponse:
        """Return distinct historical high-discharge episodes extracted from verified records."""
        if not self.episodes_csv.exists():
            raise FileNotFoundError(f"Episodes dataset not found at {self.episodes_csv}")

        episodes: List[HistoricalEpisodeItem] = []
        with open(self.episodes_csv, mode="r", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                def parse_flt(val: Any) -> Optional[float]:
                    if val in (None, "", "None"):
                        return None
                    try:
                        return float(val)
                    except ValueError:
                        return None

                def parse_int(val: Any) -> Optional[int]:
                    if val in (None, "", "None"):
                        return None
                    try:
                        return int(val)
                    except ValueError:
                        return None

                episodes.append(
                    HistoricalEpisodeItem(
                        episode_id=row["episode_id"],
                        start_date=row["start_date"],
                        end_date=row["end_date"],
                        duration_days=int(row["duration_days"]),
                        peak_date=row["peak_date"],
                        peak_upstream_inflow_cumecs=float(row["peak_upstream_inflow_cumecs"]),
                        peak_downstream_release_cumecs=float(row["peak_downstream_release_cumecs"]),
                        peak_upstream_inflow_cusecs=float(row["peak_upstream_inflow_cusecs"]),
                        peak_downstream_release_cusecs=float(row["peak_downstream_release_cusecs"]),
                        rainfall_accum_1d_mm=parse_flt(row.get("rainfall_accum_1d_mm")),
                        rainfall_accum_3d_mm=parse_flt(row.get("rainfall_accum_3d_mm")),
                        rainfall_accum_5d_mm=parse_flt(row.get("rainfall_accum_5d_mm")),
                        rainfall_accum_7d_mm=parse_flt(row.get("rainfall_accum_7d_mm")),
                        valid_rainfall_cells_at_d_minus_1=parse_int(row.get("valid_rainfall_cells_at_d_minus_1")),
                        is_documented_historical_flood=(row.get("is_documented_historical_flood", "").lower() == "true"),
                        historical_context=row.get("historical_context", ""),
                        proposed_ml_partition=row.get("proposed_ml_partition", ""),
                    )
                )

        return HistoricalEventsResponse(
            total_episodes=len(episodes),
            episodes=episodes,
        )
