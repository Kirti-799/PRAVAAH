/**
 * frontend/src/types/routing.ts
 *
 * TypeScript interface definitions for PRAVAAH Hydrological Routing Service.
 * Matches backend Pydantic schemas in backend/app/schemas/routing.py.
 */

export interface ParameterAuditItem {
  name: string;
  symbol: string;
  unit: string;
  value: number | null;
  status: 'MEASURED' | 'DERIVED' | 'ASSUMED' | 'UNAVAILABLE';
  provenance: string;
  spatial_applicability: string;
  temporal_applicability: string;
  uncertainty_description: string;
}

export interface MethodFeasibilityItem {
  method_name: string;
  is_feasible: boolean;
  data_requirements: string[];
  missing_requirements: string[];
  verdict_rationale: string;
}

export interface RoutingReadinessResponse {
  service: string;
  version: string;
  milestone: string;
  readiness_status: string;
  summary_verdict: string;
  target_gauge_id: string;
  target_gauge_name: string;
  downstream_calibration_available: boolean;
  methods_evaluation: MethodFeasibilityItem[];
  parameters_summary: Record<string, number>;
  parameters_detail: ParameterAuditItem[];
  critical_blockers: string[];
  scientific_limitations: string[];
  next_recommended_actions: string[];
}

export interface RoutingTimeSeriesItem {
  date: string;
  observed_upstream_inflow_cumecs: number | null;
  observed_upstream_release_cumecs: number;
  simulated_downstream_discharge_cumecs: number;
  observed_downstream_stage_m: number | null; // Always null
}

export interface RoutingSimulationResponse {
  service: string;
  version: string;
  status: string;
  routing_method: string;
  episode_id: string;
  episode_name: string;
  reach_name: string;
  reach_length_km: number;
  parameters: {
    K_hours: number;
    x: number;
    dt_hours: number;
    subreaches: number;
  };
  routing_coefficients: {
    C0: number;
    C1: number;
    C2: number;
    sum_coefficients: number;
  };
  numerical_stability_verified: boolean;
  mass_balance_error_percent: number;
  observed_hathnikund_peak_inflow_cumecs: number;
  observed_hathnikund_peak_release_cumecs: number;
  observed_hathnikund_peak_date: string;
  simulated_peak_downstream_discharge_cumecs: number;
  simulated_peak_downstream_date: string;
  simulated_attenuation_cumecs: number;
  simulated_attenuation_percent: number;
  simulated_lag_hours: number;
  documented_delhi_crest_stage_m: number | null;
  documented_delhi_crest_date: string | null;
  documented_delhi_breach_status: string;
  time_series: RoutingTimeSeriesItem[];
  scientific_disclaimer: string;
  scientific_caveats: string[];
}

export interface TabletopScenarioRequest {
  scenario_id?: string;
  scenario_name?: string;
  scenario_type?: string;
  scenario_description?: string;
  inflow_hydrograph: number[];
  time_labels?: string[];
  initial_outflow_cumecs?: number;
  K_hours: number;
  x: number;
  dt_hours?: number;
  subreaches?: number;
}

export interface TabletopTimeSeriesItem {
  step: number;
  time_label: string;
  inflow_cumecs: number;
  simulated_outflow_cumecs: number;
  observed_downstream_stage_m: number | null;
}

