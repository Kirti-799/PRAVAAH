"""
backend/app/integrations/maps/map_config.py

Basemap provider configuration and spatial viewport settings for PRAVAAH.
Decouples map rendering from hardcoded tile URLs and provides extensible basemap switching.
"""

import os
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class BasemapOption(BaseModel):
    """Specification for an external tile map provider."""
    id: str
    name: str
    tile_url: str
    attribution: str
    max_zoom: int = 19
    min_zoom: int = 4
    subdomains: List[str] = Field(default_factory=lambda: ["a", "b", "c"])
    is_default: bool = False
    terms_of_use_url: str
    description: str


class StudyCorridorExtent(BaseModel):
    """Authoritative study corridor boundary and reference coordinates."""
    west: float = 76.85
    east: float = 77.60
    south: float = 28.50
    north: float = 30.40
    center_lat: float = 29.45
    center_lon: float = 77.22
    default_zoom: int = 8
    reference_stations: Dict[str, Dict[str, Any]] = {
        "HATHNIKUND_BARRAGE": {
            "name": "Hathnikund Barrage (Upstream Boundary)",
            "latitude": 30.31,
            "longitude": 77.58,
            "chainage_km": 0.0,
            "type": "BARRAGE",
        },
        "YAMUNANAGAR": {
            "name": "Yamunanagar Hydrological Station",
            "latitude": 30.13,
            "longitude": 77.29,
            "chainage_km": 35.0,
            "type": "GAUGE",
        },
        "KARNAL": {
            "name": "Karnal Bridge Gauge Station",
            "latitude": 29.69,
            "longitude": 77.08,
            "chainage_km": 95.0,
            "type": "GAUGE",
        },
        "PANIPAT": {
            "name": "Panipat Embankment Watch Station",
            "latitude": 29.39,
            "longitude": 77.10,
            "chainage_km": 140.0,
            "type": "GAUGE",
        },
        "SONIPAT": {
            "name": "Sonipat Monitoring Station",
            "latitude": 28.99,
            "longitude": 77.12,
            "chainage_km": 195.0,
            "type": "GAUGE",
        },
        "DELHI_OLD_RAILWAY_BRIDGE": {
            "name": "Delhi Old Railway Bridge (ORB - Core Target)",
            "latitude": 28.66,
            "longitude": 77.25,
            "chainage_km": 240.0,
            "type": "CWC_BASE_GAUGE",
            "warning_level_m": 204.50,
            "danger_level_m": 205.33,
        },
        "OKHLA_BARRAGE": {
            "name": "Okhla Barrage (Downstream Boundary)",
            "latitude": 28.53,
            "longitude": 77.30,
            "chainage_km": 265.0,
            "type": "BARRAGE",
        },
    }


# Standard Basemap Catalog for PRAVAAH
BASEMAP_CATALOG: List[BasemapOption] = [
    BasemapOption(
        id="osm_standard",
        name="OpenStreetMap Standard",
        tile_url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors',
        max_zoom=19,
        min_zoom=4,
        is_default=True,
        terms_of_use_url="https://operations.osmfoundation.org/policies/tiles/",
        description="Standard community-maintained cartography. Free for low-to-moderate tile volume.",
    ),
    BasemapOption(
        id="carto_positron",
        name="CartoDB Positron (Light GIS)",
        tile_url=(
            f"https://{{s}}.basemaps.cartocdn.com/light_all/{{z}}/{{x}}/{{y}}{{r}}.png?api_key={os.environ.get('CARTO_API_KEY') or os.environ.get('VITE_CARTO_API_KEY')}"
            if (os.environ.get("CARTO_API_KEY") or os.environ.get("VITE_CARTO_API_KEY"))
            else "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
        ),
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
        max_zoom=19,
        min_zoom=4,
        is_default=False,
        terms_of_use_url="https://carto.com/help/working-with-data/basemaps/",
        description=(
            "Clean high-contrast light cartography. Free CARTO API key configured."
            if (os.environ.get("CARTO_API_KEY") or os.environ.get("VITE_CARTO_API_KEY"))
            else "Clean high-contrast light cartography (requires optional CARTO_API_KEY to suppress unauthenticated watermark; OpenStreetMap is active by default)."
        ),
    ),
    BasemapOption(
        id="opentopomap",
        name="OpenTopoMap (Topography)",
        tile_url="https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
        attribution='Map data: &copy; <a href="https://openstreetmap.org/copyright">OpenStreetMap</a>, SRTM | Style: &copy; <a href="http://opentopomap.org">OpenTopoMap</a>',
        max_zoom=17,
        min_zoom=4,
        is_default=False,
        terms_of_use_url="https://opentopomap.org/about",
        description="Topographic elevation contours and hillshading, useful for watershed slope visualization.",
    ),
]


def get_default_basemap() -> BasemapOption:
    """Return the default basemap configuration."""
    for b in BASEMAP_CATALOG:
        if b.is_default:
            return b
    return BASEMAP_CATALOG[0]


def get_basemap_by_id(basemap_id: str) -> Optional[BasemapOption]:
    """Retrieve basemap configuration by its identifier."""
    for b in BASEMAP_CATALOG:
        if b.id == basemap_id:
            return b
    return None
