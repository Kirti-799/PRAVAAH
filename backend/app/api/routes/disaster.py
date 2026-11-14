"""FastAPI router for Disaster Intelligence, Risk Assessment, and Shelters."""

from typing import Optional, Dict, Any
from fastapi import APIRouter, Query
from app.schemas.disaster import DisasterRiskSummaryResponse
from app.services.disaster_service import (
    get_risk_summary,
    get_shelters_geojson,
    get_evacuation_corridors_geojson,
)
from app.services.hydrology import HydrologyService

router = APIRouter()


@router.get(
    "/risk-summary",
    response_model=DisasterRiskSummaryResponse,
    summary="Get Comprehensive Disaster Risk Summary",
    description=(
        "Returns active flood risk classifications based on Hathnikund Barrage discharge "
        "and authentic CWC gauge thresholds at Delhi Old Railway Bridge (ORB)."
    ),
)
def get_disaster_risk(
    inflow_cumecs: float = Query(
        650.0,
        description="Discharge value in m³/s (default: 650.0 m³/s seasonal baseline).",
    )
):
    return get_risk_summary(inflow_cumecs=inflow_cumecs)


@router.get(
    "/shelters",
    response_model=Dict[str, Any],
    summary="Get Designated Flood Relief Shelters GeoJSON",
    description="Returns authenticated DDMA emergency relief shelters as GeoJSON points.",
)
def get_shelters():
    return get_shelters_geojson()


@router.get(
    "/evacuation-corridors",
    response_model=Dict[str, Any],
    summary="Get Emergency Evacuation Corridors GeoJSON",
    description="Returns pre-designated evacuation corridors linking lowlands to shelters as GeoJSON lines.",
)
def get_evacuation_corridors():
    return get_evacuation_corridors_geojson()
