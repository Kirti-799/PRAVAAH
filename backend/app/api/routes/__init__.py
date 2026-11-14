from fastapi import APIRouter
from app.api.routes.health import router as health_router
from app.api.routes.hydrology import router as hydrology_router
from app.api.routes.forecasting import router as forecasting_router
from app.api.routes.spatial import router as spatial_router
from app.api.routes.weather import router as weather_router
from app.api.routes.catchment import router as catchment_router
from app.api.routes.rainfall import router as rainfall_router
from app.api.routes.disaster import router as disaster_router
from app.api.routes.risk_assessment import router as risk_assessment_router

api_router = APIRouter()
api_router.include_router(health_router, prefix="", tags=["health"])
api_router.include_router(hydrology_router, prefix="", tags=["hydrology"])
api_router.include_router(forecasting_router, prefix="", tags=["forecasting"])
api_router.include_router(spatial_router, prefix="", tags=["spatial"])
api_router.include_router(weather_router, prefix="", tags=["weather"])
api_router.include_router(catchment_router, prefix="", tags=["catchment"])
api_router.include_router(rainfall_router, prefix="", tags=["rainfall"])
api_router.include_router(disaster_router, prefix="/disaster", tags=["disaster"])
api_router.include_router(risk_assessment_router, prefix="", tags=["assessment"])




