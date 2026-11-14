"""
backend/app/integrations/rainfall/base.py

Abstract Base Class defining the contract for catchment-scale spatial rainfall providers.
Supports multi-point and gridded precipitation ingestion for the Upper Yamuna basin.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class RainfallProviderAvailability(str, Enum):
    OPERATIONAL = "OPERATIONAL"
    OFFLINE_ARCHIVE_ONLY = "OFFLINE_ARCHIVE_ONLY"
    REQUIRES_AUTHENTICATION = "REQUIRES_AUTHENTICATION"
    DEPRECATED = "DEPRECATED"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass
class ProviderProvenanceMetadata:
    """Rigorous scientific data provenance metadata adhering to Phase 3D guardrails."""
    source_name: str
    product_name: str
    product_version: str
    data_type: str  # "GAUGE_INTERPOLATED", "SATELLITE_MERGED", "NWP_FORECAST_DOWNSCALED"
    spatial_resolution: str
    temporal_resolution: str
    measurement_units: str
    timestamp_convention: str
    observation_or_forecast: str  # "OBSERVATION", "FORECAST", "HISTORICAL_REANALYSIS"
    publication_latency: str
    licensing: str
    availability_status: RainfallProviderAvailability
    retrieval_method: str
    access_constraints_or_blockers: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_name": self.source_name,
            "product_name": self.product_name,
            "product_version": self.product_version,
            "data_type": self.data_type,
            "spatial_resolution": self.spatial_resolution,
            "temporal_resolution": self.temporal_resolution,
            "measurement_units": self.measurement_units,
            "timestamp_convention": self.timestamp_convention,
            "observation_or_forecast": self.observation_or_forecast,
            "publication_latency": self.publication_latency,
            "licensing": self.licensing,
            "availability_status": self.availability_status.value,
            "retrieval_method": self.retrieval_method,
            "access_constraints_or_blockers": self.access_constraints_or_blockers,
        }


class BaseSpatialRainfallAdapter(ABC):
    """Abstract interface for all spatial precipitation ingestion adapters."""

    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Machine identifier of the provider."""
        pass

    @property
    @abstractmethod
    def provenance(self) -> ProviderProvenanceMetadata:
        """Authoritative provenance metadata and access constraints."""
        pass

    @abstractmethod
    async def get_catchment_spatial_rainfall(
        self,
        sampling_nodes: List[Dict[str, Any]],
        forecast_days: int = 7,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves spatial precipitation time series across sampling points.
        Raises ProviderIntegrationError or subclass if communication fails or provider is offline.
        """
        pass

    @abstractmethod
    async def check_health(self) -> Dict[str, Any]:
        """Performs a diagnostic probe to test provider responsiveness."""
        pass

