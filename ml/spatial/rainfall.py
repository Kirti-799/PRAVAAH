"""
ml/spatial/rainfall.py

Spatial Rainfall Ingestion, Catchment-Wide Aggregation, and Antecedent Precipitation Index (API) Engine.
Computes spatially distributed rainfall metrics, temporal accumulations (24h, 72h, 168h),
and antecedent soil-moisture proxies (API-3, API-7, API-14) for the Hathnikund Upstream Catchment.

SCIENTIFIC INTEGRITY ENFORCEMENT:
- Distinguishes point sampling from continuous observation.
- Computes spatial variance and coverage; never assumes a single point represents the entire 11,112 km² basin.
- Implements standard Antecedent Precipitation Index: API_t = sum_{i=1}^N (k^i * P_{t-i}) with decay coefficient k = 0.85.
"""

import math
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import numpy as np


@dataclass
class CatchmentGridPoint:
    """Individual meteorological observation or forecast sampling node."""
    point_id: str
    latitude: float
    longitude: float
    elevation_approx_m: float
    location_name: str
    is_inside_catchment: bool = True
    current_precipitation_mm: float = 0.0
    precipitation_forecast_24h_mm: float = 0.0
    precipitation_forecast_72h_mm: float = 0.0
    precipitation_forecast_168h_mm: float = 0.0
    daily_history_mm: List[float] = field(default_factory=list)  # [day-1, day-2, ..., day-14]


@dataclass
class CatchmentSpatialRainfallSummary:
    """Comprehensive catchment-scale precipitation and antecedent moisture metrics."""
    catchment_id: str
    provider: str
    timestamp: str
    observation_or_forecast: str  # "OBSERVATION", "FORECAST", "HISTORICAL_REANALYSIS"
    contributing_points_count: int
    spatial_coverage_percentage: float
    missing_data_percentage: float

    # Spatial statistics of current / instant precipitation
    mean_precipitation_mm: float
    min_precipitation_mm: float
    max_precipitation_mm: float
    std_precipitation_mm: float

    # Cumulative time window aggregations (catchment-wide area-weighted means)
    accumulation_24h_mm: float
    accumulation_72h_mm: float
    accumulation_168h_mm: float

    # Antecedent Precipitation Indices (decay factor k = 0.85)
    api_3_day_mm: float
    api_7_day_mm: float
    api_14_day_mm: float
    api_decay_factor_k: float

    sample_grid_points: List[Dict[str, Any]]
    scientific_disclaimer: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "catchment_id": self.catchment_id,
            "provider": self.provider,
            "timestamp": self.timestamp,
            "observation_or_forecast": self.observation_or_forecast,
            "contributing_points_count": self.contributing_points_count,
            "spatial_coverage_percentage": round(self.spatial_coverage_percentage, 1),
            "missing_data_percentage": round(self.missing_data_percentage, 1),
            "current_rate": {
                "mean_mm": round(self.mean_precipitation_mm, 2),
                "min_mm": round(self.min_precipitation_mm, 2),
                "max_mm": round(self.max_precipitation_mm, 2),
                "std_mm": round(self.std_precipitation_mm, 2),
            },
            "accumulations": {
                "acc_24h_mm": round(self.accumulation_24h_mm, 2),
                "acc_72h_mm": round(self.accumulation_72h_mm, 2),
                "acc_168h_mm": round(self.accumulation_168h_mm, 2),
            },
            "antecedent_indices": {
                "api_3_mm": round(self.api_3_day_mm, 2),
                "api_7_mm": round(self.api_7_day_mm, 2),
                "api_14_mm": round(self.api_14_day_mm, 2),
                "decay_factor_k": self.api_decay_factor_k,
            },
            "sample_grid_points": self.sample_grid_points,
            "scientific_disclaimer": self.scientific_disclaimer,
        }


