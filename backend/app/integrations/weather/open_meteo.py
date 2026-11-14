"""
backend/app/integrations/weather/open_meteo.py

Open-Meteo Weather API adapter for PRAVAAH.
Implements BaseWeatherAdapter with robust network error handling, rate-limit resilience,
schema validation, and strict normalization.

Official Open-Meteo API Docs: https://open-meteo.com/en/docs
"""

import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
import httpx

from app.integrations.weather.base import BaseWeatherAdapter
from app.integrations.weather.schemas import (
    NormalizedCurrentWeather,
    NormalizedWeatherForecast,
    NormalizedHourlyForecastItem,
    ProviderStatus,
    QualityStatus,
)
from app.integrations.exceptions import (
    ProviderTimeoutError,
    ProviderRateLimitError,
    ProviderUnavailableError,
    ProviderResponseValidationError,
)


class OpenMeteoAdapter(BaseWeatherAdapter):
    """
    Concrete adapter for the Open-Meteo Forecast and Current Conditions API.
    Does not require an API key for standard non-commercial usage.
    """

    DEFAULT_BASE_URL = "https://api.open-meteo.com/v1/forecast"
    DEFAULT_TIMEOUT_SECONDS = 8.0

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        client: Optional[httpx.AsyncClient] = None,
    ):
        self._base_url = base_url
        self._timeout_seconds = timeout_seconds
        self._client = client

    @property
    def provider_name(self) -> str:
        return "open_meteo"

    @property
    def base_url(self) -> str:
        return self._base_url

    async def _get_client(self) -> httpx.AsyncClient:
        """Returns existing client or a new AsyncClient instance."""
        if self._client is not None and not self._client.is_closed:
            return self._client
        return httpx.AsyncClient(timeout=self._timeout_seconds)

    async def get_current_weather(
        self,
        latitude: float,
        longitude: float,
    ) -> NormalizedCurrentWeather:
        """
        Fetch current atmospheric conditions from Open-Meteo.
        """
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,weather_code",
            "timezone": "Asia/Kolkata",
        }

        data = await self._execute_request(params)
        retrieved_at = datetime.now(timezone.utc).isoformat()

        if "current" not in data or not isinstance(data["current"], dict):
            raise ProviderResponseValidationError(
                self.provider_name, "Response missing 'current' object"
            )

        curr = data["current"]

        return NormalizedCurrentWeather(
            provider=self.provider_name,
            latitude=float(data.get("latitude", latitude)),
            longitude=float(data.get("longitude", longitude)),
            elevation_m=data.get("elevation"),
            timezone=data.get("timezone", "Asia/Kolkata"),
            retrieved_at=retrieved_at,
            is_cached=False,
            cache_age_seconds=0.0,
            temperature_c=curr.get("temperature_2m"),
            relative_humidity_pct=curr.get("relative_humidity_2m"),
            precipitation_mm=curr.get("precipitation", 0.0),
            wind_speed_kmh=curr.get("wind_speed_10m"),
            weather_code=curr.get("weather_code"),
            quality_status=QualityStatus.PROVISIONAL,
            source_reference=f"Open-Meteo Free API ({self._base_url})",
        )

    async def get_forecast(
        self,
        latitude: float,
        longitude: float,
        forecast_days: int = 3,
    ) -> NormalizedWeatherForecast:
        """
        Fetch multi-day hourly forecast time series from Open-Meteo.
        """
        # Clamp forecast days to sensible bounds (Open-Meteo supports up to 16 days)
        days = max(1, min(10, forecast_days))
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": "temperature_2m,relative_humidity_2m,precipitation,precipitation_probability,wind_speed_10m",
            "forecast_days": days,
            "timezone": "Asia/Kolkata",
        }

        data = await self._execute_request(params)
        retrieved_at = datetime.now(timezone.utc).isoformat()

        if "hourly" not in data or not isinstance(data["hourly"], dict):
            raise ProviderResponseValidationError(
                self.provider_name, "Response missing 'hourly' object"
            )

        hourly = data["hourly"]
        times: List[str] = hourly.get("time", [])
        temps: List[Optional[float]] = hourly.get("temperature_2m", [])
        precips: List[float] = hourly.get("precipitation", [])
        precip_probs: List[Optional[float]] = hourly.get("precipitation_probability", [])
        winds: List[Optional[float]] = hourly.get("wind_speed_10m", [])
        humids: List[Optional[float]] = hourly.get("relative_humidity_2m", [])

        series: List[NormalizedHourlyForecastItem] = []
        for i, t in enumerate(times):
            series.append(
                NormalizedHourlyForecastItem(
                    timestamp=t,
                    temperature_c=temps[i] if i < len(temps) else None,
                    precipitation_mm=precips[i] if i < len(precips) else 0.0,
                    precipitation_probability_pct=precip_probs[i] if i < len(precip_probs) else None,
                    wind_speed_kmh=winds[i] if i < len(winds) else None,
                    relative_humidity_pct=humids[i] if i < len(humids) else None,
                )
            )

        return NormalizedWeatherForecast(
            provider=self.provider_name,
            latitude=float(data.get("latitude", latitude)),
            longitude=float(data.get("longitude", longitude)),
            elevation_m=data.get("elevation"),
            timezone=data.get("timezone", "Asia/Kolkata"),
            retrieved_at=retrieved_at,
            is_cached=False,
            cache_age_seconds=0.0,
            forecast_days=days,
            hourly_series=series,
            source_reference=f"Open-Meteo Free API ({self._base_url})",
        )

    async def check_status(self) -> ProviderStatus:
        """
        Check reachability and response latency against Open-Meteo.
        Uses Hathnikund Barrage reference coordinates (30.31N, 77.58E).
        """
        start_time = time.perf_counter()
        now_str = datetime.now(timezone.utc).isoformat()
        try:
            params = {
                "latitude": 30.31,
                "longitude": 77.58,
                "current": "temperature_2m",
            }
            await self._execute_request(params)
            latency_ms = (time.perf_counter() - start_time) * 1000.0

            return ProviderStatus(
                provider_name=self.provider_name,
                is_available=True,
                status_code=200,
                latency_ms=round(latency_ms, 2),
                last_checked=now_str,
                notes=[
                    "Open-Meteo public forecast endpoint reachable.",
                    "No API key required; rate-limited under fair use terms (10k daily calls).",
                ],
            )
        except ProviderIntegrationError as exc:
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            return ProviderStatus(
                provider_name=self.provider_name,
                is_available=False,
                status_code=exc.status_code,
                latency_ms=round(latency_ms, 2),
                last_checked=now_str,
                notes=[str(exc)],
            )
        except Exception as exc:
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            return ProviderStatus(
                provider_name=self.provider_name,
                is_available=False,
                status_code=500,
                latency_ms=round(latency_ms, 2),
                last_checked=now_str,
                notes=[f"Unexpected error: {str(exc)}"],
            )

    async def _execute_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Internal HTTP execution helper with centralized error classification.
        """
        should_close = False
        client = self._client
        if client is None:
            client = httpx.AsyncClient(timeout=self._timeout_seconds)
            should_close = True

        try:
            response = await client.get(self._base_url, params=params)

            if response.status_code == 429:
                retry_after_hdr = response.headers.get("Retry-After")
                retry_sec = int(retry_after_hdr) if retry_after_hdr and retry_after_hdr.isdigit() else None
                raise ProviderRateLimitError(self.provider_name, retry_sec)

            if response.status_code >= 500:
                raise ProviderUnavailableError(
                    self.provider_name,
                    f"Open-Meteo returned server error HTTP {response.status_code}",
                )

            response.raise_for_status()

            try:
                return response.json()
            except Exception as e:
                raise ProviderResponseValidationError(
                    self.provider_name, f"JSON parse error: {str(e)}"
                )

        except httpx.TimeoutException:
            raise ProviderTimeoutError(self.provider_name, self._timeout_seconds)
        except httpx.NetworkError as ne:
            raise ProviderUnavailableError(
                self.provider_name, f"Network connection failed: {str(ne)}"
            )
        finally:
            if should_close:
                await client.aclose()
