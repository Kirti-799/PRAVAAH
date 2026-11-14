"""
backend/app/api/routes/hydrology.py

FastAPI router exposing read-only non-ML hydrological intelligence endpoints:
- GET /api/hydrology/summary: Latest observations, rainfall accumulations, historical stats, and limitations.
- GET /api/hydrology/events: Historical high-discharge episodes extracted from verified Hathnikund observations.
- GET /api/hydrology/routing-readiness: Hydraulic data completeness audit and routing feasibility assessment.
- GET /api/hydrology/routing-simulation: Parameter-explicit Muskingum downstream routing simulation prototype.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status
from app.schemas.hydrology import HydrologySummaryResponse, HistoricalEventsResponse
from app.schemas.routing import (
    RoutingReadinessResponse,
    RoutingSimulationResponse,
    TabletopScenarioRequest,
    TabletopScenarioResponse,
    TabletopPresetsResponse,
    SpatialRoutingSimulationResponse,
)
from app.services.hydrology import HydrologyService
from app.services.routing import RoutingService


router = APIRouter(prefix="/hydrology", tags=["hydrology"])
hydrology_service = HydrologyService()
service = hydrology_service  # Backward compatibility alias
routing_service = RoutingService()


@router.get(
    "/summary",
    response_model=HydrologySummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Historical and Latest Hydrological Summary",
    description=(
        "Returns verified descriptive hydrological indicators from real acquired datasets: "
        "Hathnikund upstream inflow, downstream release, antecedent catchment rainfall accumulations, "
        "historical percentiles, data-quality audits, and explicit scientific limitations."
    ),
)
def get_hydrology_summary() -> HydrologySummaryResponse:
    try:
        return service.get_summary()
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Required hydrological datasets are unavailable: {str(exc)}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error computing hydrological summary: {str(exc)}",
        )


@router.get(
    "/events",
    response_model=HistoricalEventsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Historical High-Discharge Episodes",
    description=(
        "Returns reproducible multi-day high-flow episodes extracted from real Hathnikund observations "
        "(Q >= 1,500 cumecs), paired with antecedent rainfall accumulations and historical flood context."
    ),
)
def get_historical_events() -> HistoricalEventsResponse:
    try:
        return service.get_historical_events()
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Historical episodes dataset is unavailable: {str(exc)}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving historical episodes: {str(exc)}",
        )


@router.get(
    "/routing-readiness",
    response_model=RoutingReadinessResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Hydraulic Routing Feasibility & Data Readiness",
    description=(
        "Evaluates the availability of physical hydraulic parameters (reach length, slope, bathymetry, "
        "Manning's roughness, lateral inflows, barrage operations, and downstream calibration telemetry) "
        "for the 220 km Hathnikund-to-Delhi reach. Explains why hydrodynamic and calibrated models are blocked."
    ),
)
def get_routing_readiness() -> RoutingReadinessResponse:
    try:
        return routing_service.get_readiness()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error auditing routing readiness: {str(exc)}",
        )


@router.get(
    "/routing-simulation",
    response_model=RoutingSimulationResponse,
    status_code=status.HTTP_200_OK,
    summary="Run Muskingum Downstream Routing Simulation Prototype",
    description=(
        "Runs an exploratory non-ML Muskingum routing prototype on a verified historical high-flow episode. "
        "Strictly labels outputs as SIMULATED DOWNSTREAM DISCHARGE and NEVER estimates Delhi water level. "
        "Enforces numerical stability and mass-balance conservation checks."
    ),
)
def get_routing_simulation(
    episode_id: str = Query(
        default="EPISODE_2023_08",
        description="Historical episode ID to route (e.g. EPISODE_2019_04, EPISODE_2022_07, EPISODE_2023_08)",
    ),
    K_hours: float = Query(
        default=36.0,
        ge=1.0,
        le=120.0,
        description="Muskingum storage constant K in hours (wave travel time). Must satisfy stability criteria.",
    ),
    x: float = Query(
        default=0.20,
        ge=0.0,
        le=0.50,
        description="Muskingum dimensionless weighting factor x (wedge vs prism storage).",
    ),
    subreaches: int = Query(
        default=1,
        ge=1,
        le=10,
        description="Number of reach sub-divisions (m >= 1).",
    ),
) -> RoutingSimulationResponse:
    try:
        return routing_service.simulate_episode(
            episode_id=episode_id,
            K_hours=K_hours,
            x=x,
            dt_hours=24.0,
            subreaches=subreaches,
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Episode not found: {str(exc)}",
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Parameter validation / numerical stability error: {str(exc)}",
        )
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Required hydrological dataset unavailable: {str(exc)}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Routing simulation error: {str(exc)}",
        )


@router.get(
    "/routing-simulation-spatial",
    response_model=SpatialRoutingSimulationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Spatially Referenced Muskingum 1D Routing Wave Progression",
    description=(
        "Executes 1D Muskingum routing for a historical high-discharge episode and maps "
        "the flood wave progression onto continuous OSM Yamuna river thalweg geometry and corridor stations. "
        "Strictly labels discharge as 1D volumetric flow (m³/s) and NEVER estimates flood inundation or water stage."
    ),
)
def get_routing_simulation_spatial(
    episode_id: str = Query(
        default="EPISODE_2023_08",
        description="Historical episode ID to route (e.g. EPISODE_2019_04, EPISODE_2022_07, EPISODE_2023_08)",
    ),
    K_hours: float = Query(
        default=36.0,
        ge=1.0,
        le=120.0,
        description="Muskingum storage constant K in hours (wave transit time).",
    ),
    x: float = Query(
        default=0.20,
        ge=0.0,
        le=0.50,
        description="Muskingum dimensionless weighting factor x [0.0, 0.5].",
    ),
    interval_km: float = Query(
        default=5.0,
        ge=1.0,
        le=50.0,
        description="Sampling station interval in kilometers along the river centreline.",
    ),
) -> SpatialRoutingSimulationResponse:
    try:
        return routing_service.simulate_episode_spatial(
            episode_id=episode_id,
            K_hours=K_hours,
            x=x,
            sampling_interval_km=interval_km,
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Episode not found: {str(exc)}",
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Parameter validation / numerical stability error: {str(exc)}",
        )
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Required spatial or hydrological dataset unavailable: {str(exc)}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Spatial routing simulation error: {str(exc)}",
        )



@router.get(
    "/tabletop-presets",
    response_model=TabletopPresetsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Tabletop Scenario Presets & Parameter Catalog",
    description=(
        "Returns pre-configured hypothetical hydrographs (Constant, Gradual Rise, Pulse, Sustained) "
        "and documented parameter sets (Authoritative Baseline K=36h vs Alternative Heuristic K=48h) "
        "for tabletop simulation exercises."
    ),
)
def get_tabletop_presets() -> TabletopPresetsResponse:
    try:
        return routing_service.get_tabletop_presets()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving tabletop presets: {str(exc)}",
        )


@router.post(
    "/tabletop-scenario",
    response_model=TabletopScenarioResponse,
    status_code=status.HTTP_200_OK,
    summary="Run Hypothetical Tabletop Routing Scenario Simulation",
    description=(
        "Executes a reproducible Muskingum routing simulation for an arbitrary hypothetical inflow sequence. "
        "Strictly verifies input validity, non-negativity, numerical stability (2Kx <= dt <= 2K(1-x)), "
        "and mass conservation. Explicitly labels output as uncalibrated tabletop simulation."
    ),
)
def run_tabletop_scenario(request: TabletopScenarioRequest) -> TabletopScenarioResponse:
    try:
        return routing_service.simulate_tabletop_scenario(request)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Tabletop simulation validation / numerical stability error: {str(exc)}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tabletop scenario simulation failed: {str(exc)}",
        )

