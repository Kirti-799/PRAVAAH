from fastapi import APIRouter
from app.core.config import settings
from app.schemas.health import HealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=200,
    summary="Health Check",
    description="Returns the operational status and metadata of the PRAVAAH API.",
)
def get_health() -> HealthResponse:
    """
    Returns basic service health status.
    In Phase 0, this checks that the API application is running and accessible.
    """
    return HealthResponse(
        status="ok",
        service=settings.PROJECT_NAME,
        version=settings.VERSION,
    )
