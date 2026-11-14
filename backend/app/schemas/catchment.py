"""
backend/app/schemas/catchment.py

API Schemas for Upstream Catchment Delineation and Morphometric Characterization.
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class PourPointInfo(BaseModel):
    name: str
    nominal_coordinates: List[float] = Field(..., description="[lat, lon]")
    snapped_coordinates: List[float] = Field(..., description="[lat, lon]")
    distance_snapped_m: float
    provenance: str


class CatchmentSummaryResponse(BaseModel):
    catchment_id: str
    catchment_name: str
    pour_point: PourPointInfo
    area_sq_km: float
    perimeter_km: float
    elevation_min_m: float
    elevation_max_m: float
    elevation_mean_m: float
    elevation_median_m: float
    elevation_std_m: float
    hypsometry_percentiles: Dict[str, float]
    bounding_box: Dict[str, float]
    contributing_cells_count: int
    stream_length_total_km: float
    drainage_density_km_per_sq_km: float
    major_tributaries: List[str]
    scientific_caveats: List[str]


class CatchmentStatusResponse(BaseModel):
    service: str
    delineation_status: str  # "DELINEATED", "RAW_DEM_AVAILABLE", "UNACQUIRED"
    area_sq_km: float
    pour_point_name: str
    pour_point_lat: float
    pour_point_lon: float
    raw_dem_tiles_acquired: int
    raw_dem_tiles_required: int
    has_drainage_network: bool
    scientific_integrity_note: str
