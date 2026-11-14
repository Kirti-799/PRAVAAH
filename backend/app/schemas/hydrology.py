"""
backend/app/schemas/hydrology.py

Pydantic schemas for the read-only PRAVAAH Hydrological Intelligence Service.
Defines explicit typed models for observations, historical statistics,
data-quality indicators, and scientific limitations.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class TargetGaugeStatus(BaseModel):
    station_id: str = "028-MDD"
    station_name: str = "Delhi Old Railway Bridge"
    danger_mark_m: float = 205.33
    warning_mark_m: float = 204.50
    highest_flood_level_m: float = 208.66
    observation_status: str = Field(
        default="DATA_RESTRICTED_PENDING_CWC_REQUISITION",
        description="Current acquisition status of downstream continuous telemetry.",
    )
    latest_water_level_m: Optional[float] = Field(
        default=None,
        description="Always null until authentic continuous target telemetry is acquired.",
    )
    status_note: str = (
        "CWC Station 028-MDD continuous non-flood water-level records are restricted "
        "on public open CKAN endpoints under transboundary basin guidelines. "
        "Awaiting formal CWC/India-WRIS requisition."
    )


class LatestObservations(BaseModel):
    timestamp_utc: str
    date: str
    upstream_station_inflow: str = "Hathnikund Barrage (HKB U/S)"
    upstream_station_release: str = "Hathnikund Barrage (HKB D/S)"
    inflow_discharge_cumecs: Optional[float] = None
    inflow_discharge_cusecs: Optional[float] = None
    release_discharge_cumecs: Optional[float] = None
    release_discharge_cusecs: Optional[float] = None
    percentage_change_inflow_24h: Optional[float] = None
    percentage_change_release_24h: Optional[float] = None
    latest_rainfall_date: Optional[str] = None
    latest_rainfall_spatial_mean_mm: Optional[float] = None
    latest_rainfall_spatial_max_mm: Optional[float] = None
    target_gauge: TargetGaugeStatus = Field(default_factory=TargetGaugeStatus)


class RainfallAccumulations(BaseModel):
    reference_date: str
    accum_1d_mm: Optional[float] = None
    accum_3d_mm: Optional[float] = None
    accum_5d_mm: Optional[float] = None
    accum_7d_mm: Optional[float] = None
    spatial_coverage_cells: int = 91
    aggregation_method: str = "unweighted_provisional_bbox_mean"


class DistributionStats(BaseModel):
    count: int
    mean_cumecs: float
    p50_cumecs: float
    p90_cumecs: float
    p95_cumecs: float
    p99_cumecs: float
    max_cumecs: float


class DischargeStatistics(BaseModel):
    period_start: str
    period_end: str
    total_days: int
    inflow_statistics_hkb_us: DistributionStats
    release_statistics_hkb_ds: DistributionStats


class DataQualityAudit(BaseModel):
    upstream_missing_days: int = 0
    upstream_duplicate_records: int = 0
    rainfall_missing_days: int = 0
    valid_rainfall_cells_per_day: int = 91
    rainfall_grid_resolution: str = "0.25 deg x 0.25 deg (~27.5 km)"
    data_freshness_status: str


class HydrologySummaryResponse(BaseModel):
    service: str = "PRAVAAH Hydrological Intelligence Service"
    version: str = "1.0.0"
    milestone: str = "Phase 1E — Scientific Data Validation & Non-ML Hydrological Analysis"
    latest_observations: LatestObservations
    rainfall_accumulations: RainfallAccumulations
    discharge_statistics: DischargeStatistics
    data_quality: DataQualityAudit
    source_metadata: List[Dict[str, str]]
    limitations: List[str]


class HistoricalEpisodeItem(BaseModel):
    episode_id: str
    start_date: str
    end_date: str
    duration_days: int
    peak_date: str
    peak_upstream_inflow_cumecs: float
    peak_downstream_release_cumecs: float
    peak_upstream_inflow_cusecs: float
    peak_downstream_release_cusecs: float
    rainfall_accum_1d_mm: Optional[float] = None
    rainfall_accum_3d_mm: Optional[float] = None
    rainfall_accum_5d_mm: Optional[float] = None
    rainfall_accum_7d_mm: Optional[float] = None
    valid_rainfall_cells_at_d_minus_1: Optional[int] = None
    is_documented_historical_flood: bool
    historical_context: str
    proposed_ml_partition: str


class HistoricalEventsResponse(BaseModel):
    service: str = "PRAVAAH Historical Flood Events Registry"
    event_definition: str = (
        "Multi-day episodes where Hathnikund discharge (inflow or release) "
        "reaches or exceeds 1,500 cumecs (~53,000 cusecs) merged across <= 2 day gaps."
    )
    total_episodes: int
    episodes: List[HistoricalEpisodeItem]