export interface TabletopScenarioResponse {
  service: string;
  version: string;
  milestone: string;
  scenario_id: string;
  scenario_name: string;
  scenario_type: string;
  scenario_description: string;
  is_hypothetical: boolean;
  data_provenance: string;
  time_step_hours: number;
  duration_steps: number;
  duration_hours: number;
  routing_parameters: {
    K_hours: number;
    x: number;
    dt_hours: number;
    subreaches: number;
    is_authoritative_baseline?: boolean;
    is_alternative_heuristic?: boolean;
  };
  routing_coefficients: {
    C0: number;
    C1: number;
    C2: number;
    sum: number;
  };
  numerical_validity_status: string;
  stability_criteria_met: boolean;
  reproducibility_hash: string;
  timestamp_utc: string;
  model_version: string;
  peak_inflow_discharge_cumecs: number;
  peak_inflow_step: number;
  peak_inflow_time_label: string;
  peak_simulated_outflow_discharge_cumecs: number;
  peak_simulated_outflow_step: number;
  peak_simulated_outflow_time_label: string;
  peak_attenuation_cumecs: number;
  peak_attenuation_percent: number;
  apparent_lag_hours: number;
  apparent_lag_steps: number;
  total_inflow_volume_m3: number;
  total_outflow_volume_m3: number;
  reach_storage_change_m3: number;
  mass_conservation_error_percent: number;
  time_series: TabletopTimeSeriesItem[];
  scientific_disclaimer: string;
  scientific_caveats: string[];
}

export interface TabletopPresetItem {
  preset_id: string;
  preset_type: string;
  name: string;
  description: string;
  inflow_hydrograph: number[];
  time_labels: string[];
  time_step_hours: number;
  recommended_K_hours: number;
  recommended_x: number;
  purpose_and_expected_behavior: string;
}

export interface DocumentedParameterConfigItem {
  config_id: string;
  name: string;
  K_hours: number;
  x: number;
  dt_hours: number;
  subreaches: number;
  is_authoritative_baseline: boolean;
  provenance: string;
  calibration_status: string;
  numerical_characteristics: string;
  discrepancy_explanation: string;
  coefficients: {
    C0: number;
    C1: number;
    C2: number;
    sum: number;
  };
  stability_bounds: {
    lower_bound_2Kx_hours: number;
    time_step_dt_hours: number;
    upper_bound_2K_1_minus_x_hours: number;
    is_strictly_stable: boolean;
  };
}

export interface TabletopPresetsResponse {
  service: string;
  presets: TabletopPresetItem[];
  documented_parameters: DocumentedParameterConfigItem[];
  scientific_notice: string;
}

// ==============================================================================
// Phase 3E.4: Spatial 1D Routing Intelligence Types
// ==============================================================================

export interface SpatialRoutingPoint {
  station_id: string;
  name: string;
  chainage_km: number;
  latitude: number;
  longitude: number;
  discharge_cumecs: number;
  value_type: 'OBSERVED' | 'SIMULATED' | 'INTERPOLATED_WAVE';
  data_provenance: string;
  reach_id: string;
  is_monitoring_station: boolean;
}

export interface SpatialRoutingTimeStep {
  date: string;
  step_index: number;
  observed_inflow_cumecs: number;
  simulated_outflow_cumecs: number;
  points: SpatialRoutingPoint[];
}

export interface SpatialRoutingSimulationResponse {
  service: string;
  version: string;
  status: string;
  episode_id?: string;
  episode_name?: string;
  reach_name: string;
  reach_length_km: number;
  routing_corridor_nominal_km: number;
  total_stations_count: number;
  routing_parameters: Record<string, any>;
  routing_coefficients: Record<string, number>;
  numerical_stability_verified: boolean;
  mass_balance_error_percent: number;
  simulated_lag_hours: number;
  simulated_attenuation_percent: number;
  peak_observed_inflow_cumecs: number;
  peak_observed_inflow_date: string;
  peak_simulated_outflow_cumecs: number;
  peak_simulated_outflow_date: string;
  documented_delhi_crest_stage_m: number | null;
  documented_delhi_crest_date: string | null;
  documented_delhi_breach_status?: string | null;
  time_steps: SpatialRoutingTimeStep[];
  corridor_stations: Array<{
    station_id: string;
    name: string;
    latitude: number;
    longitude: number;
    role: string;
    chainage_km: number;
    offset_m: number;
    is_primary: boolean;
  }>;
  scientific_disclaimer: string;
  scientific_caveats: string[];
}


