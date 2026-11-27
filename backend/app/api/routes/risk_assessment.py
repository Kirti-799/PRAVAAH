"""backend/app/api/routes/risk_assessment.py

FastAPI router exposing simplified flood risk assessment endpoints for PRAVAAH:
- GET /api/assessment/areas: Predefined authentic geographical areas.
- POST /api/assessment/assess: Simplified, AI-powered flood risk assessment.
"""

from fastapi import APIRouter, HTTPException, status
from app.schemas.risk_assessment import (
    SupportedAreasResponse,
    AssessmentRequest,
    AssessmentResponse,
)
from app.services.risk_assessment_service import risk_assessment_service

router = APIRouter(prefix="/assessment", tags=["assessment"])


@router.get(
    "/areas",
    response_model=SupportedAreasResponse,
    summary="Supported Geographical Areas",
    description="Lists authentic geographical areas along the Yamuna corridor available for flood risk assessment.",
)
def get_supported_areas() -> SupportedAreasResponse:
    try:
        return risk_assessment_service.get_supported_areas()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load supported areas: {str(exc)}",
        )


@router.post(
    "/assess",
    response_model=AssessmentResponse,
    summary="Assess 24-Hour Flood Risk",
    description="Assesses potential flood risk for a selected area over the next 24 hours using upstream ML inflow prediction, weather forecasts, and hydrodynamic reach attenuation.",
)
async def assess_flood_risk(request: AssessmentRequest) -> AssessmentResponse:
    try:
        return await risk_assessment_service.assess_risk(request)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Risk assessment calculation failed: {str(exc)}",
        )

