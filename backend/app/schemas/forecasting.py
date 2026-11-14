"""
backend/app/schemas/forecasting.py

Pydantic schemas for the PRAVAAH Upstream Forecasting Service (Phase 2A & Phase 2B).
Exposes:
1. Upstream dataset readiness and baseline benchmarks (Phase 2A).
2. Model status, validation/test metrics, and operational gating (Phase 2B).
3. Experimental Hathnikund 24h discharge forecast requests and responses (Phase 2B).

STRICT SCIENTIFIC RESTRICTIONS:
- Target is exclusively Hathnikund Barrage downstream release (HKB D/S) in m³/s.
- Under NO circumstances predicts Delhi Old Railway Bridge stage (m MSL).
- Under NO circumstances emits flood probability or evacuation mandates.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# ------------------------------------------------------------------------------
# Phase 2A Baseline Schemas
# ------------------------------------------------------------------------------

class BaselineMetricSummary(BaseModel):
    model_name: str
    partition: str
    sample_count: int
    mae_cumecs: float
    rmse_cumecs: float
    r2_score: float
    skill_score_vs_persistence: Optional[float] = None


class ForecastingReadinessResponse(BaseModel):
    service: str = "PRAVAAH Upstream Discharge Forecasting Readiness Service"
    version: str = "1.0.0"
    milestone: str = "Phase 2A — Feature Engineering and Baseline Feasibility"
    status: str = Field(
        default="PRELIMINARY_BASELINES_EVALUATED_NOT_VALIDATED_FOR_OPERATIONS",
        description="Dataset and preliminary baselines evaluated; operational deployment not yet validated.",
    )
    target_variable: str = (
        "Hathnikund Barrage downstream release (HKB D/S) 24 hours ahead (next contiguous calendar day)"
    )
    target_unit: str = "m³/s (cumecs)"
    target_station: str = "Hathnikund Barrage (HKB D/S)"
    delhi_flood_stage_status: str = "STRICTLY_BLOCKED_PENDING_CWC_028_MDD_STAGE"
    dataset_available: bool = True
    dataset_rows_total: int
    valid_target_rows: int
    complete_operational_rows: int
    partitions: Dict[str, int]
    baseline_benchmarks: List[BaselineMetricSummary]
    linear_model_coefficients: Dict[str, float]
    scientific_caveats: List[str]


# ------------------------------------------------------------------------------
# Phase 2B Non-Linear ML Regressor Schemas
# ------------------------------------------------------------------------------

class DischargeModelStatusResponse(BaseModel):
    service: str = "PRAVAAH Hathnikund Discharge Model Service"
    version: str = "2.0.0"
    milestone: str = "Phase 2B — Non-Linear Machine Learning Regressors"
    is_artifact_available: bool
    model_identifier: str = "hathnikund_rf_v1"
    model_type: str = "RandomForestRegressor"
    target_variable: str = "target_discharge_24h_cumecs"
    target_unit: str = "m³/s (cumecs)"
    forecast_horizon_hours: int = 24
    operational_status: str = Field(
        default="EXPERIMENTAL_RESEARCH_BENCHMARK",
        description="Operational classification under Phase 2B Decision Gate.",
    )
    promoted_for_operational_disaster_warning: bool = False
    feature_count: int = 23
    feature_allowlist: List[str]
    training_date_range: str
    validation_date_range: str
    test_date_range: str
    validation_metrics: Dict[str, Any]
    test_metrics: Dict[str, Any]
    high_flow_samples: Dict[str, int]
    top_features_by_permutation_importance: List[Dict[str, Any]]
    scientific_rationale: str
    prohibited_applications: List[str]


class ExperimentalDischargeForecastRequest(BaseModel):
    features: Dict[str, float] = Field(
        ...,
        description="Exact 23 operational feature values available at forecast issue time t.",
    )


class ExperimentalDischargeForecastResponse(BaseModel):
    model_identifier: str = "hathnikund_rf_v1"
    model_type: str = "RandomForestRegressor"
    target_variable: str = "target_discharge_24h_cumecs"
    forecast_lead_time_hours: int = 24
    predicted_discharge_cumecs: float
    discharge_unit: str = "m³/s (cumecs)"
    prediction_timestamp_utc: str
    observation_context: Optional[str] = None
    operational_status: str = "EXPERIMENTAL_RESEARCH_BENCHMARK"
    promoted_for_operational_disaster_warning: bool = False
    performance_reference: Dict[str, Any]
    experimental_warning: str


# ------------------------------------------------------------------------------
# Phase 3E.2 Hydrometeorological Coupling Schemas
# ------------------------------------------------------------------------------

class HydrometCouplingStatusResponse(BaseModel):
    service: str = "PRAVAAH Hydrometeorological Coupling Service"
    version: str = "1.0.0"
    milestone: str = "Phase 3E.2 — Hydro-Meteorological Feature Coupling"
    coupling_status: str = Field(
        ...,
        description="Coupling state: DISCONNECTED_FOR_AUTONOMOUS_OPERATIONS or COUPLED_RESEARCH_BENCHMARK_ONLY",
    )
    decision_rationale: str
    has_live_discharge_telemetry: bool = False
    has_live_meteorological_feed: bool = True
    rainfall_provider: str = "open_meteo_catchment"
    sampling_nodes_count: int = 20
    temporal_alignment_summary: Dict[str, Any]
    spatial_domain_comparison: Dict[str, Any]
    feature_compatibility_matrix: List[Dict[str, Any]]
    missing_telemetry_inputs: List[str]
    covariate_shift_warnings: List[str]
    governance_caveats: List[str]
    promoted_for_operational_disaster_warning: bool = False


class LiveCoupledForecastRequest(BaseModel):
    current_discharge_cumecs: Optional[float] = Field(
        default=None,
        description="Hathnikund downstream release Q_ds(t) in m³/s. If omitted, historical latest or median imputation is evaluated.",
    )
    current_inflow_cumecs: Optional[float] = Field(
        default=None,
        description="Hathnikund upstream inflow Q_us(t) in m³/s.",
    )
    discharge_history_cumecs: Optional[List[float]] = Field(
        default=None,
        description="Optional list of antecedent daily discharges [Q(t), Q(t-1), ..., Q(t-7)].",
    )
    use_live_catchment_rainfall: bool = Field(
        default=True,
        description="Whether to query live Open-Meteo 20-node catchment grid for meteorological features.",
    )
    custom_rainfall_mean_d_minus_1_mm: Optional[float] = Field(
        default=None,
        description="Manual override for day D-1 mean rainfall (mm/day).",
    )
    custom_rainfall_accum_3d_prior_mm: Optional[float] = Field(
        default=None,
        description="Manual override for 3-day prior linear accumulation (mm).",
    )
    custom_rainfall_accum_7d_prior_mm: Optional[float] = Field(
        default=None,
        description="Manual override for 7-day prior linear accumulation (mm).",
    )
    custom_rainfall_max_cell_3d_prior_mm: Optional[float] = Field(
        default=None,
        description="Manual override for 3-day peak cell intensity (mm/day).",
    )


class LiveCoupledForecastResponse(BaseModel):
    model_identifier: str = "hathnikund_rf_v1"
    model_type: str = "RandomForestRegressor"
    target_variable: str = "target_discharge_24h_cumecs"
    forecast_lead_time_hours: int = 24
    predicted_discharge_cumecs: float
    discharge_unit: str = "m³/s (cumecs)"
    prediction_timestamp_utc: str
    inference_readiness_status: str
    historical_observations_used: Dict[str, Any]
    live_meteorological_inputs_used: Dict[str, Any]
    missing_or_imputed_inputs: Dict[str, Any]
    operational_status: str = "EXPERIMENTAL_RESEARCH_BENCHMARK"
    promoted_for_operational_disaster_warning: bool = False
    scientific_caveats: List[str]
    experimental_warning: str