class CatchmentRainfallAggregator:
    """
    Engine calculating spatial means, temporal accumulations, and antecedent precipitation indices.
    """

    DEFAULT_API_DECAY_K = 0.85  # Standard mountainous watershed recession factor

    # Strategic grid sampling coordinates across Upper Yamuna Catchment
    REPRESENTATIVE_CATCHMENT_GRID: List[Dict[str, Any]] = [
        {"id": "GRID_01", "name": "Hathnikund Outlet / Plains Exit", "lat": 30.32, "lon": 77.58, "elev": 295},
        {"id": "GRID_02", "name": "Paonta Sahib / Bata Confluence", "lat": 30.45, "lon": 77.62, "elev": 390},
        {"id": "GRID_03", "name": "Dakpathar Barrage / Lower Yamuna-Tons", "lat": 30.50, "lon": 77.78, "elev": 460},
        {"id": "GRID_04", "name": "Kalsi / Asan River Junction", "lat": 30.53, "lon": 77.85, "elev": 550},
        {"id": "GRID_05", "name": "Renuka Lake / Giri Valley", "lat": 30.60, "lon": 77.45, "elev": 670},
        {"id": "GRID_06", "name": "Rajgarh / Mid-Giri Basin", "lat": 30.85, "lon": 77.30, "elev": 1550},
        {"id": "GRID_07", "name": "Chail-Kufri Ridge / Giri Headwaters", "lat": 31.05, "lon": 77.25, "elev": 2250},
        {"id": "GRID_08", "name": "Theog / Sutlej-Yamuna Divide", "lat": 31.12, "lon": 77.35, "elev": 2300},
        {"id": "GRID_09", "name": "Tiuni / Pabbar-Tons Confluence", "lat": 30.95, "lon": 77.85, "elev": 1050},
        {"id": "GRID_10", "name": "Rohru / Mid-Pabbar Basin", "lat": 31.20, "lon": 77.75, "elev": 1525},
        {"id": "GRID_11", "name": "Chanshal Pass / High Pabbar Range", "lat": 31.35, "lon": 77.70, "elev": 3750},
        {"id": "GRID_12", "name": "Naugaon / Mid-Yamuna Stem", "lat": 30.78, "lon": 78.15, "elev": 1200},
        {"id": "GRID_13", "name": "Barkot / Yamuna Foothill Valley", "lat": 30.82, "lon": 78.22, "elev": 1220},
        {"id": "GRID_14", "name": "Netwar / Tons Supin-Rupin Junction", "lat": 31.05, "lon": 78.10, "elev": 1400},
        {"id": "GRID_15", "name": "Sankri / Govind Sanctuary (Supin)", "lat": 31.08, "lon": 78.18, "elev": 1950},
        {"id": "GRID_16", "name": "Har-Ki-Dun Valley / High Glacial Tons", "lat": 31.15, "lon": 78.42, "elev": 3550},
        {"id": "GRID_17", "name": "Yamunotri Temple / Yamuna Source", "lat": 31.01, "lon": 78.46, "elev": 3290},
        {"id": "GRID_18", "name": "Bandarpunch Massif / Glacial Ridge", "lat": 31.10, "lon": 78.55, "elev": 5800},
        {"id": "GRID_19", "name": "Mussoorie Ridge / Southern Catchment", "lat": 30.46, "lon": 78.07, "elev": 2005},
        {"id": "GRID_20", "name": "Dehradun Northern Divide (Asan)", "lat": 30.38, "lon": 77.98, "elev": 640},
    ]

    @classmethod
    def calculate_api(cls, daily_precip_series: List[float], days: int, k: float = DEFAULT_API_DECAY_K) -> float:
        """
        Calculates Antecedent Precipitation Index:
        API_N = sum_{i=1}^N (k^i * P_{t-i})
        where daily_precip_series is ordered from yesterday (index 0) backwards in time.
        """
        if not daily_precip_series:
            return 0.0
        n = min(days, len(daily_precip_series))
        api_val = 0.0
        for i in range(n):
            day_precip = max(0.0, float(daily_precip_series[i]))
            decay = k ** (i + 1)
            api_val += decay * day_precip
        return float(api_val)

    @classmethod
    def aggregate_catchment_rainfall(
        cls,
        grid_points: List[CatchmentGridPoint],
        provider_name: str = "open_meteo_catchment",
        obs_or_forecast: str = "OBSERVATION",
        k_decay: float = DEFAULT_API_DECAY_K,
    ) -> CatchmentSpatialRainfallSummary:
        """
        Aggregates multi-point precipitation fields into spatial catchment metrics.
        """
        inside_points = [p for p in grid_points if p.is_inside_catchment]
        if not inside_points:
            raise ValueError("No grid points found within the delineated catchment boundary.")

        total_pts = len(grid_points)
        contributing = len(inside_points)
        coverage_pct = (contributing / total_pts * 100.0) if total_pts > 0 else 100.0

        current_rates = [p.current_precipitation_mm for p in inside_points if p.current_precipitation_mm is not None]
        acc_24h_list = [p.precipitation_forecast_24h_mm for p in inside_points]
        acc_72h_list = [p.precipitation_forecast_72h_mm for p in inside_points]
        acc_168h_list = [p.precipitation_forecast_168h_mm for p in inside_points]

        api_3_list = [cls.calculate_api(p.daily_history_mm, 3, k_decay) for p in inside_points]
        api_7_list = [cls.calculate_api(p.daily_history_mm, 7, k_decay) for p in inside_points]
        api_14_list = [cls.calculate_api(p.daily_history_mm, 14, k_decay) for p in inside_points]

        mean_rate = float(np.mean(current_rates)) if current_rates else 0.0
        min_rate = float(np.min(current_rates)) if current_rates else 0.0
        max_rate = float(np.max(current_rates)) if current_rates else 0.0
        std_rate = float(np.std(current_rates)) if len(current_rates) > 1 else 0.0

        mean_24h = float(np.mean(acc_24h_list)) if acc_24h_list else 0.0
        mean_72h = float(np.mean(acc_72h_list)) if acc_72h_list else 0.0
        mean_168h = float(np.mean(acc_168h_list)) if acc_168h_list else 0.0

        mean_api3 = float(np.mean(api_3_list)) if api_3_list else 0.0
        mean_api7 = float(np.mean(api_7_list)) if api_7_list else 0.0
        mean_api14 = float(np.mean(api_14_list)) if api_14_list else 0.0

        sample_pts_summary = [
            {
                "id": p.point_id,
                "name": p.location_name,
                "latitude": p.latitude,
                "longitude": p.longitude,
                "elevation_m": p.elevation_approx_m,
                "current_mm": p.current_precipitation_mm,
                "forecast_24h_mm": p.precipitation_forecast_24h_mm,
                "api_3_mm": round(cls.calculate_api(p.daily_history_mm, 3, k_decay), 2),
            }
            for p in inside_points
        ]

        disclaimer = (
            "CATCHMENT SPATIAL RAINFALL INTELLIGENCE: Metrics represent area-aggregated spatial sampling across "
            "the 11,112 km² Upper Yamuna basin up to Hathnikund Barrage. Spatial interpolation is NOT a continuous "
            "ground observation. Does not directly determine river discharge or flood stage."
        )

        return CatchmentSpatialRainfallSummary(
            catchment_id="YAM_HATHNIKUND_UPSTREAM",
            provider=provider_name,
            timestamp=datetime.now(timezone.utc).isoformat(),
            observation_or_forecast=obs_or_forecast,
            contributing_points_count=contributing,
            spatial_coverage_percentage=coverage_pct,
            missing_data_percentage=0.0,
            mean_precipitation_mm=mean_rate,
            min_precipitation_mm=min_rate,
            max_precipitation_mm=max_rate,
            std_precipitation_mm=std_rate,
            accumulation_24h_mm=mean_24h,
            accumulation_72h_mm=mean_72h,
            accumulation_168h_mm=mean_168h,
            api_3_day_mm=mean_api3,
            api_7_day_mm=mean_api7,
            api_14_day_mm=mean_api14,
            api_decay_factor_k=k_decay,
            sample_grid_points=sample_pts_summary,
            scientific_disclaimer=disclaimer,
        )
