"""
backend/app/services/weather_service.py

Domain service for meteorological data ingestion, caching, and spatial validation in PRAVAAH.
Decouples FastAPI route handlers from provider adapters and enforces caching TTL guardrails.
"""

import time
from datetime import datetime, timezone
from typing import Dict, Tuple, Optional, Any, List

from app.integrations.weather.base import BaseWeatherAdapter
from app.integrations.weather.open_meteo import OpenMeteoAdapter
from app.integrations.weather.schemas import (
    NormalizedCurrentWeather,
    NormalizedWeatherForecast,
    ProviderStatus,
)
from app.schemas.weather import (
    WeatherLocation,
    WeatherLocationsResponse,
)
from app.integrations.maps.map_config import StudyCorridorExtent


class WeatherCacheEntry:
    """Wrapper holding cached payload and creation timestamp."""
    def __init__(self, data: Any, timestamp: float):
        self.data = data
        self.timestamp = timestamp

    @property
    def age_seconds(self) -> float:
        return time.time() - self.timestamp

    def is_expired(self, ttl_seconds: float) -> bool:
        return self.age_seconds > ttl_seconds


class WeatherService:
    """
    Service coordinating weather provider adapters, memory TTL caching,
    coordinate validation against the study corridor, and location presets.
    """

    DEFAULT_TTL_SECONDS = 900.0  # 15 minutes TTL

    def __init__(
        self,
        adapter: Optional[BaseWeatherAdapter] = None,
        ttl_seconds: float = DEFAULT_TTL_SECONDS,
    ):
        self.adapter = adapter or OpenMeteoAdapter()
        self.ttl_seconds = ttl_seconds
        self._current_cache: Dict[Tuple[float, float], WeatherCacheEntry] = {}
        self._forecast_cache: Dict[Tuple[float, float, int], WeatherCacheEntry] = {}
        self._extent = StudyCorridorExtent()

    def _coord_key(self, lat: float, lon: float) -> Tuple[float, float]:
        """Normalize coordinates to 2 decimal places (~1.1 km precision) for cache hits."""
        return (round(lat, 2), round(lon, 2))

    def validate_coordinates(self, lat: float, lon: float) -> Tuple[bool, Optional[str]]:
        """
        Validate whether coordinates fall within or near the Yamuna study corridor.
        Allows a 0.25-degree buffer around the strict study area bounds.
        """
        buffer = 0.25
        min_lon = self._extent.west - buffer
        max_lon = self._extent.east + buffer
        min_lat = self._extent.south - buffer
        max_lat = self._extent.north + buffer

        if not (min_lat <= lat <= max_lat and min_lon <= lon <= max_lon):
            return (
                False,
                f"Coordinates ({lat:.4f}, {lon:.4f}) are outside the PRAVAAH study corridor "
                f"bounds [{min_lat:.2f}N - {max_lat:.2f}N, {min_lon:.2f}E - {max_lon:.2f}E].",
            )
        return True, None

    async def get_current_weather(
        self,
        latitude: float,
        longitude: float,
        force_refresh: bool = False,
    ) -> NormalizedCurrentWeather:
        """
        Retrieve current weather with cache look-through.
        """
        key = self._coord_key(latitude, longitude)

        if not force_refresh and key in self._current_cache:
            entry = self._current_cache[key]
            if not entry.is_expired(self.ttl_seconds):
                cached_data: NormalizedCurrentWeather = entry.data.model_copy()
                cached_data.is_cached = True
                cached_data.cache_age_seconds = round(entry.age_seconds, 1)
                return cached_data

        # Fresh retrieval via adapter
        fresh = await self.adapter.get_current_weather(latitude, longitude)
        fresh.is_cached = False
        fresh.cache_age_seconds = 0.0

        # Update cache
        self._current_cache[key] = WeatherCacheEntry(fresh, time.time())
        return fresh

    async def get_forecast(
        self,
        latitude: float,
        longitude: float,
        forecast_days: int = 3,
        force_refresh: bool = False,
    ) -> NormalizedWeatherForecast:
        """
        Retrieve multi-day weather forecast with cache look-through.
        """
        days = max(1, min(10, forecast_days))
        coord = self._coord_key(latitude, longitude)
        key = (coord[0], coord[1], days)

        if not force_refresh and key in self._forecast_cache:
            entry = self._forecast_cache[key]
            if not entry.is_expired(self.ttl_seconds):
                cached_data: NormalizedWeatherForecast = entry.data.model_copy()
                cached_data.is_cached = True
                cached_data.cache_age_seconds = round(entry.age_seconds, 1)
                return cached_data

        # Fresh retrieval via adapter
        fresh = await self.adapter.get_forecast(latitude, longitude, days)
        fresh.is_cached = False
        fresh.cache_age_seconds = 0.0

        # Update cache
        self._forecast_cache[key] = WeatherCacheEntry(fresh, time.time())
        return fresh

    async def check_status(self) -> ProviderStatus:
        """Check status of current weather adapter."""
        return await self.adapter.check_status()

    def get_locations(self) -> WeatherLocationsResponse:
        """Return predefined reference monitoring locations along the corridor."""
        locations = [
            WeatherLocation(
                id=loc_id,
                name=info["name"],
                latitude=info["latitude"],
                longitude=info["longitude"],
                chainage_km=info.get("chainage_km"),
                station_type=info["type"],
                warning_level_m=info.get("warning_level_m"),
                danger_level_m=info.get("danger_level_m"),
            )
            for loc_id, info in self._extent.reference_stations.items()
        ]

        return WeatherLocationsResponse(
            locations=locations,
            corridor_bbox={
                "west": self._extent.west,
                "east": self._extent.east,
                "south": self._extent.south,
                "north": self._extent.north,
            },
            default_location_id="DELHI_OLD_RAILWAY_BRIDGE",
        )

    def clear_cache(self) -> None:
        """Evict all cached current and forecast entries."""
        self._current_cache.clear()
        self._forecast_cache.clear()


# Global Singleton for use in FastAPI dependency injection
weather_service = WeatherService()
