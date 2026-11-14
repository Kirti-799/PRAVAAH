"""
backend/app/schemas/routing.py

Pydantic schemas for the read-only PRAVAAH Hydrological Routing Service.
Defines typed response models for hydraulic routing readiness, parameter catalogs,
and non-ML Muskingum simulation prototypes.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ParameterAuditItem(BaseModel):
    name: str
    symbol: str
    unit: str
    value: Optional[float] = None
    status: str
    provenance: str
    spatial_applicability: str
    temporal_applicability: str
    uncertainty_description: str


class MethodFeasibilitySchema(BaseModel):
    method_name: str
    is_feasible: bool
    data_requirements: List[str]
    missing_requirements: List[str]
    verdict_rationale: str


class RoutingReadinessResponse(BaseModel):
    service: str = "PRAVAAH Hydraulic Routing Readiness Evaluator"
    version: str = "1.0.0"
    milestone: str = "Phase 1F — Hydrological Routing Feasibility & Non-ML Prototype"
    readiness_status: str
    summary_verdict: str
    target_gauge_id: str = "028-MDD"
    target_gauge_name: str = "Delhi Old Railway Bridge"
    downstream_calibration_available: bool = False
    methods_evaluation: List[MethodFeasibilitySchema]
    parameters_summary: Dict[str, int]
    parameters_detail: List[ParameterAuditItem]
    critical_blockers: List[str]
    scientific_limitations: List[str]
    next_recommended_actions: List[str]


class RoutingTimeSeriesItem(BaseModel):
    date: str
    observed_upstream_inflow_cumecs: Optional[float] = None
    observed_upstream_release_cumecs: float
    simulated_downstream_discharge_cumecs: float
    observed_downstream_stage_m: Optional[float] = Field(
        default=None,
        description="Always null: downstream continuous water level is not estimated.",
    )


class RoutingSimulationResponse(BaseModel):
    service: str = "PRAVAAH Non-ML Hydrological Routing Simulator"
    version: str = "1.0.0"
    status: str
    routing_method: str
    episode_id: str
    episode_name: str
    reach_name: str
    reach_length_km: float
    parameters: Dict[str, Any]
    routing_coefficients: Dict[str, float]
    numerical_stability_verified: bool
    mass_balance_error_percent: float
    observed_hathnikund_peak_inflow_cumecs: float
    observed_hathnikund_peak_release_cumecs: float
    observed_hathnikund_peak_date: str
    simulated_peak_downstream_discharge_cumecs: float
    simulated_peak_downstream_date: str
    simulated_attenuation_cumecs: float
    simulated_attenuation_percent: float
    simulated_lag_hours: float
    documented_delhi_crest_stage_m: Optional[float] = None
    documented_delhi_crest_date: Optional[str] = None
    documented_delhi_breach_status: str
    time_series: List[RoutingTimeSeriesItem]
    scientific_disclaimer: str = (
        "SIMULATED DOWNSTREAM DISCHARGE — NOT OBSERVED DELHI WATER LEVEL. "
        "Parameter-dependent sensitivity prototype; not an empirically calibrated forecast."
    )
    scientific_caveats: List[str]


# ==============================================================================
# Phase 2C-B: Tabletop Scenario Simulation Schemas
# ==============================================================================

class TabletopScenarioRequest(BaseModel):
    scenario_id: Optional[str] = Field(default="SCENARIO_USER_01", description="Unique identifier for scenario")
    scenario_name: Optional[str] = Field(default="Tabletop Hypothetical Scenario", description="Human-readable scenario name")
    scenario_type: Optional[str] = Field(default="CUSTOM", description="Scenario type e.g. CONSTANT, GRADUALLY_RISING, PULSE, SUSTAINED_ELEVATED, CUSTOM")
    scenario_description: Optional[str] = Field(default="Hypothetical tabletop scenario simulation", description="Description of flood-wave conditions")
    inflow_hydrograph: List[float] = Field(..., min_length=2, description="Hypothetical inflow discharge sequence in m³/s (minimum 2 points)")
    time_labels: Optional[List[str]] = Field(default=None, description="Optional time step labels (e.g. Day 1, T+00h)")
    initial_outflow_cumecs: Optional[float] = Field(default=None, ge=0.0, description="Optional initial outflow condition in m³/s. Defaults to I_0.")
    K_hours: float = Field(default=36.0, ge=1.0, le=120.0, description="Muskingum storage constant K in hours (wave transit time)")
    x: float = Field(default=0.20, ge=0.0, le=0.50, description="Muskingum dimensionless weighting factor x [0.0, 0.5]")
    dt_hours: float = Field(default=24.0, ge=0.1, le=168.0, description="Simulation time step dt in hours")
    subreaches: int = Field(default=1, ge=1, le=10, description="Number of sub-reaches m >= 1")


class TabletopTimeSeriesItem(BaseModel):
    step: int
    time_label: str
    inflow_cumecs: float
    simulated_outflow_cumecs: float
    observed_downstream_stage_m: Optional[float] = Field(
        default=None,
        description="Always null: downstream continuous water level is not estimated.",
    )


class TabletopScenarioResponse(BaseModel):
    service: str = "PRAVAAH Tabletop Hydrological Scenario Simulator"
    version: str = "2.0.0"
    milestone: str = "Phase 2C-B — Hydrological Routing Validation & Tabletop Simulation"
    scenario_id: str
    scenario_name: str
    scenario_type: str
    scenario_description: str
    is_hypothetical: bool
    data_provenance: str
    time_step_hours: float
    duration_steps: int
    duration_hours: float
    routing_parameters: Dict[str, Any]
    routing_coefficients: Dict[str, float]
    numerical_validity_status: str
    stability_criteria_met: bool
    reproducibility_hash: str
    timestamp_utc: str
    model_version: str
    peak_inflow_discharge_cumecs: float
    peak_inflow_step: int
    peak_inflow_time_label: str
    peak_simulated_outflow_discharge_cumecs: float
    peak_simulated_outflow_step: int
    peak_simulated_outflow_time_label: str
    peak_attenuation_cumecs: float
    peak_attenuation_percent: float
    apparent_lag_hours: float
    apparent_lag_steps: int
    total_inflow_volume_m3: float
    total_outflow_volume_m3: float
    reach_storage_change_m3: float
    mass_conservation_error_percent: float
    time_series: List[TabletopTimeSeriesItem]
    scientific_disclaimer: str
    scientific_caveats: List[str]


class TabletopPresetItem(BaseModel):
    preset_id: str
    preset_type: str
    name: str
    description: str
    inflow_hydrograph: List[float]
    time_labels: List[str]
    time_step_hours: float
    recommended_K_hours: float
    recommended_x: float
    purpose_and_expected_behavior: str


class DocumentedParameterConfigItem(BaseModel):
    config_id: str
    name: str
    K_hours: float
    x: float
    dt_hours: float
    subreaches: int
    is_authoritative_baseline: bool
    provenance: str
    calibration_status: str
    numerical_characteristics: str
    discrepancy_explanation: str
    coefficients: Dict[str, float]
    stability_bounds: Dict[str, Any]


class TabletopPresetsResponse(BaseModel):
    service: str = "PRAVAAH Tabletop Presets & Parameter Catalog"
    presets: List[TabletopPresetItem]
    documented_parameters: List[DocumentedParameterConfigItem]
    scientific_notice: str = (
        "Presets are mathematical stress-test hydrographs designed to evaluate routing behavior "
        "(attenuation, lag, conservation). Neither the presets nor the parameters constitute "
        "calibrated flood predictions for Delhi."
    )


# ==============================================================================
# Phase 3E.4: Spatial 1D Routing Intelligence Schemas
# ==============================================================================

class SpatialRoutingPoint(BaseModel):
    station_id: str = Field(..., description="Unique chainage or station identifier")
    name: str = Field(..., description="Station or landmark name along the corridor")
    chainage_km: float = Field(..., description="River chainage distance from Hathnikund Barrage in km")
    latitude: float = Field(..., description="WGS 84 latitude on river centreline")
    longitude: float = Field(..., description="WGS 84 longitude on river centreline")
    discharge_cumecs: float = Field(..., description="Discharge rate in m³/s (cumecs)")
    value_type: str = Field(..., description="OBSERVED, SIMULATED, or INTERPOLATED_WAVE")
    data_provenance: str = Field(..., description="Origin of data (e.g. Haryana I&WRD gauge or Muskingum routing)")
    reach_id: str = Field(..., description="Identifier of the reach segment")
    is_monitoring_station: bool = Field(default=False, description="True if point corresponds to a named corridor monitoring station")


class SpatialRoutingTimeStep(BaseModel):
    date: str = Field(..., description="Date or time label of the simulation step (YYYY-MM-DD)")
    step_index: int = Field(..., description="0-indexed sequence number of the time step")
    observed_inflow_cumecs: float = Field(..., description="Observed release at Hathnikund Barrage (km 0.0)")
    simulated_outflow_cumecs: float = Field(..., description="Simulated discharge at downstream terminus")
    points: List[SpatialRoutingPoint] = Field(..., description="Spatially mapped discharge values along river corridor")


class SpatialRoutingSimulationResponse(BaseModel):
    service: str = "PRAVAAH Spatial 1D Routing Intelligence"
    version: str = "1.0.0"
    status: str
    episode_id: Optional[str] = None
    episode_name: Optional[str] = None
    reach_name: str
    reach_length_km: float
    routing_corridor_nominal_km: float
    total_stations_count: int
    routing_parameters: Dict[str, Any]
    routing_coefficients: Dict[str, float]
    numerical_stability_verified: bool
    mass_balance_error_percent: float
    simulated_lag_hours: float
    simulated_attenuation_percent: float
    peak_observed_inflow_cumecs: float
    peak_observed_inflow_date: str
    peak_simulated_outflow_cumecs: float
    peak_simulated_outflow_date: str
    documented_delhi_crest_stage_m: Optional[float] = None
    documented_delhi_crest_date: Optional[str] = None
    documented_delhi_breach_status: Optional[str] = None
    time_steps: List[SpatialRoutingTimeStep]
    corridor_stations: List[Dict[str, Any]]
    scientific_disclaimer: str
    scientific_caveats: List[str]


