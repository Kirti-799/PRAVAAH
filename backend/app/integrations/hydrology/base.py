"""
backend/app/integrations/hydrology/base.py

Abstract Base Class defining the contract for external hydrological data providers.
Prepares interfaces for CWC (Central Water Commission), India-WRIS, IMD, and NASA GPM.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class IntegrationReadiness(str, Enum):
    IMPLEMENTED = "IMPLEMENTED"
    PARTIALLY_IMPLEMENTED = "PARTIALLY_IMPLEMENTED"
    PREPARED_FOR_FUTURE_INTEGRATION = "PREPARED_FOR_FUTURE_INTEGRATION"
    NOT_AVAILABLE = "NOT_AVAILABLE"


class HydrologicalObservation(BaseModel):
    """Schema for river water level, discharge, or barrage flow observations."""
    station_id: str
    station_name: str
    river_name: str
    latitude: float
    longitude: float
    timestamp: str
    water_level_m: Optional[float] = None
    discharge_cumecs: Optional[float] = None
    warning_level_m: Optional[float] = None
    danger_level_m: Optional[float] = None
    hfl_m: Optional[float] = None  # Highest Flood Level
    source_agency: str
    quality_status: str = "OFFICIAL_PROVISIONAL"


class BaseHydrologyAdapter(ABC):
    """Abstract interface for river gauge and hydrological data sources."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @property
    @abstractmethod
    def readiness_status(self) -> IntegrationReadiness:
        pass

    @abstractmethod
    async def get_station_observation(
        self,
        station_id: str,
    ) -> Optional[HydrologicalObservation]:
        """Fetch latest gauge water level or discharge for an official station."""
        pass

    @abstractmethod
    async def get_study_corridor_stations(self) -> List[Dict[str, Any]]:
        """List known monitoring stations along the Upper-to-Middle Yamuna corridor."""
        pass
