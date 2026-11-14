"""
backend/app/integrations/hydrology/imd.py

India Meteorological Department (IMD) Adapter (Prepared Interface).
Prepares integration architecture for official Indian meteorological observations,
gridded rainfall datasets (0.25 deg), and severe weather warnings.

STATUS: PREPARED_FOR_FUTURE_INTEGRATION (Phase 3C)
IMPORTANT:
- IMD does not provide a public open JSON REST API without authorization or academic MOUs.
- Severe weather bulletins and gridded binary datasets (.grd) require specialized ingestion.
- Never fabricates IMD responses. Missing data remains explicitly missing.
"""

from typing import Optional, List, Dict, Any
from app.integrations.hydrology.base import (
    IntegrationReadiness,
)
from app.integrations.weather.base import BaseWeatherAdapter
from app.integrations.weather.schemas import (
    NormalizedCurrentWeather,
    NormalizedWeatherForecast,
    ProviderStatus,
)


class IMDWeatherAdapter(BaseWeatherAdapter):
    """
    Prepared adapter for India Meteorological Department (IMD) observation & warning services.
    """

    @property
    def provider_name(self) -> str:
        return "imd_india"

    @property
    def base_url(self) -> str:
        return "https://mausam.imd.gov.in/api"  # Target reference URL

    @property
    def readiness_status(self) -> IntegrationReadiness:
        return IntegrationReadiness.PREPARED_FOR_FUTURE_INTEGRATION

    async def get_current_weather(
        self,
        latitude: float,
        longitude: float,
    ) -> NormalizedCurrentWeather:
        raise NotImplementedError(
            "IMD live API integration is prepared for a future phase. "
            "Requires official API authorization or gridded netCDF/GRIB parsing."
        )

    async def get_forecast(
        self,
        latitude: float,
        longitude: float,
        forecast_days: int = 3,
    ) -> NormalizedWeatherForecast:
        raise NotImplementedError(
            "IMD district forecast integration is prepared for a future phase."
        )

    async def check_status(self) -> ProviderStatus:
        return ProviderStatus(
            provider_name=self.provider_name,
            is_available=False,
            status_code=None,
            latency_ms=None,
            last_checked="N/A",
            notes=[
                "Status: PREPARED_FOR_FUTURE_INTEGRATION",
                "Official IMD data requires enterprise API key or gridded pipeline integration.",
            ],
        )
