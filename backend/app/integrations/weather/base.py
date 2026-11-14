"""
backend/app/integrations/weather/base.py

Abstract Base Class defining the contract for all external weather data adapters.
Decouples provider-specific APIs (Open-Meteo, IMD, NASA GPM) from internal PRAVAAH services.
"""

from abc import ABC, abstractmethod
from typing import Optional
from app.integrations.weather.schemas import (
    NormalizedCurrentWeather,
    NormalizedWeatherForecast,
    ProviderStatus,
)


class BaseWeatherAdapter(ABC):
    """Abstract interface for weather data providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Unique identifier of the weather provider."""
        pass

    @property
    @abstractmethod
    def base_url(self) -> str:
        """Root endpoint URL for the external provider."""
        pass

    @abstractmethod
    async def get_current_weather(
        self,
        latitude: float,
        longitude: float,
    ) -> NormalizedCurrentWeather:
        """
        Fetch and normalize current weather observations/conditions for a coordinate.

        Args:
            latitude: Geographic latitude in decimal degrees.
            longitude: Geographic longitude in decimal degrees.

        Returns:
            NormalizedCurrentWeather containing verified parameter fields.
        """
        pass

    @abstractmethod
    async def get_forecast(
        self,
        latitude: float,
        longitude: float,
        forecast_days: int = 3,
    ) -> NormalizedWeatherForecast:
        """
        Fetch and normalize meteorological forecast time series for a coordinate.

        Args:
            latitude: Geographic latitude in decimal degrees.
            longitude: Geographic longitude in decimal degrees.
            forecast_days: Number of forecast days to request (default 3, max 7).

        Returns:
            NormalizedWeatherForecast containing hourly forecast intervals.
        """
        pass

    @abstractmethod
    async def check_status(self) -> ProviderStatus:
        """
        Check health, connectivity, and latency of the external weather API.

        Returns:
            ProviderStatus reporting availability and response latency.
        """
        pass
