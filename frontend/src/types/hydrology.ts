/**
 * frontend/src/types/hydrology.ts
 *
 * TypeScript interface definitions for the PRAVAAH Hydrological Intelligence Service.
 * Matches backend Pydantic schemas in backend/app/schemas/hydrology.py.
 */

export interface TargetGaugeStatus {
  station_id: string;
  station_name: string;
  danger_mark_m: number;
  warning_mark_m: number;
  highest_flood_level_m: number;
  observation_status: string;
  latest_water_level_m: number | null;
  status_note: string;
}

export interface LatestObservations {
  timestamp_utc: string;
  date: string;
  upstream_station_inflow: string;
  upstream_station_release: string;
  inflow_discharge_cumecs: number | null;
  inflow_discharge_cusecs: number | null;
  release_discharge_cumecs: number | null;
  release_discharge_cusecs: number | null;
  percentage_change_inflow_24h: number | null;
  percentage_change_release_24h: number | null;
  latest_rainfall_date: string | null;
  latest_rainfall_spatial_mean_mm: number | null;
  latest_rainfall_spatial_max_mm: number | null;
  target_gauge: TargetGaugeStatus;
}

export interface RainfallAccumulations {
  reference_date: string;
  accum_1d_mm: number | null;
  accum_3d_mm: number | null;
  accum_5d_mm: number | null;
  accum_7d_mm: number | null;
  spatial_coverage_cells: number;
  aggregation_method: string;
}

export interface DistributionStats {
  count: number;
  mean_cumecs: number;
  p50_cumecs: number;
  p90_cumecs: number;
  p95_cumecs: number;
  p99_cumecs: number;
  max_cumecs: number;
}

export interface DischargeStatistics {
  period_start: string;
  period_end: string;
  total_days: number;
  inflow_statistics_hkb_us: DistributionStats;
  release_statistics_hkb_ds: DistributionStats;
}

export interface DataQualityAudit {
  upstream_missing_days: number;
  upstream_duplicate_records: number;
  rainfall_missing_days: number;
  valid_rainfall_cells_per_day: number;
  rainfall_grid_resolution: string;
  data_freshness_status: string;
}

export interface HydrologySummaryResponse {
  service: string;
  version: string;
  milestone: string;
  latest_observations: LatestObservations;
  rainfall_accumulations: RainfallAccumulations;
  discharge_statistics: DischargeStatistics;
  data_quality: DataQualityAudit;
  source_metadata: Array<{
    dataset: string;
    publisher: string;
    portal?: string;
    status?: string;
    verified_coverage?: string;
  }>;
  limitations: string[];
}

export interface HistoricalEpisodeItem {
  episode_id: string;
  start_date: string;
  end_date: string;
  duration_days: number;
  peak_date: string;
  peak_inflow_cumecs?: number;
  peak_release_cumecs?: number;
  peak_discharge_cumecs?: number;
  historical_context?: string;
  is_documented_historical_flood?: boolean;
}

export interface HistoricalEventsResponse {
  service: string;
  event_definition: string;
  total_episodes: number;
  episodes: HistoricalEpisodeItem[];
}
