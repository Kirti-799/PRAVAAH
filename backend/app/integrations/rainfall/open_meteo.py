"""
backend/app/integrations/rainfall/open_meteo.py

Open-Meteo Spatial Catchment Rainfall Adapter.
Retrieves multi-point NWP forecast time series and instantaneous rates across
elevational nodes within the Upper Yamuna watershed.
"""

import time
from typing import Dict, List, Optional, Any
import httpx

from app.integrations.rainfall.base import (
    BaseSpatialRainfallAdapter,
    ProviderProvenanceMetadata,
    RainfallProviderAvailability,
)
from app.integrations.exceptions import (
    ProviderTimeoutError,
    ProviderUnavailableError,
)


class OpenMeteoCatchmentRainfallAdapter(BaseSpatialRainfallAdapter):
    """
    Adapter for Open-Meteo Weather API querying multiple coordinates concurrently
    covering the Hathnikund upstream basin.
    """

    BASE_URL = "https://api.open-meteo.com/v1/forecast"

    def __init__(self, client: Optional[httpx.AsyncClient] = None, timeout_seconds: float = 10.0):
        self._client = client
        self.timeout_seconds = timeout_seconds

    @property
    def provider_id(self) -> str:
        return "open_meteo_catchment"

    @property
    def provenance(self) -> ProviderProvenanceMetadata:
        return ProviderProvenanceMetadata(
            source_name="Open-Meteo API",
            product_name="Open-Meteo Catchment Forecast Ensemble (ECMWF IFS / DWD ICON)",
            product_version="v1.0 (Seamless multi-model blend)",
            data_type="NWP_FORECAST_DOWNSCALED",
            spatial_resolution="0.1° (~10 km) native grid downscaled to topography",
            temporal_resolution="Hourly",
            measurement_units="mm (precipitation depth), mm/h (rate)",
            timestamp_convention="ISO 8601 (Asia/Kolkata / UTC+05:30)",
            observation_or_forecast="FORECAST",
            publication_latency="~1-2 hours model run delay",
            licensing="Open-Meteo Terms (Attribution Required, CC-BY 4.0 for non-commercial)",
            availability_status=RainfallProviderAvailability.OPERATIONAL,
            retrieval_method="HTTP GET multi-coordinate REST query",
            access_constraints_or_blockers=None,
        )

    async def get_catchment_spatial_rainfall(
        self,
        sampling_nodes: List[Dict[str, Any]],
        forecast_days: int = 7,
    ) -> List[Dict[str, Any]]:
        """
        Executes multi-point batch query to Open-Meteo for the supplied sampling points.
        """
        if not sampling_nodes:
            return []

        lats = [str(n["lat"]) for n in sampling_nodes]
        lons = [str(n["lon"]) for n in sampling_nodes]

        params = {
            "latitude": ",".join(lats),
            "longitude": ",".join(lons),
            "current": "temperature_2m,precipitation",
            "hourly": "precipitation",
            "daily": "precipitation_sum",
            "past_days": 14,
            "forecast_days": forecast_days,
            "timezone": "Asia/Kolkata",
        }

        should_close = False
        client = self._client
        if client is None:
            client = httpx.AsyncClient(timeout=self.timeout_seconds)
            should_close = True

        try:
            resp = await client.get(self.BASE_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return [data]
            return []
        except httpx.TimeoutException:
            raise ProviderTimeoutError(self.provider_id, self.timeout_seconds)
        except Exception as exc:
            raise ProviderUnavailableError(self.provider_id, str(exc))
        finally:
            if should_close:
                await client.aclose()

    async def check_health(self) -> Dict[str, Any]:
        """Probes endpoint with a single coordinate query."""
        start = time.perf_counter()
        try:
            params = {
                "latitude": "30.317",
                "longitude": "77.585",
                "current": "precipitation",
            }
            should_close = False
            client = self._client
            if client is None:
                client = httpx.AsyncClient(timeout=self.timeout_seconds)
                should_close = True
            try:
                resp = await client.get(self.BASE_URL, params=params)
                resp.raise_for_status()
                latency_ms = (time.perf_counter() - start) * 1000.0
                return {
                    "provider_id": self.provider_id,
                    "is_healthy": True,
                    "latency_ms": round(latency_ms, 1),
                    "status_code": resp.status_code,
                }
            finally:
                if should_close:
                    await client.aclose()
        except Exception as e:
            latency_ms = (time.perf_counter() - start) * 1000.0
            return {
                "provider_id": self.provider_id,
                "is_healthy": False,
                "latency_ms": round(latency_ms, 1),
                "error": str(e),
            }

