"""Pydantic schemas for Disaster Intelligence, Risk Assessment, and Shelters."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class CWCGaugeThresholds(BaseModel):
    station_name: str = "Delhi Old Railway Bridge (ORB)"
    zero_gauge_msl: float = 201.25
    warning_level_msl: float = 204.50
    danger_level_msl: float = 205.33
    highest_flood_level_msl: float = 208.66
    hfl_date: str = "2023-07-13"
    current_reference_level_msl: float = 203.80
    status: str = "NORMAL"


class DischargeThresholds(BaseModel):
    station_name: str = "Hathnikund Barrage"
    normal_max_cumecs: float = 1982.0  # < 70,000 cfs
    low_flood_cumecs: float = 4248.0   # 70,000 - 150,000 cfs
    high_flood_cumecs: float = 7079.0  # 150,000 - 250,000 cfs
    extreme_surge_cumecs: float = 7079.0 # > 250,000 cfs (~359,000 cfs in July 2023)
    current_inflow_cumecs: float = 650.0
    risk_category: str = "NORMAL"


class ReliefShelter(BaseModel):
    shelter_id: str
    name: str
    zone: str
    latitude: float
    longitude: float
    capacity_persons: int
    elevation_msl: float
    distance_to_river_m: float
    facilities: List[str]
    contact_agency: str
    status: str = "ILLUSTRATIVE_PROTOTYPE"


class EvacuationCorridor(BaseModel):
    corridor_id: str
    name: str
    origin_zone: str
    destination_shelter_id: str
    distance_km: float
    transit_mode: str
    priority_level: str
    status: str = "UNVALIDATED_PROTOTYPE"
    coordinates: List[List[float]]  # [[lon, lat], ...]


class PopulationExposureSummary(BaseModel):
    source: str = "Derived from published Delhi Disaster Management Authority (DDMA) flood response reports"
    methodology: str = "Illustrative administrative estimate (raster cell grid unavailable in repo)"
    low_lying_villages_count: int = 14
    estimated_floodplain_residents: int = 37500
    livestock_count: int = 12400
    high_vulnerability_clusters: List[str] = [
        "Yamuna Khadar (Mayur Vihar)",
        "Monastery Market / Tibetan Colony",
        "Geeta Colony lowlands",
        "Garhi Mandu & Usmanpur",
        "Badarpur Khadar"
    ]
    disclaimer: str = (
        "ILLUSTRATIVE PLANNING REFERENCE ONLY: Cell-level raster grids (WorldPop/LandScan) "
        "and topological road networks are not bundled in this repository. Figures reflect "
        "unvalidated administrative estimates. Not certified for operational life-safety evacuation."
    )


class DisasterRiskSummaryResponse(BaseModel):
    timestamp_iso: str
    overall_alert_level: str  # NORMAL, ALERT, WARNING, SEVERE
    active_advisories: List[str]
    cwc_gauge: CWCGaugeThresholds
    discharge_status: DischargeThresholds
    shelters_available: int
    total_shelter_capacity: int
    population_exposure: PopulationExposureSummary

