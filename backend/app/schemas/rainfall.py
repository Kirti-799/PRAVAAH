"""
backend/app/schemas/rainfall.py

API Request and Response schemas for Catchment Spatial Rainfall Ingestion,
Aggregated Accumulations, and Antecedent Precipitation Indices (API).
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class RainfallRateSummary(BaseModel):
    mean_mm: float
    min_mm: float
    max_mm: float
    std_mm: float


class RainfallAccumulationSummary(BaseModel):
    acc_24h_mm: float
    acc_72h_mm: float
    acc_168h_mm: float


class AntecedentPrecipitationSummary(BaseModel):
    api_3_mm: float
    api_7_mm: float
    api_14_mm: float
    decay_factor_k: float


class CatchmentRainfallPoint(BaseModel):
    id: str
    name: str
    latitude: float
    longitude: float
    elevation_m: float
    current_mm: float
    forecast_24h_mm: float
    api_3_mm: float


class CatchmentRainfallSummaryResponse(BaseModel):
    catchment_id: str
    provider: str
    timestamp: str
    observation_or_forecast: str
    contributing_points_count: int
    spatial_coverage_percentage: float
    missing_data_percentage: float
    current_rate: RainfallRateSummary
    accumulations: RainfallAccumulationSummary
    antecedent_indices: AntecedentPrecipitationSummary
    sample_grid_points: List[CatchmentRainfallPoint]
    scientific_disclaimer: str


class RainfallStatusResponse(BaseModel):
    provider_name: str
    is_available: bool
    status_code: Optional[int] = 200
    latency_ms: Optional[float] = None
    spatial_sampling_nodes_count: int
    catchment_bounding_box: Dict[str, float]
    active_aggregation_window_hours: List[int] = [24, 72, 168]
    notes: List[str] = Field(default_factory=list)
