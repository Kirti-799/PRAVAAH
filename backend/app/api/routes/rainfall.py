"""
backend/app/api/routes/rainfall.py

FastAPI router exposing Spatial Rainfall Intelligence and Catchment Aggregation:
- GET /api/rainfall/status: Multi-point provider connectivity and sampling grid status.
- GET /api/rainfall/catchment/current: Catchment-wide current precipitation rate and nodes.
- GET /api/rainfall/catchment/forecast: Multi-horizon (24h, 72h, 168h) accumulated rainfall forecast.
- GET /api/rainfall/catchment/history: Antecedent Precipitation Index (API-3, API-7, API-14) metrics.
- GET /api/rainfall/catchment/summary: Catchment spatial rainfall synthesis (unweighted arithmetic mean across 20 elevational nodes).
"""

from typing import Any, Dict
from fastapi import APIRouter, HTTPException, Query, status
from app.schemas.rainfall import (
    CatchmentRainfallSummaryResponse,
    RainfallStatusResponse,
)
from app.services.rainfall_service import rainfall_service

router = APIRouter(prefix="/rainfall", tags=["rainfall"])


@router.get(
    "/status",
    response_model=RainfallStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Spatial Rainfall Provider & Ingestion Status",
    description=(
        "Returns connectivity, latency, and sampling grid health for multi-point catchment rainfall queries."
    ),
)
async def get_rainfall_status() -> RainfallStatusResponse:
    try:
        return await rainfall_service.get_rainfall_status()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking rainfall provider status: {str(exc)}",
        )


@router.get(
    "/catchment/summary",
    response_model=CatchmentRainfallSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Full Catchment Spatial Rainfall Synthesis",
    description=(
        "Retrieves multi-point rainfall across 20 representative elevational nodes in the Hathnikund basin, "
        "computing catchment-mean precipitation, 24h/72h/168h accumulations, and API-3/7/14 moisture indices."
    ),
)
async def get_catchment_rainfall_summary(
    force_refresh: bool = Query(
        default=False,
        description="Whether to bypass internal 15-minute TTL cache and query Open-Meteo freshly.",
    )
) -> CatchmentRainfallSummaryResponse:
    try:
        return await rainfall_service.get_catchment_rainfall_summary(force_refresh=force_refresh)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error aggregating catchment rainfall: {str(exc)}",
        )


@router.get(
    "/catchment/current",
    status_code=status.HTTP_200_OK,
    summary="Get Catchment Current Precipitation Distribution",
    description="Returns current instantaneous precipitation rates across sampling points and catchment-average rate.",
)
async def get_catchment_current_rainfall(
    force_refresh: bool = Query(default=False)
) -> Dict[str, Any]:
    try:
        summary = await rainfall_service.get_catchment_rainfall_summary(force_refresh=force_refresh)
        return {
            "catchment_id": summary.catchment_id,
            "provider": summary.provider,
            "timestamp": summary.timestamp,
            "current_rate": summary.current_rate.model_dump(),
            "sample_grid_points": [
                {
                    "point_id": p.id,
                    "location_name": p.name,
                    "latitude": p.latitude,
                    "longitude": p.longitude,
                    "elevation_approx_m": p.elevation_m,
                    "current_precipitation_mm": p.current_mm,
                }
                for p in summary.sample_grid_points
            ],
            "spatial_coverage_percentage": summary.spatial_coverage_percentage,
            "scientific_disclaimer": summary.scientific_disclaimer,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving current catchment rainfall: {str(exc)}",
        )


@router.get(
    "/catchment/forecast",
    status_code=status.HTTP_200_OK,
    summary="Get Catchment Accumulated Rainfall Forecasts",
    description="Returns multi-horizon (24h, 72h, 168h) rainfall accumulations across the upstream basin.",
)
async def get_catchment_forecast_rainfall(
    force_refresh: bool = Query(default=False)
) -> Dict[str, Any]:
    try:
        summary = await rainfall_service.get_catchment_rainfall_summary(force_refresh=force_refresh)
        return {
            "catchment_id": summary.catchment_id,
            "provider": summary.provider,
            "timestamp": summary.timestamp,
            "accumulations": summary.accumulations.model_dump(),
            "sample_grid_points": [
                {
                    "point_id": p.id,
                    "location_name": p.name,
                    "latitude": p.latitude,
                    "longitude": p.longitude,
                    "precipitation_forecast_24h_mm": p.forecast_24h_mm,
                }
                for p in summary.sample_grid_points
            ],
            "spatial_coverage_percentage": summary.spatial_coverage_percentage,
            "scientific_disclaimer": summary.scientific_disclaimer,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving forecast catchment accumulations: {str(exc)}",
        )


@router.get(
    "/catchment/history",
    status_code=status.HTTP_200_OK,
    summary="Get Catchment Antecedent Precipitation Indices (API)",
    description="Returns antecedent moisture indices API-3, API-7, and API-14 with exponential daily decay (k=0.85).",
)
async def get_catchment_history_rainfall(
    force_refresh: bool = Query(default=False)
) -> Dict[str, Any]:
    try:
        summary = await rainfall_service.get_catchment_rainfall_summary(force_refresh=force_refresh)
        return {
            "catchment_id": summary.catchment_id,
            "provider": summary.provider,
            "timestamp": summary.timestamp,
            "antecedent_indices": summary.antecedent_indices.model_dump(),
            "decay_coefficient_k": summary.antecedent_indices.decay_factor_k,
            "sample_grid_points": [
                {
                    "point_id": p.id,
                    "location_name": p.name,
                    "latitude": p.latitude,
                    "longitude": p.longitude,
                    "api_3_mm": p.api_3_mm,
                }
                for p in summary.sample_grid_points
            ],
            "scientific_disclaimer": summary.scientific_disclaimer,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving antecedent precipitation history: {str(exc)}",
        )
