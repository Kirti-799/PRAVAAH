"""
backend/app/integrations/rainfall/__init__.py

Package exposing catchment spatial rainfall provider adapters and provenance contracts.
"""

from app.integrations.rainfall.base import (
    BaseSpatialRainfallAdapter,
    ProviderProvenanceMetadata,
    RainfallProviderAvailability,
)
from app.integrations.rainfall.open_meteo import OpenMeteoCatchmentRainfallAdapter
from app.integrations.rainfall.imd import IMDRainfallAdapter
from app.integrations.rainfall.nasa_gpm import NASAGPMAdapter

__all__ = [
    "BaseSpatialRainfallAdapter",
    "ProviderProvenanceMetadata",
    "RainfallProviderAvailability",
    "OpenMeteoCatchmentRainfallAdapter",
    "IMDRainfallAdapter",
    "NASAGPMAdapter",
]

