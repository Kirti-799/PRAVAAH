"""
ml/spatial/hydrography.py

Phase 3B: River Hydrography, Network Topology & Station Chainage Engine for PRAVAAH.
Authoritative module for validating, processing, classifying, extracting, and analyzing
river network hydrography for the Upper-to-Middle Yamuna River Corridor.

CORE CAPABILITIES:
1. Hydrography Ingestion & Geometry Validation:
   - Ingests GeoJSON, GeoPackage, and Shapefile vector hydrography.
   - Detects empty geometries, invalid shapes, coordinate bounds, and duplicates.
   - Reprojects to EPSG:32643 (UTM Zone 43N) for metric geodesic length calculations.
   - Clips features to the authoritative PRAVAAH study corridor [76.85°E–77.60°E, 28.50°N–30.40°N].
2. Evidence-Based Feature Classification:
   - Classifies waterways into Main River, Tributary, Canal, Drain/Minor Waterway,
     and Embankment based on verified source attributes (never geometry alone).
3. Main Channel Extraction & Continuity / Gap Analysis:
   - Traces Yamuna thalweg reaches, detects geometric gaps and topological breaks.
   - Reports channel continuity status (CONTINUOUS, FRAGMENTED, DISCONNECTED).
4. NetworkX Graph Representation & Topology Validation:
   - Node-edge graph representing river junctions, confluences, and reaches.
   - Analyzes connected components, isolated reaches, node degrees, cycles/braids.
   - Never assumes flow direction merely from digitization vertex order.
5. Downstream River Chainage / Stationing:
   - If geometry is continuous, derives cumulative downstream distance from Hathnikund Barrage.
   - Reports stations at regular intervals (km) and landmark reaches.
   - If geometry is disconnected, explicitly reports limitation and refuses misleading chainage.
6. Scientific Guardrails & Non-Fabrication:
   - Clear distinction between actual source data, processed data, and test fixtures.
   - Explicit disclaimers: river lines do NOT denote flood inundation extents or water depths.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import json
import math
import uuid

import geopandas as gpd
import networkx as nx
import numpy as np
from pyproj import CRS
from shapely.geometry import (
    LineString,
    MultiLineString,
    Point,
    Polygon,
    MultiPolygon,
    box,
    mapping,
    shape,
)
from shapely.ops import linemerge, substring, transform

from ml.spatial.study_area import StudyAreaCatalog, StudyAreaBounds


class HydrographyClass(str, Enum):
    MAIN_RIVER = "main_river"
    TRIBUTARY = "tributary"
    CANAL = "canal"
    DRAIN_MINOR = "drain_minor"
    EMBANKMENT = "embankment"
    AMBIGUOUS = "ambiguous"


class ChannelContinuityStatus(str, Enum):
    CONTINUOUS = "CONTINUOUS"
    FRAGMENTED = "FRAGMENTED"
    DISCONNECTED = "DISCONNECTED"
    UNAVAILABLE = "UNAVAILABLE"


class HydrographyValidationStatus(str, Enum):
    VALID = "VALID"
    VALID_WITH_WARNINGS = "VALID_WITH_WARNINGS"
    INVALID = "INVALID"
    EMPTY = "EMPTY"


@dataclass
class ChannelGapReport:
    """Quantitative diagnostics for geometric discontinuities along a river reach."""
    gap_count: int
    max_gap_distance_m: float
    total_gap_distance_m: float
    gap_locations: List[Dict[str, Any]]
    continuity_status: ChannelContinuityStatus
    is_continuous: bool
    diagnostic_notes: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gap_count": self.gap_count,
            "max_gap_distance_m": round(self.max_gap_distance_m, 2),
            "total_gap_distance_m": round(self.total_gap_distance_m, 2),
            "gap_locations": self.gap_locations,
            "continuity_status": self.continuity_status.value,
            "is_continuous": self.is_continuous,
            "diagnostic_notes": self.diagnostic_notes,
        }


@dataclass
class ChainageStation:
    """Downstream station reference along the river thalweg."""
    station_id: str
    chainage_km: float
    chainage_m: float
    latitude: float
    longitude: float
    reach_name: str
    is_landmark: bool
    landmark_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "station_id": self.station_id,
            "chainage_km": round(self.chainage_km, 3),
            "chainage_m": round(self.chainage_m, 1),
            "latitude": round(self.latitude, 6),
            "longitude": round(self.longitude, 6),
            "reach_name": self.reach_name,
            "is_landmark": self.is_landmark,
            "landmark_name": self.landmark_name,
        }


@dataclass
class RiverChainageReport:
    """River chainage stationing analysis along the Yamuna main channel."""
    status: str  # "AVAILABLE", "UNAVAILABLE", "FRAGMENTED_LIMITED"
    origin_point_name: str
    terminus_point_name: str
    total_chainage_km: float
    station_interval_km: float
    stations_count: int
    stations: List[ChainageStation]
    calculation_crs: str
    channel_continuity: ChannelContinuityStatus
    limitations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "origin_point_name": self.origin_point_name,
            "terminus_point_name": self.terminus_point_name,
            "total_chainage_km": round(self.total_chainage_km, 3),
            "station_interval_km": self.station_interval_km,
            "stations_count": self.stations_count,
            "stations": [s.to_dict() for s in self.stations],
            "calculation_crs": self.calculation_crs,
            "channel_continuity": self.channel_continuity.value,
            "limitations": self.limitations,
        }


@dataclass
class NetworkTopologySummary:
    """Network graph topological diagnostics for the hydrographic reach network."""
    total_nodes: int
    total_edges: int
    connected_components_count: int
    giant_component_nodes: int
    giant_component_ratio: float
    isolated_edges_count: int
    confluence_junctions_count: int  # Nodes with degree >= 3
    dead_end_nodes_count: int  # Nodes with degree == 1
    has_cycles_or_braids: bool
    cycles_count: int
    flow_direction_verified: bool
    scientific_notes: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_nodes": self.total_nodes,
            "total_edges": self.total_edges,
            "connected_components_count": self.connected_components_count,
            "giant_component_nodes": self.giant_component_nodes,
            "giant_component_ratio": round(self.giant_component_ratio, 3),
            "isolated_edges_count": self.isolated_edges_count,
            "confluence_junctions_count": self.confluence_junctions_count,
            "dead_end_nodes_count": self.dead_end_nodes_count,
            "has_cycles_or_braids": self.has_cycles_or_braids,
            "cycles_count": self.cycles_count,
            "flow_direction_verified": self.flow_direction_verified,
            "scientific_notes": self.scientific_notes,
        }


@dataclass
class HydrographyProcessingReport:
    """Complete summary of hydrographic ingestion, validation, and classification."""
    source_file: str
    total_raw_features: int
    valid_features_count: int
    invalid_features_count: int
    empty_features_count: int
    duplicate_features_count: int
    features_within_corridor: int
    total_network_length_km: float
    features_by_class: Dict[str, int]
    length_by_class_km: Dict[str, float]
    native_crs: str
    metric_crs: str
    bounding_box: Dict[str, float]
    validation_status: HydrographyValidationStatus
    main_channel_continuity: ChannelContinuityStatus
    main_channel_length_km: float
    topology_summary: Optional[NetworkTopologySummary]
    chainage_summary: Optional[RiverChainageReport]
    transformation_log: List[str]
    warnings: List[str]
    scientific_limitations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_file": self.source_file,
            "total_raw_features": self.total_raw_features,
            "valid_features_count": self.valid_features_count,
            "invalid_features_count": self.invalid_features_count,
            "empty_features_count": self.empty_features_count,
            "duplicate_features_count": self.duplicate_features_count,
            "features_within_corridor": self.features_within_corridor,
            "total_network_length_km": round(self.total_network_length_km, 3),
            "features_by_class": self.features_by_class,
            "length_by_class_km": {k: round(v, 3) for k, v in self.length_by_class_km.items()},
            "native_crs": self.native_crs,
            "metric_crs": self.metric_crs,
            "bounding_box": self.bounding_box,
            "validation_status": self.validation_status.value,
            "main_channel_continuity": self.main_channel_continuity.value,
            "main_channel_length_km": round(self.main_channel_length_km, 3),
            "topology_summary": self.topology_summary.to_dict() if self.topology_summary else None,
            "chainage_summary": self.chainage_summary.to_dict() if self.chainage_summary else None,
            "transformation_log": self.transformation_log,
            "warnings": self.warnings,
            "scientific_limitations": self.scientific_limitations,
        }


class HydrographyProcessor:
    """Production-grade Hydrography validation, classification, and network topology engine."""

    PROJECTED_METRIC_CRS = "EPSG:32643"  # UTM Zone 43N
    ALLOWED_EXTENSIONS = {".geojson", ".json", ".gpkg", ".shp"}

    # Authoritative corridor bounding box
    STUDY_CORRIDOR_BOUNDS = {
        "west": 76.85,
        "south": 28.50,
        "east": 77.60,
        "north": 30.40,
    }

    # Known Yamuna tributaries in study corridor
    KNOWN_TRIBUTARY_NAMES = {
        "hindon", "som", "boli", "maskara", "pathrala", "somb",
        "harnaundi", "budhi yamuna", "sahibi", "badshapur",
    }

    # Known canals diverting from Yamuna
    KNOWN_CANAL_NAMES = {
        "western yamuna canal", "eastern yamuna canal", "wyc", "eyc",
        "agra canal", "munak canal", "delhi branch", "bhalaut branch",
    }

    # Known drains in Delhi NCR reach
    KNOWN_DRAIN_NAMES = {
        "najafgarh drain", "barapullah", "shahdara drain", "supplementary drain",
        "trans-yamuna drain", "gazipur drain", "sen nursing home drain",
    }

    @classmethod
    def classify_feature(cls, properties: Dict[str, Any]) -> HydrographyClass:
        """
        Evidence-based classification of a waterway feature using source tags.
        Never infers physical class solely from line geometry.
        """
        # Lowercase all string properties for robust lookup
        props_clean = {str(k).lower(): str(v).lower().strip() for k, v in properties.items() if v is not None}

        name = props_clean.get("name") or props_clean.get("name:en") or props_clean.get("river_name") or ""
        waterway = props_clean.get("waterway") or ""
        man_made = props_clean.get("man_made") or ""
        barrier = props_clean.get("barrier") or ""
        fclass = props_clean.get("fclass") or ""

        # 1. Embankment / Flood Protection Feature
        if (
            "dyke" in man_made
            or "embankment" in man_made
            or "dyke" in barrier
            or "embankment" in barrier
            or "flood_protection" in props_clean
            or "bund" in name
            or "bundh" in name
            or "embankment" in name
        ):
            return HydrographyClass.EMBANKMENT

        # 2. Canals
        if waterway == "canal" or fclass == "canal" or any(c in name for c in cls.KNOWN_CANAL_NAMES):
            return HydrographyClass.CANAL

        # 3. Drains and Minor Waterways
        if (
            waterway in ["drain", "ditch"]
            or fclass in ["drain", "ditch"]
            or "drain" in name
            or "nala" in name
            or "nullah" in name
            or any(d in name for d in cls.KNOWN_DRAIN_NAMES)
        ):
            return HydrographyClass.DRAIN_MINOR

        # 4. Main River (Yamuna / Jumna)
        if (
            ("yamuna" in name or "jumna" in name or "jamuna" in name)
            and "canal" not in name
            and "drain" not in name
        ):
            return HydrographyClass.MAIN_RIVER

        # 5. Tributaries
        if (
            any(trib in name for trib in cls.KNOWN_TRIBUTARY_NAMES)
            or (waterway in ["river", "stream"] and name and "yamuna" not in name)
        ):
            return HydrographyClass.TRIBUTARY

        # 6. Fallback based on waterway tag
        if waterway == "river" or fclass == "river":
            return HydrographyClass.MAIN_RIVER if "yamuna" in name else HydrographyClass.TRIBUTARY
        elif waterway in ["stream", "brook"] or fclass in ["stream"]:
            return HydrographyClass.DRAIN_MINOR

        return HydrographyClass.AMBIGUOUS

    @classmethod
    def validate_and_process(
        cls,
        file_path: Path,
        clip_to_corridor: bool = True,
        snap_tolerance_m: float = 10.0,
    ) -> Tuple[gpd.GeoDataFrame, HydrographyProcessingReport]:
        """
        Loads, validates, reprojects, classifies, and audits vector hydrography.
        Returns the processed GeoDataFrame (EPSG:4326 geometry with UTM metric lengths)
        and a detailed HydrographyProcessingReport.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Hydrography dataset not found: {file_path}")

        ext = file_path.suffix.lower()
        if ext not in cls.ALLOWED_EXTENSIONS:
            raise ValueError(f"Unsupported format '{ext}'. Allowed: {sorted(list(cls.ALLOWED_EXTENSIONS))}")

        transformation_log: List[str] = [f"Ingested raw vector file '{file_path.name}'."]
        warnings: List[str] = []

        try:
            gdf = gpd.read_file(file_path)
        except Exception as exc:
            raise ValueError(f"Failed to parse vector dataset with GDAL/GeoPandas: {str(exc)}") from exc

        total_raw = len(gdf)

        if gdf.empty:
            empty_report = HydrographyProcessingReport(
                source_file=file_path.name,
                total_raw_features=0,
                valid_features_count=0,
                invalid_features_count=0,
                empty_features_count=0,
                duplicate_features_count=0,
                features_within_corridor=0,
                total_network_length_km=0.0,
                features_by_class={},
                length_by_class_km={},
                native_crs="UNDEFINED",
                metric_crs=cls.PROJECTED_METRIC_CRS,
                bounding_box={"west": 0.0, "south": 0.0, "east": 0.0, "north": 0.0},
                validation_status=HydrographyValidationStatus.EMPTY,
                main_channel_continuity=ChannelContinuityStatus.UNAVAILABLE,
                main_channel_length_km=0.0,
                topology_summary=None,
                chainage_summary=None,
                transformation_log=["Dataset is empty."],
                warnings=["Dataset contains zero features."],
                scientific_limitations=["Empty collection cannot support spatial or hydrological analysis."],
            )
            return gdf, empty_report

        # 1. CRS Check & Assignment
        if gdf.crs is None:
            warnings.append("Lacks native CRS metadata. Assuming EPSG:4326 (WGS 84 geographic).")
            gdf.set_crs("EPSG:4326", inplace=True)
            native_crs_str = "MISSING (Assumed EPSG:4326)"
        else:
            native_crs_str = f"EPSG:{gdf.crs.to_epsg()}" if gdf.crs.to_epsg() else str(gdf.crs)
        transformation_log.append(f"CRS verified: native={native_crs_str}.")

        # 2. Geometry Validity and Cleaning
        empty_mask = gdf.geometry.is_empty | gdf.geometry.isnull()
        empty_count = int(empty_mask.sum())
        if empty_count > 0:
            warnings.append(f"Removed {empty_count} empty geometries.")
            gdf = gdf[~empty_mask].copy()

        invalid_mask = ~gdf.geometry.is_valid
        invalid_count = int(invalid_mask.sum())
        if invalid_count > 0:
            warnings.append(f"Found {invalid_count} geometrically invalid features (attempting buffer(0) fix).")
            gdf["geometry"] = gdf.geometry.buffer(0)
            transformation_log.append(f"Applied topological buffer(0) to {invalid_count} invalid features.")

        # 3. Duplicate Detection (by WKT geometry match)
        geom_wkt = gdf.geometry.apply(lambda g: g.wkt if g else "")
        dup_mask = geom_wkt.duplicated()
        duplicate_count = int(dup_mask.sum())
        if duplicate_count > 0:
            warnings.append(f"Detected {duplicate_count} duplicate geometry features (retained primary instance).")
            gdf = gdf[~dup_mask].copy()
            transformation_log.append(f"Filtered out {duplicate_count} duplicate geometries.")

        # 4. Study Area Clipping
        study_corridor_box = box(
            cls.STUDY_CORRIDOR_BOUNDS["west"],
            cls.STUDY_CORRIDOR_BOUNDS["south"],
            cls.STUDY_CORRIDOR_BOUNDS["east"],
            cls.STUDY_CORRIDOR_BOUNDS["north"],
        )

        gdf_wgs84 = gdf.to_crs("EPSG:4326")
        within_corridor_count = int(gdf_wgs84.geometry.intersects(study_corridor_box).sum())

        if clip_to_corridor:
            gdf_wgs84 = gdf_wgs84[gdf_wgs84.geometry.intersects(study_corridor_box)].copy()
            gdf_wgs84["geometry"] = gdf_wgs84.geometry.intersection(study_corridor_box)
            # Remove any empty geometries resulting from intersection
            gdf_wgs84 = gdf_wgs84[~gdf_wgs84.geometry.is_empty & gdf_wgs84.geometry.notnull()].copy()
            transformation_log.append(
                f"Clipped to study corridor [{cls.STUDY_CORRIDOR_BOUNDS['west']}E, {cls.STUDY_CORRIDOR_BOUNDS['south']}N, "
                f"{cls.STUDY_CORRIDOR_BOUNDS['east']}E, {cls.STUDY_CORRIDOR_BOUNDS['north']}N]."
            )
            gdf = gdf_wgs84
        else:
            gdf = gdf_wgs84

        # 5. Reproject to UTM Zone 43N for metric calculations
        gdf_metric = gdf.to_crs(cls.PROJECTED_METRIC_CRS)
        lengths_m = gdf_metric.geometry.length.values
        gdf["length_km"] = lengths_m / 1000.0
        gdf["length_m"] = lengths_m

        # 6. Feature Classification
        classified_types = []
        for _, row in gdf.iterrows():
            props = row.to_dict()
            props.pop("geometry", None)
            w_class = cls.classify_feature(props)
            classified_types.append(w_class.value)
        gdf["hydro_class"] = classified_types

        # Compute counts and lengths by classification
        features_by_class: Dict[str, int] = {}
        length_by_class_km: Dict[str, float] = {}
        for c_type in HydrographyClass:
            c_val = c_type.value
            sub = gdf[gdf["hydro_class"] == c_val]
            features_by_class[c_val] = len(sub)
            length_by_class_km[c_val] = float(sub["length_km"].sum()) if len(sub) > 0 else 0.0

        total_length_km = float(gdf["length_km"].sum()) if len(gdf) > 0 else 0.0

        # Bounding box in EPSG:4326
        if not gdf.empty:
            total_bounds = gdf.total_bounds
            bbox_dict = {
                "west": round(float(total_bounds[0]), 4),
                "south": round(float(total_bounds[1]), 4),
                "east": round(float(total_bounds[2]), 4),
                "north": round(float(total_bounds[3]), 4),
            }
        else:
            bbox_dict = {"west": 0.0, "south": 0.0, "east": 0.0, "north": 0.0}

        # 7. Main Channel Continuity & Gap Analysis
        main_channel_gdf = gdf[gdf["hydro_class"] == HydrographyClass.MAIN_RIVER.value].copy()
        main_length_km = float(main_channel_gdf["length_km"].sum()) if len(main_channel_gdf) > 0 else 0.0

        gap_report = cls.analyze_channel_continuity(main_channel_gdf, max_acceptable_gap_m=snap_tolerance_m)
        main_continuity = gap_report.continuity_status

        # 8. Network Topology Graph Construction (NetworkX)
        topology_summary, river_graph = cls.build_network_topology(gdf, snap_tolerance_m=snap_tolerance_m)

        # 9. River Chainage / Stationing
        chainage_report = cls.compute_river_chainage(
            main_channel_gdf,
            gap_report=gap_report,
            interval_km=5.0,
        )

        validation_status = HydrographyValidationStatus.VALID
        if warnings:
            validation_status = HydrographyValidationStatus.VALID_WITH_WARNINGS

        limitations = [
            "VECTOR CENTERLINE ONLY: Centerlines and reaches do NOT reflect river bathymetry, bed depth, or flow velocity.",
            "NO FLOOD INUNDATION IMPLICATION: Hydrography lines alone cannot determine inundation perimeters.",
            "EMBANKMENT ELEVATION: Mapped bunds/embankments lack certified crest elevations and breach integrity data.",
            f"METRIC CALCULATIONS: Linear lengths derived in {cls.PROJECTED_METRIC_CRS} (UTM Zone 43N).",
        ]

        report = HydrographyProcessingReport(
            source_file=file_path.name,
            total_raw_features=total_raw,
            valid_features_count=len(gdf),
            invalid_features_count=invalid_count,
            empty_features_count=empty_count,
            duplicate_features_count=duplicate_count,
            features_within_corridor=within_corridor_count,
            total_network_length_km=total_length_km,
            features_by_class=features_by_class,
            length_by_class_km=length_by_class_km,
            native_crs=native_crs_str,
            metric_crs=cls.PROJECTED_METRIC_CRS,
            bounding_box=bbox_dict,
            validation_status=validation_status,
            main_channel_continuity=main_continuity,
            main_channel_length_km=main_length_km,
            topology_summary=topology_summary,
            chainage_summary=chainage_report,
            transformation_log=transformation_log,
            warnings=warnings,
            scientific_limitations=limitations,
        )

        return gdf, report

    @classmethod
    def analyze_channel_continuity(
        cls,
        main_channel_gdf: gpd.GeoDataFrame,
        max_acceptable_gap_m: float = 25.0,
    ) -> ChannelGapReport:
        """
        Evaluates geometric continuity of the main channel.
        Sorts reaches geographically from upstream (North) to downstream (South),
        and detects Euclidean gaps between consecutive segments in UTM 43N meters.
        """
        if main_channel_gdf.empty:
            return ChannelGapReport(
                gap_count=0,
                max_gap_distance_m=0.0,
                total_gap_distance_m=0.0,
                gap_locations=[],
                continuity_status=ChannelContinuityStatus.UNAVAILABLE,
                is_continuous=False,
                diagnostic_notes=["No main river features detected in dataset."],
            )

        # Reproject to metric UTM 43N
        main_metric = main_channel_gdf.to_crs(cls.PROJECTED_METRIC_CRS)

        # Extract lines
        lines: List[LineString] = []
        for geom in main_metric.geometry:
            if isinstance(geom, LineString):
                lines.append(geom)
            elif isinstance(geom, MultiLineString):
                lines.extend(list(geom.geoms))

        if not lines:
            return ChannelGapReport(
                gap_count=0,
                max_gap_distance_m=0.0,
                total_gap_distance_m=0.0,
                gap_locations=[],
                continuity_status=ChannelContinuityStatus.UNAVAILABLE,
                is_continuous=False,
                diagnostic_notes=["No valid LineString geometries found for main channel."],
            )

        # Sort reaches generally North-to-South by start coordinate latitude
        # In UTM 43N, Northing increases northward
        sorted_lines = sorted(
            lines,
            key=lambda ls: max(ls.coords[0][1], ls.coords[-1][1]),
            reverse=True,
        )

        gaps: List[Dict[str, Any]] = []
        total_gap_dist = 0.0
        max_gap_dist = 0.0

        for i in range(len(sorted_lines) - 1):
            curr_line = sorted_lines[i]
            next_line = sorted_lines[i + 1]

            # Minimum distance between end of current and start of next
            dist = curr_line.distance(next_line)
            if dist > max_acceptable_gap_m:
                gaps.append({
                    "segment_index": i,
                    "gap_distance_m": round(float(dist), 1),
                    "segment_a_end": (round(curr_line.coords[-1][0], 1), round(curr_line.coords[-1][1], 1)),
                    "segment_b_start": (round(next_line.coords[0][0], 1), round(next_line.coords[0][1], 1)),
                })
                total_gap_dist += dist
                if dist > max_gap_dist:
                    max_gap_dist = dist

        is_continuous = len(gaps) == 0
        if is_continuous:
            status = ChannelContinuityStatus.CONTINUOUS
            notes = [f"Channel continuity validated across {len(lines)} reaches with no gaps > {max_acceptable_gap_m}m."]
        elif len(gaps) <= 3 and max_gap_dist < 500.0:
            status = ChannelContinuityStatus.FRAGMENTED
            notes = [
                f"Channel exhibits {len(gaps)} localized gaps (max gap: {round(max_gap_dist, 1)}m). "
                "May indicate unmapped bridge cross-sections or island braids."
            ]
        else:
            status = ChannelContinuityStatus.DISCONNECTED
            notes = [
                f"Severe channel discontinuity detected: {len(gaps)} gaps (max gap: {round(max_gap_dist / 1000.0, 2)}km). "
                "Network is disconnected; cumulative chainage cannot be reliably established."
            ]

        return ChannelGapReport(
            gap_count=len(gaps),
            max_gap_distance_m=max_gap_dist,
            total_gap_distance_m=total_gap_dist,
            gap_locations=gaps,
            continuity_status=status,
            is_continuous=is_continuous,
            diagnostic_notes=notes,
        )

    @classmethod
    def build_network_topology(
        cls,
        gdf: gpd.GeoDataFrame,
        snap_tolerance_m: float = 10.0,
    ) -> Tuple[NetworkTopologySummary, nx.Graph]:
        """
        Builds a NetworkX graph representation of the river network.
        Nodes represent reach endpoints and confluence junctions.
        Edges represent reach segments with attributes (length, class, feature_id).
        """
        graph = nx.Graph()

        if gdf.empty:
            summary = NetworkTopologySummary(
                total_nodes=0,
                total_edges=0,
                connected_components_count=0,
                giant_component_nodes=0,
                giant_component_ratio=0.0,
                isolated_edges_count=0,
                confluence_junctions_count=0,
                dead_end_nodes_count=0,
                has_cycles_or_braids=False,
                cycles_count=0,
                flow_direction_verified=False,
                scientific_notes=["Empty hydrography dataset produces an empty topological graph."],
            )
            return summary, graph

        gdf_metric = gdf.to_crs(cls.PROJECTED_METRIC_CRS)

        # Coordinate rounding to snap endpoints within tolerance
        round_factor = max(1.0, snap_tolerance_m)

        def node_key(coord: Tuple[float, float]) -> Tuple[float, float]:
            return (round(coord[0] / round_factor) * round_factor, round(coord[1] / round_factor) * round_factor)

        for idx, row in gdf_metric.iterrows():
            geom = row.geometry
            if not geom or geom.is_empty:
                continue

            lines: List[LineString] = []
            if isinstance(geom, LineString):
                lines = [geom]
            elif isinstance(geom, MultiLineString):
                lines = list(geom.geoms)

            for line in lines:
                if len(line.coords) < 2:
                    continue

                u = node_key(line.coords[0])
                v = node_key(line.coords[-1])

                length_m = float(line.length)
                w_class = str(row.get("hydro_class", "unknown"))
                feat_id = str(row.get("osm_id") or row.get("id") or f"EDGE_{idx}")
                name = str(row.get("name") or "Unnamed Reach")

                # Add edge to graph
                graph.add_edge(
                    u,
                    v,
                    feature_id=feat_id,
                    name=name,
                    waterway_class=w_class,
                    length_m=round(length_m, 1),
                    length_km=round(length_m / 1000.0, 3),
                    flow_direction_verified=False,  # Flow direction cannot be assumed from line digitization
                    provenance="PRAVAAH Hydrography Topology Engine",
                )

        total_nodes = graph.number_of_nodes()
        total_edges = graph.number_of_edges()

        if total_nodes == 0:
            summary = NetworkTopologySummary(
                total_nodes=0,
                total_edges=0,
                connected_components_count=0,
                giant_component_nodes=0,
                giant_component_ratio=0.0,
                isolated_edges_count=0,
                confluence_junctions_count=0,
                dead_end_nodes_count=0,
                has_cycles_or_braids=False,
                cycles_count=0,
                flow_direction_verified=False,
                scientific_notes=["No connected nodes could be extracted."],
            )
            return summary, graph

        components = list(nx.connected_components(graph))
        comp_count = len(components)
        giant_size = len(max(components, key=len)) if components else 0
        giant_ratio = float(giant_size / total_nodes) if total_nodes > 0 else 0.0

        degrees = dict(graph.degree())
        confluences = sum(1 for d in degrees.values() if d >= 3)
        dead_ends = sum(1 for d in degrees.values() if d == 1)

        # Cycles / island braids
        try:
            cycles = nx.cycle_basis(graph)
            cycle_count = len(cycles)
            has_cycles = cycle_count > 0
        except Exception:
            cycle_count = 0
            has_cycles = False

        # Isolated edges (components with exactly 2 nodes and 1 edge)
        isolated_edges = sum(1 for comp in components if len(comp) == 2)

        notes = [
            f"Network comprises {total_nodes} topological nodes and {total_edges} hydraulic reach edges.",
            f"Connected components: {comp_count}. Giant connected component encloses {giant_size} nodes ({round(giant_ratio * 100, 1)}%).",
            f"Confluence junctions (degree >= 3): {confluences}. Dead-end terminals (degree = 1): {dead_ends}.",
        ]
        if has_cycles:
            notes.append(f"Detected {cycle_count} closed loops/braids (characteristic of alluvial anabranching channels).")
        notes.append("FLOW DIRECTION GUARD: Network edges are undirected; flow orientation is not inferred without hydrodynamic validation.")

        summary = NetworkTopologySummary(
            total_nodes=total_nodes,
            total_edges=total_edges,
            connected_components_count=comp_count,
            giant_component_nodes=giant_size,
            giant_component_ratio=giant_ratio,
            isolated_edges_count=isolated_edges,
            confluence_junctions_count=confluences,
            dead_end_nodes_count=dead_ends,
            has_cycles_or_braids=has_cycles,
            cycles_count=cycle_count,
            flow_direction_verified=False,
            scientific_notes=notes,
        )

        return summary, graph

    @classmethod
    def compute_river_chainage(
        cls,
        main_channel_gdf: gpd.GeoDataFrame,
        gap_report: Optional[ChannelGapReport] = None,
        interval_km: float = 5.0,
    ) -> RiverChainageReport:
        """
        Computes downstream river chainage in kilometers along the Yamuna main channel
        from Hathnikund Barrage (~30.31°N) towards Delhi Old Railway Bridge (~28.66°N).
        If the channel is disconnected, explicitly returns an UNAVAILABLE or FRAGMENTED report.
        """
        if main_channel_gdf.empty:
            return RiverChainageReport(
                status="UNAVAILABLE",
                origin_point_name="Hathnikund Barrage (Yamunanagar)",
                terminus_point_name="Delhi Old Railway Bridge (Delhi)",
                total_chainage_km=0.0,
                station_interval_km=interval_km,
                stations_count=0,
                stations=[],
                calculation_crs=cls.PROJECTED_METRIC_CRS,
                channel_continuity=ChannelContinuityStatus.UNAVAILABLE,
                limitations=["No main river channel features present to compute chainage."],
            )

        # Check gap report
        if gap_report and gap_report.continuity_status == ChannelContinuityStatus.DISCONNECTED:
            return RiverChainageReport(
                status="DISCONNECTED_REFUSED",
                origin_point_name="Hathnikund Barrage (Yamunanagar)",
                terminus_point_name="Delhi Old Railway Bridge (Delhi)",
                total_chainage_km=0.0,
                station_interval_km=interval_km,
                stations_count=0,
                stations=[],
                calculation_crs=cls.PROJECTED_METRIC_CRS,
                channel_continuity=ChannelContinuityStatus.DISCONNECTED,
                limitations=[
                    "CHAINAGE COMPUTATION REFUSED: Main channel exhibits critical topological discontinuities.",
                    f"Found {gap_report.gap_count} gaps with max gap {round(gap_report.max_gap_distance_m, 1)}m.",
                    "PRAVAAH strictly refuses to substitute straight-line distance for missing river thalweg geometry.",
                ],
            )

        # Reproject to UTM Zone 43N
        main_metric = main_channel_gdf.to_crs(cls.PROJECTED_METRIC_CRS)

        lines: List[LineString] = []
        for geom in main_metric.geometry:
            if isinstance(geom, LineString):
                lines.append(geom)
            elif isinstance(geom, MultiLineString):
                lines.extend(list(geom.geoms))

        if not lines:
            return RiverChainageReport(
                status="UNAVAILABLE",
                origin_point_name="Hathnikund Barrage (Yamunanagar)",
                terminus_point_name="Delhi Old Railway Bridge (Delhi)",
                total_chainage_km=0.0,
                station_interval_km=interval_km,
                stations_count=0,
                stations=[],
                calculation_crs=cls.PROJECTED_METRIC_CRS,
                channel_continuity=ChannelContinuityStatus.UNAVAILABLE,
                limitations=["No valid LineString geometries."],
            )

        # Try to merge lines into continuous thalweg
        merged = linemerge(lines)
        if isinstance(merged, MultiLineString):
            # Take the longest continuous LineString or concatenate sorted segments
            longest_line = max(merged.geoms, key=lambda g: g.length)
            thalweg = longest_line
            continuity = ChannelContinuityStatus.FRAGMENTED
        elif isinstance(merged, LineString):
            thalweg = merged
            continuity = ChannelContinuityStatus.CONTINUOUS
        else:
            thalweg = lines[0]
            continuity = ChannelContinuityStatus.FRAGMENTED

        # Ensure thalweg is oriented downstream (North to South, i.e., start has higher Y than end in UTM 43N)
        if thalweg.coords[0][1] < thalweg.coords[-1][1]:
            # Reverse coordinates so index 0 is upstream (North)
            thalweg = LineString(list(reversed(thalweg.coords)))

        total_length_m = thalweg.length
        total_chainage_km = total_length_m / 1000.0

        # Reprojector from UTM 43N to WGS 84 for geographic station coordinates
        to_wgs84 = CRS(cls.PROJECTED_METRIC_CRS)
        wgs84 = CRS("EPSG:4326")
        from pyproj import Transformer
        transformer = Transformer.from_crs(to_wgs84, wgs84, always_xy=True)

        # Generate stations every `interval_km`
        interval_m = interval_km * 1000.0
        num_stations = max(1, int(math.floor(total_length_m / interval_m)))

        stations: List[ChainageStation] = []

        # Origin station (KM 0.0)
        start_pt = Point(thalweg.coords[0])
        lon, lat = transformer.transform(start_pt.x, start_pt.y)
        stations.append(ChainageStation(
            station_id="STN_CH_000K",
            chainage_km=0.0,
            chainage_m=0.0,
            latitude=lat,
            longitude=lon,
            reach_name="Hathnikund Barrage (Yamunanagar)",
            is_landmark=True,
            landmark_name="Hathnikund Barrage (Upstream Origin)",
        ))

        # Intermediate regular stations
        for i in range(1, num_stations + 1):
            dist_m = i * interval_m
            if dist_m >= total_length_m:
                break
            pt = thalweg.interpolate(dist_m)
            lon, lat = transformer.transform(pt.x, pt.y)
            dist_km = dist_m / 1000.0

            # Landmark annotation
            is_landmark = False
            landmark_name = None
            if 40.0 <= dist_km <= 55.0:
                is_landmark = True
                landmark_name = "Kalanaur / Yamunanagar Reach"
            elif 95.0 <= dist_km <= 110.0:
                is_landmark = True
                landmark_name = "Mawi / Panipat Reach"
            elif 170.0 <= dist_km <= 185.0:
                is_landmark = True
                landmark_name = "Wazirabad Barrage Entry"
            elif 195.0 <= dist_km <= 210.0:
                is_landmark = True
                landmark_name = "Delhi Old Railway Bridge (ORB Gauge)"

            stations.append(ChainageStation(
                station_id=f"STN_CH_{int(dist_km):03d}K",
                chainage_km=dist_km,
                chainage_m=dist_m,
                latitude=lat,
                longitude=lon,
                reach_name=f"Yamuna Reach km {dist_km:.1f}",
                is_landmark=is_landmark,
                landmark_name=landmark_name,
            ))

        # Terminus station
        end_pt = Point(thalweg.coords[-1])
        end_lon, end_lat = transformer.transform(end_pt.x, end_pt.y)
        stations.append(ChainageStation(
            station_id=f"STN_CH_{int(total_chainage_km):03d}K_END",
            chainage_km=total_chainage_km,
            chainage_m=total_length_m,
            latitude=end_lat,
            longitude=end_lon,
            reach_name="Delhi Terminal Reach (Okhla / Downstream)",
            is_landmark=True,
            landmark_name="Yamuna Corridor Terminus",
        ))

        limitations = [
            f"Derived along merged river thalweg centerline in {cls.PROJECTED_METRIC_CRS}.",
            "Does NOT incorporate meander migration or seasonal braiding changes post-monsoon.",
            "Station coordinates represent geometric centerline points; not physical benchmark pillars.",
        ]

        return RiverChainageReport(
            status="AVAILABLE",
            origin_point_name="Hathnikund Barrage (Yamunanagar)",
            terminus_point_name="Delhi Reach Terminus",
            total_chainage_km=total_chainage_km,
            station_interval_km=interval_km,
            stations_count=len(stations),
            stations=stations,
            calculation_crs=cls.PROJECTED_METRIC_CRS,
            channel_continuity=continuity,
            limitations=limitations,
        )

    @classmethod
    def create_synthetic_hydrography_fixture(
        cls,
        output_path: Path,
        include_gaps: bool = False,
    ) -> Path:
        """
        Creates an explicitly isolated synthetic vector GeoJSON fixture strictly for automated testing.
        Contains main river, canal, tributary, drain, and embankment features in EPSG:4326.
        """
        if not include_gaps:
            # Continuous main Yamuna channel from Hathnikund (~30.3°N) to Delhi (~28.53°N)
            yamuna_seg1 = LineString([(77.58, 30.31), (77.40, 29.95), (77.15, 29.68)])
            yamuna_seg2 = LineString([(77.15, 29.68), (77.08, 29.39), (77.12, 28.98)])
            yamuna_seg3 = LineString([(77.12, 28.98), (77.25, 28.66), (77.30, 28.53)])
        else:
            # Segment with a 5 km gap between seg1 and seg2
            yamuna_seg1 = LineString([(77.58, 30.31), (77.40, 29.95)])
            yamuna_seg2 = LineString([(77.20, 29.50), (77.08, 29.39)])
            yamuna_seg3 = LineString([(77.12, 28.98), (77.25, 28.66)])

        # Western Yamuna Canal diversion
        wyc_canal = LineString([(77.57, 30.31), (77.28, 29.96), (76.98, 29.69), (76.97, 28.99)])

        # Hindon River tributary
        hindon_trib = LineString([(77.55, 30.15), (77.45, 29.80), (77.35, 29.00), (77.40, 28.55)])

        # Najafgarh Drain
        najafgarh_drain = LineString([(77.01, 28.60), (77.12, 28.67), (77.23, 28.68)])

        # Yamuna Right Marginal Bund (Embankment)
        marginal_bund = LineString([(77.22, 28.72), (77.24, 28.66), (77.27, 28.58)])

        features = [
            {
                "type": "Feature",
                "id": "SYNTH_YAMUNA_01",
                "geometry": mapping(yamuna_seg1),
                "properties": {
                    "osm_id": "1001",
                    "name": "Yamuna River",
                    "waterway": "river",
                },
            },
            {
                "type": "Feature",
                "id": "SYNTH_YAMUNA_02",
                "geometry": mapping(yamuna_seg2),
                "properties": {
                    "osm_id": "1002",
                    "name": "Yamuna",
                    "waterway": "river",
                },
            },
            {
                "type": "Feature",
                "id": "SYNTH_YAMUNA_03",
                "geometry": mapping(yamuna_seg3),
                "properties": {
                    "osm_id": "1003",
                    "name": "River Yamuna",
                    "waterway": "river",
                },
            },
            {
                "type": "Feature",
                "id": "SYNTH_WYC_04",
                "geometry": mapping(wyc_canal),
                "properties": {
                    "osm_id": "2001",
                    "name": "Western Yamuna Canal",
                    "waterway": "canal",
                },
            },
            {
                "type": "Feature",
                "id": "SYNTH_HINDON_05",
                "geometry": mapping(hindon_trib),
                "properties": {
                    "osm_id": "3001",
                    "name": "Hindon River",
                    "waterway": "river",
                },
            },
            {
                "type": "Feature",
                "id": "SYNTH_NAJAFGARH_06",
                "geometry": mapping(najafgarh_drain),
                "properties": {
                    "osm_id": "4001",
                    "name": "Najafgarh Drain",
                    "waterway": "drain",
                },
            },
            {
                "type": "Feature",
                "id": "SYNTH_BUND_07",
                "geometry": mapping(marginal_bund),
                "properties": {
                    "osm_id": "5001",
                    "name": "Yamuna Right Marginal Bund",
                    "man_made": "dyke",
                    "barrier": "embankment",
                },
            },
        ]

        geojson_doc = {
            "type": "FeatureCollection",
            "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::4326"}},
            "features": features,
            "properties": {
                "dataset_name": "PRAVAAH Synthetic Hydrography Unit Test Fixture",
                "is_synthetic_fixture": True,
                "disclaimer": "SYNTHETIC TEST FIXTURE: NOT REAL GEOGRAPHY. FOR AUTOMATED TESTS ONLY.",
            },
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(geojson_doc, f, indent=2)

        return output_path

    @classmethod
    def scan_hydrography_status(cls, data_dir: Optional[Path] = None) -> Dict[str, Any]:
        """
        Scans data/raw/spatial/hydrography/ and data/processed/spatial/hydrography/
        for physical vector river datasets. Reports availability, provenance, and validation.
        """
        repo_root = Path(__file__).resolve().parents[2]
        base_dir = data_dir or (repo_root / "data")
        raw_dir = base_dir / "raw" / "spatial" / "hydrography"
        proc_dir = base_dir / "processed" / "spatial" / "hydrography"

        raw_dir.mkdir(parents=True, exist_ok=True)
        proc_dir.mkdir(parents=True, exist_ok=True)

        candidate_files = []
        for d in [proc_dir, raw_dir]:
            for ext in cls.ALLOWED_EXTENSIONS:
                candidate_files.extend(list(d.glob(f"*{ext}")))
        candidate_files = sorted(list(set(candidate_files)))

        if not candidate_files:
            return {
                "hydrography_availability": "UNAVAILABLE",
                "scanned_directories": [str(raw_dir), str(proc_dir)],
                "total_files_found": 0,
                "active_hydrography_file": None,
                "processing_report": None,
                "acquisition_guide": {
                    "required_coverage": "Yamuna River corridor (West: 76.85°E, South: 28.50°N, East: 77.60°E, North: 30.40°N)",
                    "recommended_sources": [
                        "OpenStreetMap (OSM) Northern India waterway extracts (Geofabrik or Overpass)",
                        "Central Water Commission (CWC) National River Reach Network GIS data",
                        "Survey of India (SOI) Open Series Topographical Hydrography",
                    ],
                    "target_placement_directory": "data/raw/spatial/hydrography/osm_yamuna_waterways.geojson",
                    "accepted_formats": sorted(list(cls.ALLOWED_EXTENSIONS)),
                },
                "scientific_notice": (
                    "RIVER HYDROGRAPHY DATA UNAVAILABLE IN REPOSITORY — PRAVAAH strictly refuses to substitute "
                    "mock vector polylines for unacquired public waterways in operational reporting."
                ),
            }

        primary_file = candidate_files[0]
        _, report = cls.validate_and_process(primary_file, clip_to_corridor=True)

        return {
            "hydrography_availability": "AVAILABLE",
            "scanned_directories": [str(raw_dir), str(proc_dir)],
            "total_files_found": len(candidate_files),
            "all_files": [f.name for f in candidate_files],
            "active_hydrography_file": primary_file.name,
            "processing_report": report.to_dict(),
            "scientific_notice": (
                "Hydrography dataset active. Features reflect centerline geometry and network topology. "
                "Does NOT represent river bathymetry, water depth, flow velocity, or flood inundation extent."
            ),
        }
