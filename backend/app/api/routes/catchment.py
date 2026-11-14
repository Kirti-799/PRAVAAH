"""
backend/app/api/routes/catchment.py

FastAPI router exposing Hathnikund Upstream Catchment and Drainage endpoints:
- GET /api/spatial/catchment/status: Inventory, readiness, and DEM coverage status.
- GET /api/spatial/catchment/summary: Morphometric metrics, hypsometry, and caveats.
- GET /api/spatial/catchment/geometry: GeoJSON FeatureCollection of watershed boundary.
- GET /api/spatial/catchment/drainage: GeoJSON FeatureCollection of stream network.
"""

from typing import Any, Dict
from fastapi import APIRouter, HTTPException, status
from app.schemas.catchment import (
    CatchmentStatusResponse,
    CatchmentSummaryResponse,
)
from app.services.catchment_service import catchment_service

router = APIRouter(prefix="/spatial/catchment", tags=["catchment"])


@router.get(
    "/status",
    response_model=CatchmentStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Upstream Catchment Infrastructure Status",
    description=(
        "Returns operational status of the Hathnikund catchment delineation engine, "
        "including acquired Copernicus GLO-30 DEM tile count and pour-point alignment."
    ),
)
def get_catchment_status() -> CatchmentStatusResponse:
    try:
        return catchment_service.get_catchment_status()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving catchment status: {str(exc)}",
        )


@router.get(
    "/summary",
    response_model=CatchmentSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Catchment Morphometry & Hypsometric Distribution",
    description=(
        "Returns authoritative morphometric summary of the 11,112 km² Hathnikund basin: "
        "elevation statistics (min 295m, max 6,387m), hypsometric percentiles, and drainage density."
    ),
)
def get_catchment_summary() -> CatchmentSummaryResponse:
    try:
        return catchment_service.get_catchment_summary()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving catchment summary: {str(exc)}",
        )


@router.get(
    "/geometry",
    status_code=status.HTTP_200_OK,
    summary="Get Catchment Boundary GeoJSON",
    description=(
        "Returns the delineated upstream watershed boundary as an RFC 7946 GeoJSON FeatureCollection. "
        "Coordinates in EPSG:4326. Explicitly covers the Himalayan drainage basin."
    ),
)
def get_catchment_geometry() -> Dict[str, Any]:
    try:
        return catchment_service.get_catchment_geometry()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error loading catchment geometry GeoJSON: {str(exc)}",
        )


@router.get(
    "/drainage",
    status_code=status.HTTP_200_OK,
    summary="Get Contributing Drainage Network GeoJSON",
    description=(
        "Returns DEM-extracted and verified stream channels (Yamuna, Tons, Pabbar, Giri, Asan) "
        "as a GeoJSON FeatureCollection in EPSG:4326."
    ),
)
def get_catchment_drainage() -> Dict[str, Any]:
    try:
        return catchment_service.get_catchment_drainage()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error loading catchment drainage GeoJSON: {str(exc)}",
        )
