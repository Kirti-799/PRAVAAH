"""
backend/app/integrations/weather/__init__.py

Weather integrations package for PRAVAAH.
Provides normalized schemas, base adapter abstractions, and concrete provider implementations.
"""

from app.integrations.weather.schemas import (
    ObservationOrForecast,
    QualityStatus,
    WeatherVariableRecord,
    NormalizedCurrentWeather,
    NormalizedHourlyForecastItem,
    NormalizedWeatherForecast,
    ProviderStatus,
)
from app.integrations.weather.base import BaseWeatherAdapter
from app.integrations.weather.open_meteo import OpenMeteoAdapter

__all__ = [
    "ObservationOrForecast",
    "QualityStatus",
    "WeatherVariableRecord",
    "NormalizedCurrentWeather",
    "NormalizedHourlyForecastItem",
    "NormalizedWeatherForecast",
    "ProviderStatus",
    "BaseWeatherAdapter",
    "OpenMeteoAdapter",
]
