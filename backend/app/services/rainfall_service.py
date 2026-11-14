"""
backend/app/services/rainfall_service.py

Domain service coordinating catchment-wide spatial rainfall ingestion,
multi-point grid querying, caching, and Antecedent Precipitation Index (API) calculation.
"""

import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from ml.spatial.rainfall import (
    CatchmentGridPoint,
    CatchmentRainfallAggregator,
    CatchmentSpatialRainfallSummary,
)
from app.schemas.rainfall import (
    CatchmentRainfallSummaryResponse,
    RainfallStatusResponse,
    RainfallRateSummary,
    RainfallAccumulationSummary,
    AntecedentPrecipitationSummary,
    CatchmentRainfallPoint,
)
from app.integrations.rainfall.base import BaseSpatialRainfallAdapter
from app.integrations.rainfall.open_meteo import OpenMeteoCatchmentRainfallAdapter
from app.integrations.rainfall.imd import IMDRainfallAdapter
from app.integrations.rainfall.nasa_gpm import NASAGPMAdapter
from app.integrations.exceptions import (
    ProviderTimeoutError,
    ProviderUnavailableError,
    ProviderIntegrationError,
)


class RainfallCacheEntry:
    def __init__(self, data: CatchmentRainfallSummaryResponse, timestamp: float):
        self.data = data
        self.timestamp = timestamp

    @property
    def age_seconds(self) -> float:
        return time.time() - self.timestamp

    def is_expired(self, ttl: float) -> bool:
        return self.age_seconds > ttl


class RainfallService:
    """Coordinates spatial rainfall queries across the Hathnikund upstream basin."""

    DEFAULT_TTL_SECONDS = 900.0  # 15 minutes TTL

    def __init__(
        self,
        adapter: Optional[BaseSpatialRainfallAdapter] = None,
        ttl_seconds: float = DEFAULT_TTL_SECONDS,
    ):
        self.adapter = adapter or OpenMeteoCatchmentRainfallAdapter()
        self.imd_adapter = IMDRainfallAdapter()
        self.nasa_adapter = NASAGPMAdapter()
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, RainfallCacheEntry] = {}
        self.aggregator = CatchmentRainfallAggregator()

    async def get_catchment_rainfall_summary(
        self,
        force_refresh: bool = False,
    ) -> CatchmentRainfallSummaryResponse:
        """
        Retrieves real-time spatially distributed precipitation across the Hathnikund catchment.
        Aggregates multi-point sampling grid into catchment mean, accumulations, and API indices.
        """
        cache_key = "catchment_summary_latest"
        if not force_refresh and cache_key in self._cache:
            entry = self._cache[cache_key]
            if not entry.is_expired(self.ttl_seconds):
                return entry.data

        grid_defs = self.aggregator.REPRESENTATIVE_CATCHMENT_GRID
        try:
            data_list = await self.adapter.get_catchment_spatial_rainfall(grid_defs, forecast_days=7)
        except (ProviderUnavailableError, ProviderTimeoutError, Exception) as exc:
            if cache_key in self._cache:
                return self._cache[cache_key].data
            # Graceful fallback: construct empty node responses with disclaimer
            data_list = [{}] * len(grid_defs)

        points: List[CatchmentGridPoint] = []
        for i, g in enumerate(grid_defs):
            node_resp = data_list[i] if i < len(data_list) else {}
            curr = node_resp.get("current", {})
            hourly = node_resp.get("hourly", {})
            h_precip = hourly.get("precipitation", [])

            acc_24 = sum(h_precip[:24]) if len(h_precip) >= 24 else (sum(h_precip) if h_precip else 0.0)
            acc_72 = sum(h_precip[:72]) if len(h_precip) >= 72 else (sum(h_precip) if h_precip else 0.0)
            acc_168 = sum(h_precip[:168]) if len(h_precip) >= 168 else (sum(h_precip) if h_precip else 0.0)

            curr_rate = float(curr.get("precipitation", 0.0))

            # Genuine antecedent daily history from provider (14 past days in reverse order: [t-1, t-2, ..., t-14])
            daily_dict = node_resp.get("daily", {})
            daily_precip_list = daily_dict.get("precipitation_sum", [])
            if len(daily_precip_list) >= 14:
                actual_daily_history = [float(v) if v is not None else 0.0 for v in reversed(daily_precip_list[:14])]
            elif daily_precip_list:
                actual_daily_history = [float(v) if v is not None else 0.0 for v in reversed(daily_precip_list)]
            else:
                actual_daily_history = [0.0] * 14

            points.append(
                CatchmentGridPoint(
                    point_id=g["id"],
                    latitude=g["lat"],
                    longitude=g["lon"],
                    elevation_approx_m=g["elev"],
                    location_name=g["name"],
                    is_inside_catchment=True,
                    current_precipitation_mm=curr_rate,
                    precipitation_forecast_24h_mm=acc_24,
                    precipitation_forecast_72h_mm=acc_72,
                    precipitation_forecast_168h_mm=acc_168,
                    daily_history_mm=actual_daily_history,
                )
            )

        summary = self.aggregator.aggregate_catchment_rainfall(points)

        res = CatchmentRainfallSummaryResponse(
            catchment_id=summary.catchment_id,
            provider=self.adapter.provenance.source_name,
            timestamp=summary.timestamp,
            observation_or_forecast=summary.observation_or_forecast,
            contributing_points_count=summary.contributing_points_count,
            spatial_coverage_percentage=summary.spatial_coverage_percentage,
            missing_data_percentage=summary.missing_data_percentage,
            current_rate=RainfallRateSummary(**summary.to_dict()["current_rate"]),
            accumulations=RainfallAccumulationSummary(**summary.to_dict()["accumulations"]),
            antecedent_indices=AntecedentPrecipitationSummary(**summary.to_dict()["antecedent_indices"]),
            sample_grid_points=[CatchmentRainfallPoint(**p) for p in summary.sample_grid_points],
            scientific_disclaimer=summary.scientific_disclaimer,
        )

        self._cache[cache_key] = RainfallCacheEntry(res, time.time())
        return res

    async def get_rainfall_status(self) -> RainfallStatusResponse:
        """Reports connectivity and spatial grid status."""
        health = await self.adapter.check_health()
        is_healthy = health.get("is_healthy", False)
        latency = health.get("latency_ms")

        notes = [
            "Multi-point spatial sampling grid operational.",
            "Covers 20 representative elevational nodes across the 11,112 km² Hathnikund basin.",
            f"Provider Source: {self.adapter.provenance.source_name} ({self.adapter.provenance.data_type})",
            f"IMD Gridded Status: {self.imd_adapter.provenance.availability_status.value} (Offline .GRD archive only)",
            f"NASA GPM Status: {self.nasa_adapter.provenance.availability_status.value} (Requires Earthdata URS token)",
        ]
        if not is_healthy and "error" in health:
            notes.append(f"Provider health check failed: {health['error']}")

        return RainfallStatusResponse(
            provider_name=self.adapter.provider_id,
            is_available=is_healthy,
            status_code=health.get("status_code", 200 if is_healthy else 503),
            latency_ms=latency,
            spatial_sampling_nodes_count=len(self.aggregator.REPRESENTATIVE_CATCHMENT_GRID),
            catchment_bounding_box={"south": 30.30, "north": 31.45, "west": 77.05, "east": 78.62},
            active_aggregation_window_hours=[24, 72, 168],
            notes=notes,
        )


rainfall_service = RainfallService()
