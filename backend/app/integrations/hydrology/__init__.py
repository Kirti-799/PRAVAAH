"""
backend/app/integrations/hydrology/__init__.py

Hydrological integrations package for PRAVAAH.
Provides interfaces and prepared adapters for CWC, India-WRIS, IMD, and NASA GPM.
"""

from app.integrations.hydrology.base import (
    BaseHydrologyAdapter,
    IntegrationReadiness,
    HydrologicalObservation,
)
from app.integrations.hydrology.cwc import CWCHydrologyAdapter
from app.integrations.hydrology.imd import IMDWeatherAdapter
from app.integrations.hydrology.nasa_gpm import NASAGPMAdapter

__all__ = [
    "BaseHydrologyAdapter",
    "IntegrationReadiness",
    "HydrologicalObservation",
    "CWCHydrologyAdapter",
    "IMDWeatherAdapter",
    "NASAGPMAdapter",
]
