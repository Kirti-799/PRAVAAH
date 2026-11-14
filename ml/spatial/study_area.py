"""
ml/spatial/study_area.py

Study Area Metadata Contract, Coordinate Reference System (CRS) Management,
and Bounding Geometry Validation for PRAVAAH.

SCIENTIFIC INTEGRITY ENFORCEMENT:
- The study area is strictly documented as a RECTANGULAR BOUNDING EXTENT,
  NOT an empirical watershed boundary or calibrated floodplain zone.
- Never fabricates a natural catchment perimeter without surveyed hydrology.
- Enforces strict CRS discipline:
  * Geographic operations: EPSG:4326 (WGS 84, angular units in degrees).
  * Metric / Distance / Area / Slope operations: EPSG:32643 (WGS 84 / UTM Zone 43N, linear units in meters).
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple


class GeometryType(str, Enum):
    POLYGON = "Polygon"
    RECTANGULAR_EXTENT = "Rectangular Bounding Box"


@dataclass(frozen=True)
class StudyAreaBounds:
    """Bounding box coordinates for the study extent in EPSG:4326."""
    west_lon: float   # min longitude (deg)
    south_lat: float  # min latitude (deg)
    east_lon: float   # max longitude (deg)
    north_lat: float  # max latitude (deg)

    def to_list(self) -> List[float]:
        """Returns bounds in standard [min_lon, min_lat, max_lon, max_lat] order."""
        return [self.west_lon, self.south_lat, self.east_lon, self.north_lat]

    def to_geojson_polygon(self) -> Dict[str, Any]:
        """Generates GeoJSON Polygon geometry following [lon, lat] coordinate ordering."""
        return {
            "type": "Polygon",
            "coordinates": [[
                [self.west_lon, self.south_lat],
                [self.east_lon, self.south_lat],
                [self.east_lon, self.north_lat],
                [self.west_lon, self.north_lat],
                [self.west_lon, self.south_lat],  # Closed ring
            ]],
        }

    def validate(self) -> None:
        """Validates bounding box coordinate validity and orientation."""
        if not (-180.0 <= self.west_lon <= 180.0):
            raise ValueError(f"Invalid west_lon {self.west_lon}: must be between -180 and 180 degrees.")
        if not (-180.0 <= self.east_lon <= 180.0):
            raise ValueError(f"Invalid east_lon {self.east_lon}: must be between -180 and 180 degrees.")
        if not (-90.0 <= self.south_lat <= 90.0):
            raise ValueError(f"Invalid south_lat {self.south_lat}: must be between -90 and 90 degrees.")
        if not (-90.0 <= self.north_lat <= 90.0):
            raise ValueError(f"Invalid north_lat {self.north_lat}: must be between -90 and 90 degrees.")

        if self.west_lon >= self.east_lon:
            raise ValueError(
                f"Reversed longitudinal bounds: west_lon ({self.west_lon}) >= east_lon ({self.east_lon})."
            )
        if self.south_lat >= self.north_lat:
            raise ValueError(
                f"Reversed latitudinal bounds: south_lat ({self.south_lat}) >= north_lat ({self.north_lat})."
            )


@dataclass
class StudyAreaMetadata:
    """Comprehensive, scientifically guarded metadata contract for PRAVAAH study extent."""
    name: str
    description: str
    geometry_type: GeometryType
    geographic_crs: str
    projected_crs: str
    projected_crs_justification: str
    bounds: StudyAreaBounds
    reach_length_km: float
    spatial_coverage: str
    validation_status: str
    provenance: str
    scientific_limitations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        self.bounds.validate()
        return {
            "name": self.name,
            "description": self.description,
            "geometry_type": self.geometry_type.value,
            "geographic_crs": self.geographic_crs,
            "projected_crs": self.projected_crs,
            "projected_crs_justification": self.projected_crs_justification,
            "bounds": {
                "west_lon": self.bounds.west_lon,
                "south_lat": self.bounds.south_lat,
                "east_lon": self.bounds.east_lon,
                "north_lat": self.bounds.north_lat,
                "bbox_standard_order": self.bounds.to_list(),
            },
            "geojson": self.bounds.to_geojson_polygon(),
            "reach_length_km": self.reach_length_km,
            "spatial_coverage": self.spatial_coverage,
            "validation_status": self.validation_status,
            "provenance": self.provenance,
            "scientific_limitations": self.scientific_limitations,
        }


class StudyAreaCatalog:
    """Authoritative study area registry for PRAVAAH."""

    @classmethod
    def get_authoritative_study_area(cls) -> StudyAreaMetadata:
        """
        Returns the verified rectangular study extent covering Hathnikund Barrage to Delhi.
        Notice: Explicitly defined as a rectangular bounding extent, NOT a watershed boundary.
        """
        bounds = StudyAreaBounds(
            west_lon=76.85,
            south_lat=28.50,
            east_lon=77.60,
            north_lat=30.40,
        )
        bounds.validate()

        limitations = [
            "RECTANGULAR BOUNDING EXTENT — NOT A VERIFIED WATERSHED OR NATURAL BASIN BOUNDARY.",
            "This bounding box provides spatial delimitation for raster ingestion and feature indexing only.",
            "It does NOT represent a calibrated floodplain boundary, hydraulic inundation polygon, or safe zone.",
            "Geographic coordinates (EPSG:4326) are angular degrees. Distance, slope, and area operations MUST use EPSG:32643 (UTM 43N).",
        ]

        return StudyAreaMetadata(
            name="Upper-to-Middle Yamuna River Corridor Bounding Extent",
            description=(
                "Rectangular spatial bounding box enclosing the 220 km Yamuna transit reach "
                "from Hathnikund Barrage (Yamunanagar, Haryana) to Delhi Old Railway Bridge / Okhla."
            ),
            geometry_type=GeometryType.RECTANGULAR_EXTENT,
            geographic_crs="EPSG:4326 (WGS 84, angular degrees)",
            projected_crs="EPSG:32643 (WGS 84 / UTM Zone 43N, linear meters)",
            projected_crs_justification=(
                "The study corridor (76.85°E to 77.60°E) lies inside UTM Zone 43N (72°E to 78°E, "
                "central meridian 75°E). This projection preserves local scale with minimal distortion "
                "for horizontal distances, areas, and finite-difference slope gradients."
            ),
            bounds=bounds,
            reach_length_km=220.0,
            spatial_coverage="Haryana (Yamunanagar, Karnal, Panipat, Sonipat) and Delhi NCT (Central/North/East/South-East)",
            validation_status="VERIFIED_RECTANGULAR_EXTENT",
            provenance="Defined in Phase 1A feasibility study and harmonized across IMD 0.25° gridded and Haryana discharge domains.",
            scientific_limitations=limitations,
        )


def validate_spatial_bounds(west: float, south: float, east: float, north: float) -> Tuple[bool, Optional[str]]:
    """Helper utility to validate rectangular geographic bounding coordinates."""
    try:
        b = StudyAreaBounds(west_lon=west, south_lat=south, east_lon=east, north_lat=north)
        b.validate()
        return True, None
    except ValueError as exc:
        return False, str(exc)
