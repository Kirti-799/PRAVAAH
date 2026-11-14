"""
backend/app/api/routes/weather.py

FastAPI router exposing external weather and basemap data integration endpoints for PRAVAAH:
- GET /api/weather/status: Provider connectivity, latency, and operational health.
- GET /api/weather/current: Current atmospheric observations/conditions for target coordinates.
- GET /api/weather/forecast: Hourly meteorological forecast time series (1-7 days).
- GET /api/weather/locations: Predefined monitoring stations along the Yamuna corridor.
- POST /api/weather/refresh: Explicit cache eviction and fresh provider query.
- GET /api/weather/basemap/config: Available basemap tile providers and study area extent.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.weather import (
    WeatherLocationsResponse,
    WeatherRefreshRequest,
    WeatherRefreshResponse,
    BasemapCatalogResponse,
)
from app.integrations.weather.schemas import (
    NormalizedCurrentWeather,
    NormalizedWeatherForecast,
    ProviderStatus,
)
from app.integrations.maps.map_config import (
    BASEMAP_CATALOG,
    StudyCorridorExtent,
)
from app.services.weather_service import weather_service
from app.integrations.exceptions import (
    ProviderTimeoutError,
    ProviderRateLimitError,
    ProviderUnavailableError,
    ProviderResponseValidationError,
    ProviderIntegrationError,
)

router = APIRouter(prefix="/weather", tags=["weather"])


@router.get(
    "/status",
    response_model=ProviderStatus,
    summary="External Weather Provider Health & Status",
    description="Reports connectivity, response latency, and rate-limit status for Open-Meteo.",
)
async def get_weather_status() -> ProviderStatus:
    try:
        return await weather_service.check_status()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Unable to query weather provider health: {str(exc)}",
        )


@router.get(
    "/locations",
    response_model=WeatherLocationsResponse,
    summary="Corridor Hydrometeorological Reference Locations",
    description="Predefined reference stations along the Hathnikund-to-Delhi corridor.",
)
def get_corridor_locations() -> WeatherLocationsResponse:
    return weather_service.get_locations()


@router.get(
    "/basemap/config",
    response_model=BasemapCatalogResponse,
    summary="Basemap Tile Catalog & Spatial Bounds",
    description="Lists configured basemap options and Yamuna corridor extent.",
)
def get_basemap_config() -> BasemapCatalogResponse:
    extent = StudyCorridorExtent()
    return BasemapCatalogResponse(
        basemaps=BASEMAP_CATALOG,
        default_basemap_id="osm_standard",
        corridor_extent={
            "west": extent.west,
            "east": extent.east,
            "south": extent.south,
            "north": extent.north,
            "center": [extent.center_lat, extent.center_lon],
            "default_zoom": extent.default_zoom,
        },
    )


@router.get(
    "/current",
    response_model=NormalizedCurrentWeather,
    summary="Current Meteorological Conditions",
    description="Retrieves current atmospheric conditions for a target coordinate within the study corridor.",
)
async def get_current_weather(
    lat: float = Query(28.66, ge=27.0, le=32.0, description="Latitude in decimal degrees (default: Delhi ORB)"),
    lon: float = Query(77.25, ge=75.0, le=79.0, description="Longitude in decimal degrees (default: Delhi ORB)"),
    force_refresh: bool = Query(False, description="Bypass cache and force fresh query to provider"),
) -> NormalizedCurrentWeather:
    valid, err_msg = weather_service.validate_coordinates(lat, lon)
    if not valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)

    try:
        return await weather_service.get_current_weather(lat, lon, force_refresh=force_refresh)
    except ProviderTimeoutError as e:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=str(e))
    except ProviderRateLimitError as e:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e))
    except (ProviderUnavailableError, ProviderResponseValidationError) as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    except ProviderIntegrationError as e:
        raise HTTPException(status_code=e.status_code or 502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected weather retrieval error: {str(e)}")


@router.get(
    "/forecast",
    response_model=NormalizedWeatherForecast,
    summary="Meteorological Hourly Forecast",
    description="Retrieves hourly forecast time series for a coordinate. Maximum 7 days.",
)
async def get_weather_forecast(
    lat: float = Query(28.66, ge=27.0, le=32.0, description="Latitude in decimal degrees (default: Delhi ORB)"),
    lon: float = Query(77.25, ge=75.0, le=79.0, description="Longitude in decimal degrees (default: Delhi ORB)"),
    days: int = Query(3, ge=1, le=7, description="Number of forecast days (1-7)"),
    force_refresh: bool = Query(False, description="Bypass cache and force fresh query to provider"),
) -> NormalizedWeatherForecast:
    valid, err_msg = weather_service.validate_coordinates(lat, lon)
    if not valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)

    try:
        return await weather_service.get_forecast(lat, lon, forecast_days=days, force_refresh=force_refresh)
    except ProviderTimeoutError as e:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=str(e))
    except ProviderRateLimitError as e:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e))
    except (ProviderUnavailableError, ProviderResponseValidationError) as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    except ProviderIntegrationError as e:
        raise HTTPException(status_code=e.status_code or 502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected forecast retrieval error: {str(e)}")


@router.post(
    "/refresh",
    response_model=WeatherRefreshResponse,
    summary="Force Refresh Weather Cache",
    description="Invalidates cached weather data for the specified coordinate and queries provider directly.",
)
async def refresh_weather_cache(request: WeatherRefreshRequest) -> WeatherRefreshResponse:
    valid, err_msg = weather_service.validate_coordinates(request.latitude, request.longitude)
    if not valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)

    try:
        current = await weather_service.get_current_weather(
            request.latitude, request.longitude, force_refresh=True
        )
        forecast = None
        if request.refresh_forecast:
            forecast = await weather_service.get_forecast(
                request.latitude, request.longitude, forecast_days=3, force_refresh=True
            )

        return WeatherRefreshResponse(
            status="SUCCESS",
            message=f"Cache refreshed for ({request.latitude:.2f}, {request.longitude:.2f})",
            current=current,
            forecast=forecast,
        )
    except ProviderIntegrationError as e:
        raise HTTPException(status_code=e.status_code or 502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache refresh failed: {str(e)}")
