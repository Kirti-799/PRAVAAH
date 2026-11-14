"""
backend/app/integrations/maps/__init__.py

Map provider integration package for PRAVAAH.
Decouples tile layers, study corridor extent, and cartographic configurations.
"""

from app.integrations.maps.map_config import (
    BasemapOption,
    StudyCorridorExtent,
    BASEMAP_CATALOG,
    get_default_basemap,
    get_basemap_by_id,
)

__all__ = [
    "BasemapOption",
    "StudyCorridorExtent",
    "BASEMAP_CATALOG",
    "get_default_basemap",
    "get_basemap_by_id",
]
