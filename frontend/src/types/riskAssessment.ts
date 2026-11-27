/**
 * frontend/src/types/riskAssessment.ts
 *
 * TypeScript types for the simplified PRAVAAH AI-Powered Flood Risk Assessment & Management System.
 */

export type RiskLevel = 'LOW' | 'MODERATE' | 'HIGH';
export type RiskColor = 'GREEN' | 'YELLOW' | 'RED';
export type ConfidenceLevel = 'HIGH' | 'MODERATE' | 'FAIR' | 'LOW';
export type AreaType = 'CORRIDOR_ALL' | 'BASIN' | 'REACH' | 'STATION';

export interface SupportedArea {
  id: string;
  name: string;
  area_type: AreaType;
  coverage_description: string;
  length_km?: number | null;
  area_km2?: number | null;
  representative_coord: [number, number];
  osm_way_id?: number | null;
  associated_stations: string[];
}

export interface SupportedAreasResponse {
  areas: SupportedArea[];
  default_area_id: string;
  total_corridor_length_km: number;
  catchment_area_km2: number;
}

export interface AssessmentRequest {
  area_id: string;
  forecast_days?: number;
  horizon_hours?: number;
}

export interface UpstreamMLForecast {
  model_name: string;
  predicted_inflow_cumecs: number;
  flood_band: string;
  model_r2_score: number;
  model_rmse_cumecs: number;
  model_mae_cumecs?: number;
  horizon_hours?: number;
  provenance_note: string;
}

export interface WeatherAssessmentSummary {
  provider: string;
  requested_days: number;
  available_days: number;
  total_forecast_rainfall_mm: number;
  peak_daily_rainfall_mm: number;
  peak_rainfall_date?: string | null;
  mean_temperature_c?: number | null;
  rainfall_risk_band: string;
  data_retrieved_at: string;
}

export interface ForecastConfidenceSummary {
  forecast_days: number;
  horizon_hours?: number;
  confidence_level: ConfidenceLevel;
  confidence_score_pct: number;
  decay_explanation: string;
}

export interface ReachRiskItem {
  area_id: string;
  name: string;
  risk_level: RiskLevel;
  risk_color: RiskColor;
  estimated_peak_discharge_cumecs: number;
  transit_lag_hours: number;
  osm_way_id?: number | null;
}

export interface StationRiskItem {
  station_id: string;
  station_name: string;
  latitude: number;
  longitude: number;
  chainage_km: number;
  risk_level: RiskLevel;
  risk_color: RiskColor;
  estimated_discharge_cumecs: number;
  warning_level_m?: number | null;
  danger_level_m?: number | null;
}

export interface CandidateShelter {
  shelter_id: string;
  name: string;
  zone: string;
  latitude: number;
  longitude: number;
  estimated_capacity_persons: number;
  elevation_msl: number;
  distance_to_river_m: number;
  approx_distance_km: number;
  facilities: string[];
  contact_agency: string;
  validation_status: string;
}

export interface ScientificProvenanceMetadata {
  ml_model_prediction: string;
  rule_based_risk_engine: string;
  weather_forecast_source: string;
  historical_observation_baseline: string;
  unavailable_realtime_data: string;
}

export interface AssessmentResponse {
  area_id: string;
  area_name: string;
  area_type: AreaType;
  coverage_description: string;
  forecast_days: number;
  risk_level: RiskLevel;
  risk_color: RiskColor;
  summary: string;
  guidance_action: string;
  confidence: ForecastConfidenceSummary;
  upstream_ml_forecast: UpstreamMLForecast;
  weather: WeatherAssessmentSummary;
  reach_risks: ReachRiskItem[];
  station_risks: StationRiskItem[];
  candidate_shelters: CandidateShelter[];
  scientific_provenance: ScientificProvenanceMetadata;
  assessed_at: string;
}

