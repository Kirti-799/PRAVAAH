"""
backend/app/schemas/weather.py

API Request and Response schemas for PRAVAAH Weather & Basemap endpoints.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.integrations.weather.schemas import (
    NormalizedCurrentWeather,
    NormalizedWeatherForecast,
    ProviderStatus,
)
from app.integrations.maps.map_config import BasemapOption


class WeatherLocation(BaseModel):
    """Corridor monitoring station or key point of interest."""
    id: str
    name: str
    latitude: float
    longitude: float
    chainage_km: Optional[float] = None
    station_type: str
    warning_level_m: Optional[float] = None
    danger_level_m: Optional[float] = None


class WeatherLocationsResponse(BaseModel):
    """Response containing predefined study corridor weather locations."""
    locations: List[WeatherLocation]
    corridor_bbox: Dict[str, float]
    default_location_id: str


class WeatherRefreshRequest(BaseModel):
    """Request payload to force refresh weather cache for a coordinate."""
    latitude: float = Field(..., ge=27.0, le=32.0, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=75.0, le=79.0, description="Longitude in decimal degrees")
    refresh_forecast: bool = True


class WeatherRefreshResponse(BaseModel):
    """Response returned upon explicit cache eviction and fresh retrieval."""
    status: str
    message: str
    current: Optional[NormalizedCurrentWeather] = None
    forecast: Optional[NormalizedWeatherForecast] = None


class BasemapCatalogResponse(BaseModel):
    """Catalog of available basemap tile providers and study extent."""
    basemaps: List[BasemapOption]
    default_basemap_id: str
    corridor_extent: Dict[str, Any]
