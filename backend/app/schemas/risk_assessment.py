"""backend/app/schemas/risk_assessment.py

Pydantic schemas for the simplified PRAVAAH AI-Powered Flood Risk Assessment & Management System.
Defines:
- Supported geographical areas along the Yamuna corridor.
- Forecast horizon (2 to 10 days) with confidence decay metrics.
- Rule-based & ML-coupled risk classifications (LOW / MODERATE / HIGH).
- Transparent provenance metadata and unvalidated candidate evacuation shelters.
"""

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field


RiskLevel = Literal["LOW", "MODERATE", "HIGH"]
RiskColor = Literal["GREEN", "YELLOW", "RED"]
ConfidenceLevel = Literal["HIGH", "MODERATE", "FAIR", "LOW"]
AreaType = Literal["CORRIDOR_ALL", "BASIN", "REACH", "STATION"]


class SupportedArea(BaseModel):
    """Geographical area supported by authentic spatial data in PRAVAAH."""
    id: str = Field(..., description="Unique area identifier, e.g. 'DELHI_CENTRAL'")
    name: str = Field(..., description="Human-readable area title")
    area_type: AreaType = Field(..., description="Classification: BASIN, REACH, STATION, or CORRIDOR_ALL")
    coverage_description: str = Field(..., description="Geographical coverage and landmarks")
    length_km: Optional[float] = Field(None, description="Reach thalweg length in km if applicable")
    area_km2: Optional[float] = Field(None, description="Basin area in km² if applicable")
    representative_coord: List[float] = Field(..., description="[lat, lon] representative midpoint")
    osm_way_id: Optional[int] = Field(None, description="OpenStreetMap way ID if derived from river geometry")
    associated_stations: List[str] = Field(default_factory=list, description="Hydrometric stations within/adjacent to this area")


class SupportedAreasResponse(BaseModel):
    """Catalog of supported areas."""
    areas: List[SupportedArea]
    default_area_id: str = "DELHI_CENTRAL"
    total_corridor_length_km: float = 268.94
    catchment_area_km2: float = 11365.12


class AssessmentRequest(BaseModel):
    """Request payload for flood risk assessment (Strict 24-Hour Horizon)."""
    area_id: str = Field(default="DELHI_CENTRAL", description="Supported area ID to assess")
    forecast_days: int = Field(default=1, ge=1, le=10, description="Forecast horizon (strictly 1 day / 24 hours)")
    horizon_hours: int = Field(default=24, description="Strict 24-hour prediction horizon")


class UpstreamMLForecast(BaseModel):
    """Output from the trained upstream Random Forest model (Audited Test Metrics)."""
    model_name: str = "Hathnikund Random Forest Regressor v1"
    predicted_inflow_cumecs: float = Field(..., description="Predicted next-24-hour discharge at Hathnikund Barrage")
    flood_band: str = Field(..., description="Flow band: NORMAL_FLOW, ALERT_FLOW, MEDIUM_FLOOD, HIGH_FLOOD")
    model_r2_score: float = 0.380
    model_rmse_cumecs: float = 469.5
    model_mae_cumecs: float = 95.8
    horizon_hours: int = 24
    provenance_note: str = Field(
        default="ML model predicts upstream Hathnikund Barrage discharge (m³/s) for the next 24 hours. Downstream reach risk is determined via hydraulic lag and reach attenuation. Tree-based models cannot extrapolate beyond historical training peak (3,524 m³/s).",
        description="Scientific scope statement"
    )


class WeatherAssessmentSummary(BaseModel):
    """Atmospheric conditions over the 24-hour operational horizon."""
    provider: str = "Open-Meteo Weather API"
    requested_days: int = 1
    available_days: int = 1
    total_forecast_rainfall_mm: float
    peak_daily_rainfall_mm: float
    peak_rainfall_date: Optional[str] = None
    mean_temperature_c: Optional[float] = None
    rainfall_risk_band: str = Field(..., description="LOW_OR_TRACE, MODERATE_RAIN, HEAVY_RAIN, VERY_HEAVY_RAIN")
    data_retrieved_at: str


class ForecastConfidenceSummary(BaseModel):
    """Operational horizon indicator."""
    forecast_days: int = 1
    horizon_hours: int = 24
    confidence_level: ConfidenceLevel = "HIGH"
    confidence_score_pct: int = 92
    decay_explanation: str = "High confidence 24-hour operational horizon. Short-range numerical weather predictions exhibit high spatial and volumetric consistency."


class ReachRiskItem(BaseModel):
    """Risk status for a river reach segment on the interactive map."""
    area_id: str
    name: str
    risk_level: RiskLevel
    risk_color: RiskColor
    estimated_peak_discharge_cumecs: float
    transit_lag_hours: float
    osm_way_id: Optional[int] = None


class StationRiskItem(BaseModel):
    """Risk status for a corridor monitoring station."""
    station_id: str
    station_name: str
    latitude: float
    longitude: float
    chainage_km: float
    risk_level: RiskLevel
    risk_color: RiskColor
    estimated_discharge_cumecs: float
    warning_level_m: Optional[float] = None
    danger_level_m: Optional[float] = None


class CandidateShelter(BaseModel):
    """Candidate evacuation shelter near the affected area."""
    shelter_id: str
    name: str
    zone: str
    latitude: float
    longitude: float
    estimated_capacity_persons: int
    elevation_msl: float
    distance_to_river_m: float
    approx_distance_km: float
    facilities: List[str]
    contact_agency: str
    validation_status: str = "ILLUSTRATIVE_PROTOTYPE (Candidate shelter for planning; real-time occupancy tracking is unavailable)"


class ScientificProvenanceMetadata(BaseModel):
    """Transparent scientific audit trail distinguishing ML, rules, observations, and gaps."""
    ml_model_prediction: str
    rule_based_risk_engine: str
    weather_forecast_source: str
    historical_observation_baseline: str
    unavailable_realtime_data: str


class AssessmentResponse(BaseModel):
    """Comprehensive, simplified flood risk assessment response."""
    area_id: str
    area_name: str
    area_type: AreaType
    coverage_description: str
    forecast_days: int
    risk_level: RiskLevel
    risk_color: RiskColor
    summary: str
    guidance_action: str
    confidence: ForecastConfidenceSummary
    upstream_ml_forecast: UpstreamMLForecast
    weather: WeatherAssessmentSummary
    reach_risks: List[ReachRiskItem]
    station_risks: List[StationRiskItem]
    candidate_shelters: List[CandidateShelter]
    scientific_provenance: ScientificProvenanceMetadata
    assessed_at: str

