"""
backend/app/integrations/weather/schemas.py

Internal normalized data schemas for weather integrations in PRAVAAH.
Enforces strict decoupling between external provider formats (Open-Meteo, IMD, NASA GPM)
and internal domain services or API responses.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ObservationOrForecast(str, Enum):
    OBSERVATION = "OBSERVATION"
    CURRENT_CONDITION = "CURRENT_CONDITION"
    FORECAST = "FORECAST"


class QualityStatus(str, Enum):
    VERIFIED = "VERIFIED"
    PROVISIONAL = "PROVISIONAL"
    ESTIMATED = "ESTIMATED"
    UNVALIDATED = "UNVALIDATED"


class WeatherVariableRecord(BaseModel):
    """Normalized schema for an individual meteorological parameter."""
    provider: str
    variable: str
    value: float
    unit: str
    latitude: float
    longitude: float
    timestamp: str  # ISO 8601 formatted string with timezone
    timezone: str
    observation_or_forecast: ObservationOrForecast
    retrieved_at: str
    source_reference: str
    quality_status: QualityStatus = QualityStatus.PROVISIONAL


class NormalizedCurrentWeather(BaseModel):
    """Normalized current atmospheric conditions at a target coordinate."""
    provider: str
    latitude: float
    longitude: float
    elevation_m: Optional[float] = None
    timezone: str
    retrieved_at: str
    is_cached: bool = False
    cache_age_seconds: float = 0.0
    temperature_c: Optional[float] = None
    relative_humidity_pct: Optional[float] = None
    precipitation_mm: Optional[float] = None
    wind_speed_kmh: Optional[float] = None
    weather_code: Optional[int] = None
    quality_status: QualityStatus = QualityStatus.PROVISIONAL
    source_reference: str
    scientific_disclaimer: str = (
        "Current meteorological condition reported by provider. "
        "Does NOT constitute an official flood warning or river discharge estimate."
    )


class NormalizedHourlyForecastItem(BaseModel):
    """Forecast metrics for an individual hourly time step."""
    timestamp: str
    temperature_c: Optional[float] = None
    precipitation_mm: float = 0.0
    precipitation_probability_pct: Optional[float] = None
    wind_speed_kmh: Optional[float] = None
    relative_humidity_pct: Optional[float] = None


class NormalizedWeatherForecast(BaseModel):
    """Normalized multi-day meteorological forecast series."""
    provider: str
    latitude: float
    longitude: float
    elevation_m: Optional[float] = None
    timezone: str
    retrieved_at: str
    is_cached: bool = False
    cache_age_seconds: float = 0.0
    forecast_days: int
    hourly_series: List[NormalizedHourlyForecastItem]
    source_reference: str
    scientific_disclaimer: str = (
        "METEOROLOGICAL FORECAST ONLY: Point precipitation forecast does NOT denote basin-wide rainfall. "
        "Precipitation does NOT directly establish river discharge or flood inundation depth."
    )


class ProviderStatus(BaseModel):
    """Health, latency, and connectivity status of an external provider."""
    provider_name: str
    is_available: bool
    status_code: Optional[int] = None
    latency_ms: Optional[float] = None
    last_checked: str
    rate_limit_remaining: Optional[int] = None
    notes: List[str] = Field(default_factory=list)
