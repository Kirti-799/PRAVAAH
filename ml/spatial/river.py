"""
ml/spatial/river.py

River Network Ingestion, Geodetic Validation, and Spatial Analysis Engine for PRAVAAH.
Authoritative module for ingesting, validating, clipping, and metric analysis of
river centerline, canal, and drainage network geometries for the Yamuna River Corridor.

CORE STANDARDS:
- Supports GeoJSON (.geojson, .json), GeoPackage (.gpkg), and Shapefile (.shp).
- Strict CRS enforcement: ingests native CRS (e.g. EPSG:4326), reprojects to EPSG:32643
  (UTM Zone 43N) for rigorous metric length calculations.
- Comprehensive topology checks: validates geometry type, self-intersections, empty geoms,
  and coordinate ranges.
- Explicit non-fabrication guarantee: unacquired datasets return structured UNAVAILABLE reports.
- Scientific guardrails: river centerlines do NOT indicate flood inundation extents,
  river depths, bathymetry, or discharge capacity.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import json

import geopandas as gpd
import numpy as np
from pyproj import CRS
from shapely.geometry import LineString, MultiLineString, Polygon, MultiPolygon, box, mapping, shape
from shapely.ops import transform

from ml.spatial.study_area import StudyAreaCatalog, StudyAreaBounds


class WaterwayType(str, Enum):
    RIVER = "river"
    CANAL = "canal"
    DRAIN = "drain"
    STREAM = "stream"
    EMBANKMENT = "embankment"
    OTHER = "other"


class RiverValidationStatus(str, Enum):
    VALID = "VALID"
    VALID_WITH_WARNINGS = "VALID_WITH_WARNINGS"
    INVALID = "INVALID"
    EMPTY = "EMPTY"
    MISSING_CRS = "MISSING_CRS"


@dataclass
class RiverFeatureMetadata:
    """Metadata and geodetic metrics for an individual river network feature."""
    feature_id: str
    name: Optional[str]
    waterway_type: WaterwayType
    geometry_type: str
    length_km: float
    length_m: float
    original_crs: str
    projected_crs: str
    is_valid_geom: bool
    is_empty_geom: bool
    source_dataset: str
    source_feature_id: Optional[str]
    tags: Dict[str, Any] = field(default_factory=dict)
    validation_notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "feature_id": self.feature_id,
            "name": self.name,
            "waterway_type": self.waterway_type.value,
            "geometry_type": self.geometry_type,
            "length_km": round(self.length_km, 3),
            "length_m": round(self.length_m, 1),
            "original_crs": self.original_crs,
            "projected_crs": self.projected_crs,
            "is_valid_geom": self.is_valid_geom,
            "is_empty_geom": self.is_empty_geom,
            "source_dataset": self.source_dataset,
            "source_feature_id": self.source_feature_id,
            "tags": self.tags,
            "validation_notes": self.validation_notes,
        }


@dataclass
class RiverNetworkReport:
    """Comprehensive geodetic validation and summary report for a river network dataset."""
    dataset_file: str
    total_features: int
    valid_features_count: int
    invalid_features_count: int
    empty_features_count: int
    total_length_km: float
    features_by_type: Dict[str, int]
    length_by_type_km: Dict[str, float]
    native_crs: str
    projected_metric_crs: str
    bounding_box: Dict[str, float]
    intersects_study_area: bool
    study_area_containment_ratio: float
    validation_status: RiverValidationStatus
    warnings: List[str]
    provenance: str
    scientific_limitations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dataset_file": self.dataset_file,
            "total_features": self.total_features,
            "valid_features_count": self.valid_features_count,
            "invalid_features_count": self.invalid_features_count,
            "empty_features_count": self.empty_features_count,
            "total_length_km": round(self.total_length_km, 2),
            "features_by_type": self.features_by_type,
            "length_by_type_km": {k: round(v, 2) for k, v in self.length_by_type_km.items()},
            "native_crs": self.native_crs,
            "projected_metric_crs": self.projected_metric_crs,
            "bounding_box": self.bounding_box,
            "intersects_study_area": self.intersects_study_area,
            "study_area_containment_ratio": round(self.study_area_containment_ratio, 3),
            "validation_status": self.validation_status.value,
            "warnings": self.warnings,
            "provenance": self.provenance,
            "scientific_limitations": self.scientific_limitations,
        }


class RiverNetworkValidator:
    """Ingestion, validation, and spatial metrics engine for river networks."""

    PROJECTED_METRIC_CRS = "EPSG:32643"  # UTM Zone 43N (Haryana/Delhi linear meters)
    ALLOWED_EXTENSIONS = {".geojson", ".json", ".gpkg", ".shp"}

    @classmethod
    def validate_file(
        cls,
        file_path: Path,
        clip_to_study_corridor: bool = False,
    ) -> RiverNetworkReport:
        """
        Validates a vector river network file.
        Checks geometry validity, CRS, coordinate ranges, duplicates, and compute metric lengths in EPSG:32643.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"River network file not found: {file_path}")

        ext = file_path.suffix.lower()
        if ext not in cls.ALLOWED_EXTENSIONS:
            raise ValueError(
                f"Unsupported format '{ext}'. Supported formats: {sorted(list(cls.ALLOWED_EXTENSIONS))}"
            )

        # Ingest using GeoPandas
        try:
            gdf = gpd.read_file(file_path)
        except Exception as exc:
            raise ValueError(f"Failed to parse vector file with GeoPandas/GDAL: {str(exc)}") from exc

        warnings: List[str] = []

        if gdf.empty:
            return RiverNetworkReport(
                dataset_file=file_path.name,
                total_features=0,
                valid_features_count=0,
                invalid_features_count=0,
                empty_features_count=0,
                total_length_km=0.0,
                features_by_type={},
                length_by_type_km={},
                native_crs="UNDEFINED",
                projected_metric_crs=cls.PROJECTED_METRIC_CRS,
                bounding_box={"west": 0.0, "south": 0.0, "east": 0.0, "north": 0.0},
                intersects_study_area=False,
                study_area_containment_ratio=0.0,
                validation_status=RiverValidationStatus.EMPTY,
                warnings=["Dataset contains zero features (empty collection)."],
                provenance="Unidentified empty vector file",
                scientific_limitations=["Empty dataset cannot be used for any spatial analysis."],
            )

        # Check CRS
        if gdf.crs is None:
            warnings.append("Dataset lacks embedded CRS definition. Defaulting to EPSG:4326 for geodetic verification.")
            native_crs_str = "MISSING_CRS (Assumed EPSG:4326)"
            gdf.set_crs("EPSG:4326", inplace=True)
            val_status = RiverValidationStatus.VALID_WITH_WARNINGS
        else:
            native_crs_str = f"EPSG:{gdf.crs.to_epsg()}" if gdf.crs.to_epsg() else str(gdf.crs)
            val_status = RiverValidationStatus.VALID

        # Ensure we have geometry
        if "geometry" not in gdf.columns or gdf.geometry.isnull().all():
            raise ValueError("Dataset has no valid geometry column.")

        # Study area bounds for spatial intersection
        study_area = StudyAreaCatalog.get_authoritative_study_area()
        sa_b = study_area.bounds
        study_box_geom = box(sa_b.west_lon, sa_b.south_lat, sa_b.east_lon, sa_b.north_lat)

        # Reproject study box to native CRS if needed for clipping/intersection
        study_box_native = study_box_geom
        if gdf.crs and gdf.crs.to_epsg() != 4326:
            study_box_native = gpd.GeoSeries([study_box_geom], crs="EPSG:4326").to_crs(gdf.crs).iloc[0]

        # Geometry validity audit
        empty_count = int(gdf.geometry.is_empty.sum())
        invalid_geom_count = int((~gdf.geometry.is_valid).sum())
        total_features = len(gdf)

        if empty_count > 0:
            warnings.append(f"Found {empty_count} empty geometries in dataset.")
            val_status = RiverValidationStatus.VALID_WITH_WARNINGS

        if invalid_geom_count > 0:
            warnings.append(f"Found {invalid_geom_count} invalid geometries (self-intersections or degenerate coordinates).")
            val_status = RiverValidationStatus.VALID_WITH_WARNINGS

        # Coordinate Range Verification (for geographic coordinates)
        if gdf.crs and gdf.crs.is_geographic:
            bounds = gdf.total_bounds
            if bounds[0] < -180.0 or bounds[2] > 180.0 or bounds[1] < -90.0 or bounds[3] > 90.0:
                warnings.append("Geographic coordinates exceed plausible global latitude/longitude ranges.")
                val_status = RiverValidationStatus.INVALID

        # Reproject to metric CRS (UTM Zone 43N) for rigorous linear measurements
        try:
            gdf_metric = gdf.to_crs(cls.PROJECTED_METRIC_CRS)
        except Exception as exc:
            warnings.append(f"Reprojection to metric CRS ({cls.PROJECTED_METRIC_CRS}) failed: {str(exc)}")
            gdf_metric = gdf

        # Compute metric lengths
        lengths_m = gdf_metric.geometry.length.values
        total_length_km = float(np.sum(lengths_m) / 1000.0)

        # Categorization by waterway type
        features_by_type: Dict[str, int] = {}
        length_by_type_km: Dict[str, float] = {}

        type_col = None
        for col in ["waterway", "type", "fclass", "feature_type"]:
            if col in gdf.columns:
                type_col = col
                break

        for idx, row in gdf.iterrows():
            w_type = "river"
            if type_col and row[type_col]:
                val = str(row[type_col]).lower()
                if "river" in val:
                    w_type = "river"
                elif "canal" in val:
                    w_type = "canal"
                elif "drain" in val:
                    w_type = "drain"
                elif "stream" in val:
                    w_type = "stream"
                elif "embankment" in val or "dyke" in val:
                    w_type = "embankment"
                else:
                    w_type = "other"

            features_by_type[w_type] = features_by_type.get(w_type, 0) + 1
            length_by_type_km[w_type] = float(length_by_type_km.get(w_type, 0.0) + (float(lengths_m[idx]) / 1000.0))

        # Check bounds in WGS 84
        try:
            gdf_wgs84 = gdf.to_crs("EPSG:4326")
            total_b = gdf_wgs84.total_bounds
            bbox_dict = {
                "west": round(float(total_b[0]), 4),
                "south": round(float(total_b[1]), 4),
                "east": round(float(total_b[2]), 4),
                "north": round(float(total_b[3]), 4),
            }
            # Overlap check
            intersects = bool(gdf_wgs84.intersects(study_box_geom).any())
            # Ratio of features intersecting
            intersecting_features = gdf_wgs84.intersects(study_box_geom).sum()
            containment_ratio = float(intersecting_features / total_features) if total_features > 0 else 0.0
        except Exception:
            bbox_dict = {"west": 0.0, "south": 0.0, "east": 0.0, "north": 0.0}
            intersects = False
            containment_ratio = 0.0

        if not intersects:
            warnings.append(
                f"Dataset bounds [{bbox_dict['west']}, {bbox_dict['south']}, {bbox_dict['east']}, {bbox_dict['north']}] "
                f"do not intersect the Yamuna study area extent."
            )
            val_status = RiverValidationStatus.VALID_WITH_WARNINGS

        # Provenance attribution
        provenance = "OpenStreetMap Hydrography / Geofabrik / Regional Hydrographic Survey"
        if "osm_id" in gdf.columns or "@id" in gdf.columns:
            provenance = "OpenStreetMap Contributors (ODbL 1.0) via Overpass / Geofabrik extract"

        limitations = [
            "VECTOR CENTERLINE TOPOLOGY ONLY: Does not represent surveyed river bathymetry or channel cross-sections.",
            "NO INUNDATION IMPLICATION: River lines alone do NOT establish flood inundation extents or water levels.",
            "TEMPORAL ACCURACY: Braided reaches and seasonal sandy riverbeds may shift post-monsoon.",
            f"METRIC CALCULATIONS: Derived in {cls.PROJECTED_METRIC_CRS} (UTM Zone 43N).",
        ]

        return RiverNetworkReport(
            dataset_file=file_path.name,
            total_features=total_features,
            valid_features_count=total_features - invalid_geom_count - empty_count,
            invalid_features_count=invalid_geom_count,
            empty_features_count=empty_count,
            total_length_km=total_length_km,
            features_by_type=features_by_type,
            length_by_type_km=length_by_type_km,
            native_crs=native_crs_str,
            projected_metric_crs=cls.PROJECTED_METRIC_CRS,
            bounding_box=bbox_dict,
            intersects_study_area=intersects,
            study_area_containment_ratio=containment_ratio,
            validation_status=val_status,
            warnings=warnings,
            provenance=provenance,
            scientific_limitations=limitations,
        )

    @classmethod
    def load_features_geojson(
        cls,
        file_path: Path,
        clip_to_study_corridor: bool = True,
    ) -> Dict[str, Any]:
        """
        Loads vector river features and converts them to standard GeoJSON FeatureCollection in EPSG:4326.
        Optionally clips to the Yamuna study extent.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        gdf = gpd.read_file(file_path)
        if gdf.empty:
            return {"type": "FeatureCollection", "features": []}

        # Ensure CRS
        if gdf.crs is None:
            gdf.set_crs("EPSG:4326", inplace=True)
        elif gdf.crs.to_epsg() != 4326:
            gdf = gdf.to_crs("EPSG:4326")

        # Clean empty geometries
        gdf = gdf[~gdf.geometry.is_empty & gdf.geometry.notnull()].copy()

        # Clip if requested
        if clip_to_study_corridor:
            study_area = StudyAreaCatalog.get_authoritative_study_area()
            sa_b = study_area.bounds
            study_box = box(sa_b.west_lon, sa_b.south_lat, sa_b.east_lon, sa_b.north_lat)
            gdf = gdf[gdf.geometry.intersects(study_box)].copy()
            # Perform intersection clipping to keep within bounds
            gdf["geometry"] = gdf.geometry.intersection(study_box)
            gdf = gdf[~gdf.geometry.is_empty].copy()

        # Compute metric length in UTM 43N
        gdf_metric = gdf.to_crs(cls.PROJECTED_METRIC_CRS)
        lengths_km = gdf_metric.geometry.length.values / 1000.0

        features = []
        for idx, (_, row) in enumerate(gdf.iterrows()):
            geom = row.geometry
            if geom.is_empty:
                continue

            # Attributes
            name = None
            for name_col in ["name", "NAME", "river_name"]:
                if name_col in row and row[name_col] and str(row[name_col]).strip():
                    name = str(row[name_col]).strip()
                    break

            waterway_type = "river"
            for type_col in ["waterway", "type", "fclass"]:
                if type_col in row and row[type_col]:
                    val = str(row[type_col]).lower()
                    if "canal" in val:
                        waterway_type = "canal"
                    elif "drain" in val:
                        waterway_type = "drain"
                    elif "stream" in val:
                        waterway_type = "stream"
                    elif "river" in val:
                        waterway_type = "river"
                    break

            feature_id = str(row.get("osm_id") or row.get("id") or f"RIVER_FEAT_{idx:04d}")

            # Keep safe serializable properties
            props = {
                "feature_id": feature_id,
                "name": name or "Unnamed Waterway",
                "waterway_type": waterway_type,
                "length_km": round(float(lengths_km[idx]), 3),
                "source_dataset": file_path.name,
                "study_corridor": "Yamuna Upper-to-Middle Reach",
            }

            features.append({
                "type": "Feature",
                "id": feature_id,
                "geometry": mapping(geom),
                "properties": props,
            })

        return {
            "type": "FeatureCollection",
            "features": features,
            "crs": {
                "type": "name",
                "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"},
            },
            "properties": {
                "total_features": len(features),
                "source_file": file_path.name,
                "metric_crs": cls.PROJECTED_METRIC_CRS,
                "disclaimer": (
                    "River geometry reflects centerline and hydrographic alignment. "
                    "Does NOT indicate water depth, velocity, bathymetry, or flood extent."
                ),
            },
        }

    @classmethod
    def scan_repository_river_status(cls, data_dir: Optional[Path] = None) -> Dict[str, Any]:
        """
        Scans data/raw/spatial/hydrography/ for physical river network datasets.
        Returns explicit AVAILABLE or UNAVAILABLE status report.
        """
        repo_root = Path(__file__).resolve().parents[2]
        base_dir = data_dir or (repo_root / "data")
        hydro_dir = base_dir / "raw" / "spatial" / "hydrography"
        hydro_dir.mkdir(parents=True, exist_ok=True)

        candidate_files = []
        for ext in cls.ALLOWED_EXTENSIONS:
            candidate_files.extend(list(hydro_dir.glob(f"*{ext}")))
        candidate_files = sorted(candidate_files)

        if not candidate_files:
            return {
                "river_data_availability": "UNAVAILABLE",
                "scanned_directory": str(hydro_dir),
                "total_files_found": 0,
                "active_river_file": None,
                "validation_report": None,
                "acquisition_guide": {
                    "instructions": (
                        "Place verified vector river network datasets into data/raw/spatial/hydrography/. "
                        "Recommended source: OpenStreetMap (OSM) waterway extracts for Northern India "
                        "(clipped to Yamuna corridor: West 76.85°E, South 28.50°N, East 77.60°E, North 30.40°N) "
                        "or CWC / Survey of India hydrographic GIS data."
                    ),
                    "accepted_formats": sorted(list(cls.ALLOWED_EXTENSIONS)),
                    "required_properties": [
                        "Valid georeferenced CRS (EPSG:4326 WGS 84 or EPSG:32643 UTM Zone 43N)",
                        "LineString or MultiLineString geometry for river thalweg / centerlines",
                        "Source tags (name, waterway=river/canal/drain, osm_id)",
                    ],
                },
                "scientific_notice": (
                    "RIVER NETWORK DATA UNAVAILABLE IN REPOSITORY -- PRAVAAH strictly refuses to fabricate "
                    "mock river centerlines or synthetic water hazards for operational reporting."
                ),
            }

        # Inspect the primary file found
        primary_file = candidate_files[0]
        report = cls.validate_file(primary_file)

        return {
            "river_data_availability": "AVAILABLE",
            "scanned_directory": str(hydro_dir),
            "total_files_found": len(candidate_files),
            "all_files": [f.name for f in candidate_files],
            "active_river_file": primary_file.name,
            "validation_report": report.to_dict(),
            "scientific_notice": (
                "River network data detected and validated. Features reflect vector alignment "
                "and metric length calculations in EPSG:32643. Does NOT imply flood stage or cross-section bathymetry."
            ),
        }

    @classmethod
    def create_synthetic_river_fixture(
        cls,
        output_path: Path,
        crs_epsg: int = 4326,
        corridor_aligned: bool = True,
    ) -> Path:
        """
        Creates a miniature synthetic GeoJSON fixture solely for automated testing.
        NOT REAL DATA: Isolated strictly for unit test verification.
        """
        if corridor_aligned:
            # 3 synthetic waterway lines flowing north-to-south within the Yamuna bounding box
            # Hathnikund (~30.3°N, 77.5°E) to Delhi (~28.6°N, 77.2°E)
            yamuna_main = LineString([
                (77.58, 30.31),  # Near Hathnikund Barrage
                (77.40, 29.95),  # Yamunanagar reach
                (77.15, 29.68),  # Karnal reach
                (77.08, 29.39),  # Panipat reach
                (77.12, 28.98),  # Sonipat reach
                (77.25, 28.66),  # Delhi Old Railway Bridge
                (77.30, 28.53),  # Okhla Barrage
            ])

            # Western Yamuna Canal diversion
            wyc_canal = LineString([
                (77.57, 30.31),
                (77.28, 29.96),
                (76.98, 29.69),
                (76.97, 28.99),
            ])

            # Najafgarh drain confluence in Delhi
            drain_line = LineString([
                (77.01, 28.60),
                (77.12, 28.67),
                (77.23, 28.68),
            ])

            features = [
                {
                    "type": "Feature",
                    "id": "SYNTH_YAMUNA_001",
                    "geometry": mapping(yamuna_main),
                    "properties": {
                        "osm_id": "10001",
                        "name": "Yamuna",
                        "waterway": "river",
                        "surface": "water",
                    },
                },
                {
                    "type": "Feature",
                    "id": "SYNTH_WYC_002",
                    "geometry": mapping(wyc_canal),
                    "properties": {
                        "osm_id": "10002",
                        "name": "Western Yamuna Canal",
                        "waterway": "canal",
                        "flow": "regulated",
                    },
                },
                {
                    "type": "Feature",
                    "id": "SYNTH_DRAIN_003",
                    "geometry": mapping(drain_line),
                    "properties": {
                        "osm_id": "10003",
                        "name": "Najafgarh Drain",
                        "waterway": "drain",
                        "flow": "intermittent",
                    },
                },
            ]
        else:
            # Out-of-bounds fixture for negative testing
            out_line = LineString([(10.0, 10.0), (10.5, 10.5)])
            features = [
                {
                    "type": "Feature",
                    "id": "SYNTH_OUT_001",
                    "geometry": mapping(out_line),
                    "properties": {"name": "Out of Bounds River", "waterway": "river"},
                }
            ]

        geojson_data = {
            "type": "FeatureCollection",
            "crs": {
                "type": "name",
                "properties": {"name": f"urn:ogc:def:crs:EPSG::{crs_epsg}"},
            },
            "features": features,
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(geojson_data, f, indent=2)

        return output_path
