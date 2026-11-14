/**
 * frontend/src/types/forecasting.ts
 *
 * TypeScript interface definitions for PRAVAAH Upstream Forecasting Services (Phase 2A & 2B).
 * Matches backend Pydantic schemas in backend/app/schemas/forecasting.py.
 */

export interface BaselineMetricSummary {
  model_name: string;
  partition: string;
  sample_count: number;
  mae_cumecs: number;
  rmse_cumecs: number;
  r2_score: number;
  skill_score_vs_persistence?: number | null;
}

export interface ForecastingReadinessResponse {
  service: string;
  version: string;
  milestone: string;
  status: string;
  target_variable: string;
  target_unit: string;
  target_station: string;
  delhi_flood_stage_status: string;
  dataset_available: boolean;
  dataset_rows_total: number;
  valid_target_rows: number;
  complete_operational_rows: number;
  partitions: Record<string, number>;
  baseline_benchmarks: BaselineMetricSummary[];
  linear_model_coefficients: Record<string, number>;
  scientific_caveats: string[];
}

export interface MetricDetail {
  sample_count: number;
  mae_cumecs: number;
  rmse_cumecs: number;
  r2_score: number;
  mean_bias_cumecs?: number;
  skill_score_vs_persistence?: number | null;
}

export interface PermutationImportanceItem {
  feature: string;
  rf_impurity_importance: number;
  val_permutation_rmse_delta: number;
  val_permutation_std: number;
}

export interface DischargeModelStatusResponse {
  service: string;
  version: string;
  milestone: string;
  is_artifact_available: boolean;
  model_identifier: string;
  model_type: string;
  target_variable: string;
  target_unit: string;
  forecast_horizon_hours: number;
  operational_status: string;
  promoted_for_operational_disaster_warning: boolean;
  feature_count: number;
  feature_allowlist: string[];
  training_date_range: string;
  validation_date_range: string;
  test_date_range: string;
  validation_metrics: MetricDetail;
  test_metrics: MetricDetail;
  high_flow_samples: Record<string, number>;
  top_features_by_permutation_importance: PermutationImportanceItem[];
  scientific_rationale: string;
  prohibited_applications: string[];
}

export interface ExperimentalDischargeForecastResponse {
  model_identifier: string;
  model_type: string;
  target_variable: string;
  forecast_lead_time_hours: number;
  predicted_discharge_cumecs: number;
  discharge_unit: string;
  prediction_timestamp_utc: string;
  observation_context?: string | null;
  operational_status: string;
  promoted_for_operational_disaster_warning: boolean;
  performance_reference: Record<string, number>;
  experimental_warning: string;
}
