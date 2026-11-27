"""
backend/app/services/spatial.py

Backend Business Logic Service for PRAVAAH Spatial Data Infrastructure.
Provides typed access to spatial dataset inventories, study-area bounds,
DEM integrity validation, and terrain slope analysis.

SECURITY & INTEGRITY SAFEGUARDS:
- Strictly prevents path traversal attacks: resolves files exclusively within data/raw/spatial/dem/.
- Never fabricates synthetic DEM rasters for operational requests.
- When DEM is unavailable, returns structured, typed unavailable responses with actionable guidelines.
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

# Ensure repository root is in sys.path
_repo_root = Path(__file__).resolve().parents[3]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from ml.spatial.study_area import StudyAreaCatalog
from ml.spatial.inventory import SpatialInventoryCatalog
from app.schemas.spatial import (
    SpatialDatasetSchema,
    SpatialInventoryResponse,
    StudyAreaBoundsSchema,
    StudyAreaMetadataResponse,
    DEMValidationReportSchema,
    DEMStatusResponse,
    TerrainSlopeSummarySchema,
    TerrainSummaryResponse,
    RiverNetworkReportSchema,
    RiverNetworkStatusResponse,
    RiverGeoJSONResponse,
    ChannelGapReportSchema,
    ChainageStationSchema,
    RiverChainageResponse,
    NetworkTopologySummarySchema,
    RiverNetworkGraphResponse,
    HydrographyProcessingReportSchema,
    HydrographyStatusResponse,
    HydrographyLayersResponse,
    HydrographySummaryResponse,
)


class SpatialService:
    """Service providing spatial data cataloging, boundary validation, DEM inspection, and river network analysis."""

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or (_repo_root / "data")
        self.dem_dir = self.data_dir / "raw" / "spatial" / "dem"
        self.dem_dir.mkdir(parents=True, exist_ok=True)
        self.hydro_dir = self.data_dir / "raw" / "spatial" / "hydrography"
        self.hydro_dir.mkdir(parents=True, exist_ok=True)
        self.proc_hydro_dir = self.data_dir / "processed" / "spatial" / "hydrography"
        self.proc_hydro_dir.mkdir(parents=True, exist_ok=True)


    def get_inventory(self) -> SpatialInventoryResponse:
        """Returns the authoritative spatial dataset inventory."""
        catalog_entries = SpatialInventoryCatalog.get_catalog()
        schemas = [SpatialDatasetSchema(**entry.to_dict()) for entry in catalog_entries]
        return SpatialInventoryResponse(
            total_datasets=len(schemas),
            datasets=schemas,
        )

    def get_study_area(self) -> StudyAreaMetadataResponse:
        """Returns the verified rectangular study extent metadata contract."""
        meta = StudyAreaCatalog.get_authoritative_study_area()
        meta_dict = meta.to_dict()

        bounds_schema = StudyAreaBoundsSchema(
            west_lon=meta_dict["bounds"]["west_lon"],
            south_lat=meta_dict["bounds"]["south_lat"],
            east_lon=meta_dict["bounds"]["east_lon"],
            north_lat=meta_dict["bounds"]["north_lat"],
            bbox_standard_order=meta_dict["bounds"]["bbox_standard_order"],
        )

        return StudyAreaMetadataResponse(
            name=meta_dict["name"],
            description=meta_dict["description"],
            geometry_type=meta_dict["geometry_type"],
            geographic_crs=meta_dict["geographic_crs"],
            projected_crs=meta_dict["projected_crs"],
            projected_crs_justification=meta_dict["projected_crs_justification"],
            bounds=bounds_schema,
            geojson=meta_dict["geojson"],
            reach_length_km=meta_dict["reach_length_km"],
            spatial_coverage=meta_dict["spatial_coverage"],
            validation_status=meta_dict["validation_status"],
            provenance=meta_dict["provenance"],
            scientific_limitations=meta_dict["scientific_limitations"],
        )

    def get_dem_status(self) -> DEMStatusResponse:
        """Scans the repository DEM directory and returns availability and validation status."""
        status_dict = SpatialInventoryCatalog.scan_repository_dem_status(self.data_dir)

        val_report = None
        if status_dict.get("validation_report"):
            val_report = DEMValidationReportSchema(**status_dict["validation_report"])

        return DEMStatusResponse(
            dem_availability=status_dict["dem_availability"],
            scanned_directory=status_dict["scanned_directory"],
            total_files_found=status_dict["total_files_found"],
            all_files=status_dict.get("all_files", []),
            active_dem_file=status_dict.get("active_dem_file"),
            validation_report=val_report,
            acquisition_guide=status_dict.get("acquisition_guide"),
            scientific_notice=status_dict["scientific_notice"],
        )

    def inspect_dem_file(self, relative_file_name: str) -> DEMValidationReportSchema:
        """
        Safely validates a specific DEM GeoTIFF located in data/raw/spatial/dem/.
        Guards against directory traversal by strictly enforcing path confinement.
        """
        # Security sanitization
        clean_name = Path(relative_file_name).name
        if clean_name != relative_file_name.strip():
            raise ValueError("Directory traversal attempt blocked: supply a simple filename without path separators.")

        suffix = Path(clean_name).suffix.lower()
        if suffix not in [".tif", ".tiff"]:
            raise ValueError(f"Invalid file extension '{suffix}': DEM must be a GeoTIFF (.tif or .tiff).")

        target_file = (self.dem_dir / clean_name).resolve()

        # Enforce that resolved path is strictly within dem_dir
        if not str(target_file).startswith(str(self.dem_dir.resolve())):
            raise ValueError("Security violation: path resolves outside the configured DEM directory.")

        if not target_file.exists():
            raise FileNotFoundError(f"Requested DEM file '{clean_name}' does not exist in {self.dem_dir}.")

        from ml.spatial.dem import DEMValidator
        report = DEMValidator.validate_file(target_file)
        return DEMValidationReportSchema(**report.to_dict())

    def get_terrain_summary(self) -> TerrainSummaryResponse:
        """
        Computes elevation and slope analysis if a physical DEM is present in the repository.
        If unavailable, returns a structured UNAVAILABLE response with explicit caveats.
        """
        status_dict = SpatialInventoryCatalog.scan_repository_dem_status(self.data_dir)

        if status_dict["dem_availability"] != "AVAILABLE" or not status_dict.get("active_dem_file"):
            return TerrainSummaryResponse(
                status="UNAVAILABLE",
                source_dem_file=None,
                elevation_summary=None,
                slope_summary=None,
                valid_coverage_summary=None,
                scientific_disclaimer=(
                    "TERRAIN SUMMARY UNAVAILABLE — No validated DEM raster exists in data/raw/spatial/dem/. "
                    "PRAVAAH strictly refuses to fabricate synthetic terrain metrics for operational reporting."
                ),
                scientific_caveats=[
                    "Acquisition of high-resolution digital elevation data (SRTM 30m / Copernicus GLO-30) is required.",
                    "Slope analysis requires valid horizontal and vertical metric coordinates to prevent unit distortion.",
                    "Terrain slope alone does not determine flood inundation extent.",
                ],
            )

        active_file = self.dem_dir / status_dict["active_dem_file"]
        from ml.spatial.dem import DEMValidator
        dem_report = DEMValidator.validate_file(active_file)
        slope_summary = DEMValidator.compute_slope(active_file)

        elev_dict = {
            "min_elevation_m": dem_report.min_elevation_m,
            "max_elevation_m": dem_report.max_elevation_m,
            "mean_elevation_m": dem_report.mean_elevation_m,
            "std_elevation_m": dem_report.std_elevation_m,
            "p10_elevation_m": dem_report.p10_elevation_m,
            "p50_elevation_m": dem_report.p50_elevation_m,
            "p90_elevation_m": dem_report.p90_elevation_m,
            "vertical_units": "meters",
        }

        cov_dict = {
            "total_cells": dem_report.total_cells,
            "valid_cells": dem_report.valid_cells,
            "missing_cells": dem_report.missing_cells,
            "missing_cells_percentage": dem_report.missing_cells_percentage,
            "has_non_finite_values": dem_report.has_non_finite_values,
        }

        return TerrainSummaryResponse(
            status="AVAILABLE",
            source_dem_file=status_dict["active_dem_file"],
            elevation_summary=elev_dict,
            slope_summary=TerrainSlopeSummarySchema(**slope_summary.to_dict()),
            valid_coverage_summary=cov_dict,
            scientific_disclaimer=(
                "TERRAIN ELEVATION & SLOPE SUMMARY — Derived from active DEM raster. "
                "Represents static surface topography; does NOT predict flood hazard or evacuation safety."
            ),
            scientific_caveats=dem_report.scientific_caveats,
        )

    def get_river_status(self) -> RiverNetworkStatusResponse:
        """Scans the repository hydrography directory and returns availability and validation status."""
        from ml.spatial.river import RiverNetworkValidator
        status_dict = RiverNetworkValidator.scan_repository_river_status(self.data_dir)

        val_report = None
        if status_dict.get("validation_report"):
            val_report = RiverNetworkReportSchema(**status_dict["validation_report"])

        return RiverNetworkStatusResponse(
            river_data_availability=status_dict["river_data_availability"],
            scanned_directory=status_dict["scanned_directory"],
            total_files_found=status_dict["total_files_found"],
            all_files=status_dict.get("all_files", []),
            active_river_file=status_dict.get("active_river_file"),
            validation_report=val_report,
            acquisition_guide=status_dict.get("acquisition_guide"),
            scientific_notice=status_dict["scientific_notice"],
        )

    def get_river_features(self, clip_to_corridor: bool = True) -> RiverGeoJSONResponse:
        """
        Returns validated river network features as standard GeoJSON FeatureCollection.
        If no river dataset is present, returns an empty FeatureCollection with explicit status disclaimer.
        """
        from ml.spatial.river import RiverNetworkValidator
        status_dict = RiverNetworkValidator.scan_repository_river_status(self.data_dir)
        if status_dict["river_data_availability"] != "AVAILABLE" or not status_dict.get("active_river_file"):
            return RiverGeoJSONResponse(
                type="FeatureCollection",
                features=[],
                properties={
                    "status": "UNAVAILABLE",
                    "total_features": 0,
                    "disclaimer": (
                        "River network data currently unavailable in data/raw/spatial/hydrography/. "
                        "PRAVAAH strictly refuses to fabricate synthetic river lines for operational use."
                    ),
                },
            )

        active_file = self.hydro_dir / status_dict["active_river_file"]
        geojson_data = RiverNetworkValidator.load_features_geojson(active_file, clip_to_study_corridor=clip_to_corridor)
        return RiverGeoJSONResponse(**geojson_data)

    def inspect_river_file(self, relative_file_name: str, clip_to_corridor: bool = False) -> RiverNetworkReportSchema:
        """
        Safely validates a specific vector hydrography file in data/raw/spatial/hydrography/.
        Strictly confines paths within the sandboxed directory to block traversal.
        """
        from ml.spatial.river import RiverNetworkValidator
        clean_name = Path(relative_file_name).name
        if clean_name != relative_file_name.strip():
            raise ValueError("Directory traversal attempt blocked: supply a simple filename without path separators.")

        suffix = Path(clean_name).suffix.lower()
        if suffix not in RiverNetworkValidator.ALLOWED_EXTENSIONS:
            raise ValueError(
                f"Invalid file extension '{suffix}'. Supported formats: {sorted(list(RiverNetworkValidator.ALLOWED_EXTENSIONS))}"
            )

        target_file = (self.hydro_dir / clean_name).resolve()

        if not str(target_file).startswith(str(self.hydro_dir.resolve())):
            raise ValueError("Security violation: path resolves outside the configured hydrography directory.")

        if not target_file.exists():
            raise FileNotFoundError(f"Requested river dataset '{clean_name}' does not exist in {self.hydro_dir}.")

        report = RiverNetworkValidator.validate_file(target_file, clip_to_study_corridor=clip_to_corridor)
        return RiverNetworkReportSchema(**report.to_dict())

    # --- Phase 3B: Advanced Hydrography Endpoints Logic ---

    def _get_active_hydrography_file(self) -> Optional[Path]:
        """Resolves primary candidate file from processed or raw hydrography directories."""
        allowed_extensions = {".geojson", ".shp", ".gpkg"}
        for d in [self.proc_hydro_dir, self.hydro_dir]:
            for ext in allowed_extensions:
                files = sorted(list(d.glob(f"*{ext}")))
                if files:
                    return files[0]
        return None

    def get_hydrography_status(self) -> HydrographyStatusResponse:
        """Scans directories and returns complete Phase 3B hydrography status."""
        from ml.spatial.hydrography import HydrographyProcessor
        status_dict = HydrographyProcessor.scan_hydrography_status(self.data_dir)
        report_schema = None
        if status_dict.get("processing_report"):
            report_schema = HydrographyProcessingReportSchema(**status_dict["processing_report"])

        return HydrographyStatusResponse(
            hydrography_availability=status_dict["hydrography_availability"],
            scanned_directories=status_dict["scanned_directories"],
            total_files_found=status_dict["total_files_found"],
            all_files=status_dict.get("all_files", []),
            active_hydrography_file=status_dict.get("active_hydrography_file"),
            processing_report=report_schema,
            acquisition_guide=status_dict.get("acquisition_guide"),
            scientific_notice=status_dict["scientific_notice"],
        )

    def get_hydrography_layers(self, clip_to_corridor: bool = True) -> HydrographyLayersResponse:
        """Returns hydrography features partitioned into discrete semantic GIS layers."""
        active_file = self._get_active_hydrography_file()
        if not active_file:
            return HydrographyLayersResponse(
                status="UNAVAILABLE",
                active_file=None,
                layers={},
                features_by_class={},
                length_by_class_km={},
                metric_crs="EPSG:32643",
                scientific_disclaimer=(
                    "HYDROGRAPHY LAYERS UNAVAILABLE — No vector river network files detected in data/raw/spatial/hydrography/ "
                    "or data/processed/spatial/hydrography/. PRAVAAH strictly refuses to substitute synthetic geometries."
                ),
            )

        from ml.spatial.hydrography import HydrographyProcessor, HydrographyClass
        gdf, report = HydrographyProcessor.validate_and_process(active_file, clip_to_corridor=clip_to_corridor)

        from shapely.geometry import mapping
        layers: Dict[str, RiverGeoJSONResponse] = {}

        for h_class in HydrographyClass:
            sub_gdf = gdf[gdf["hydro_class"] == h_class.value]
            features = []
            for idx, (_, row) in enumerate(sub_gdf.iterrows()):
                geom = row.geometry
                if not geom or geom.is_empty:
                    continue
                feat_id = str(row.get("osm_id") or row.get("id") or f"{h_class.value.upper()}_{idx}")
                props = {
                    "feature_id": feat_id,
                    "name": str(row.get("name") or "Unnamed Feature"),
                    "hydro_class": h_class.value,
                    "length_km": round(float(row.get("length_km", 0.0)), 3),
                    "source_dataset": active_file.name,
                }
                features.append({
                    "type": "Feature",
                    "id": feat_id,
                    "geometry": mapping(geom),
                    "properties": props,
                })

            layers[h_class.value] = RiverGeoJSONResponse(
                type="FeatureCollection",
                features=features,
                crs={"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
                properties={
                    "layer_class": h_class.value,
                    "features_count": len(features),
                    "total_length_km": round(report.length_by_class_km.get(h_class.value, 0.0), 3),
                },
            )

        return HydrographyLayersResponse(
            status="AVAILABLE",
            active_file=active_file.name,
            layers=layers,
            features_by_class=report.features_by_class,
            length_by_class_km=report.length_by_class_km,
            metric_crs="EPSG:32643",
            scientific_disclaimer=(
                "HYDROGRAPHIC LAYERS ACTIVE — Categorized via verified source attributes. "
                "Centerline and thalweg features do NOT imply flood stage, water depth, or cross-section bathymetry."
            ),
        )

    def get_hydrography_summary(self) -> HydrographySummaryResponse:
        """Returns high-level synthesis of network topology, channel length, and continuity."""
        active_file = self._get_active_hydrography_file()
        if not active_file:
            return HydrographySummaryResponse(
                status="UNAVAILABLE",
                active_file=None,
                total_features=0,
                total_network_length_km=0.0,
                features_by_class={},
                length_by_class_km={},
                main_channel_continuity="UNAVAILABLE",
                main_channel_length_km=0.0,
                topology=None,
                chainage=None,
                scientific_disclaimer=(
                    "HYDROGRAPHY SUMMARY UNAVAILABLE — No verified river vectors present in repository. "
                    "PRAVAAH strictly refuses to fabricate mock waterways."
                ),
                scientific_limitations=[
                    "Acquisition of OpenStreetMap Northern India waterway extract or CWC river reach GIS data required.",
                    "Topological metrics cannot be derived without authoritative vector data.",
                ],
            )

        from ml.spatial.hydrography import HydrographyProcessor
        _, report = HydrographyProcessor.validate_and_process(active_file, clip_to_corridor=True)

        return HydrographySummaryResponse(
            status="AVAILABLE",
            active_file=active_file.name,
            total_features=report.valid_features_count,
            total_network_length_km=report.total_network_length_km,
            features_by_class=report.features_by_class,
            length_by_class_km=report.length_by_class_km,
            main_channel_continuity=report.main_channel_continuity.value,
            main_channel_length_km=report.main_channel_length_km,
            topology=NetworkTopologySummarySchema(**report.topology_summary.to_dict()) if report.topology_summary else None,
            chainage=RiverChainageResponse(**report.chainage_summary.to_dict()) if report.chainage_summary else None,
            scientific_disclaimer=(
                "HYDROGRAPHY SUMMARY ACTIVE — Derived from active vector dataset in EPSG:32643 metric projection."
            ),
            scientific_limitations=report.scientific_limitations,
        )

    def get_hydrography_network(self) -> RiverNetworkGraphResponse:
        """Returns the topological graph analysis of the river reach network."""
        active_file = self._get_active_hydrography_file()
        if not active_file:
            return RiverNetworkGraphResponse(
                status="UNAVAILABLE",
                source_file=None,
                metric_crs="EPSG:32643",
                topology=None,
                nodes_count=0,
                edges_count=0,
                sample_nodes=[],
                sample_edges=[],
                scientific_notice="River network graph unavailable due to unacquired source data.",
            )

        from ml.spatial.hydrography import HydrographyProcessor
        gdf, report = HydrographyProcessor.validate_and_process(active_file, clip_to_corridor=True)
        summary, graph = HydrographyProcessor.build_network_topology(gdf)

        # Sample nodes and edges for serialization
        sample_nodes = [{"id": f"{n[0]}_{n[1]}", "utm_x": n[0], "utm_y": n[1]} for n in list(graph.nodes)[:30]]
        sample_edges = []
        for u, v, data in list(graph.edges(data=True))[:30]:
            sample_edges.append({
                "source": f"{u[0]}_{u[1]}",
                "target": f"{v[0]}_{v[1]}",
                "feature_id": data.get("feature_id"),
                "name": data.get("name"),
                "waterway_class": data.get("waterway_class"),
                "length_km": data.get("length_km"),
            })

        return RiverNetworkGraphResponse(
            status="AVAILABLE",
            source_file=active_file.name,
            metric_crs="EPSG:32643",
            topology=NetworkTopologySummarySchema(**summary.to_dict()),
            nodes_count=graph.number_of_nodes(),
            edges_count=graph.number_of_edges(),
            sample_nodes=sample_nodes,
            sample_edges=sample_edges,
            scientific_notice="Reach graph constructed in EPSG:32643. Flow direction is undirected.",
        )

    def get_hydrography_chainage(self, interval_km: float = 5.0) -> RiverChainageResponse:
        """Returns downstream river station chainage from Hathnikund towards Delhi."""
        active_file = self._get_active_hydrography_file()
        if not active_file:
            return RiverChainageResponse(
                status="UNAVAILABLE",
                origin_point_name="Hathnikund Barrage (Yamunanagar)",
                terminus_point_name="Delhi Old Railway Bridge (Delhi)",
                total_chainage_km=0.0,
                station_interval_km=interval_km,
                stations_count=0,
                stations=[],
                calculation_crs="EPSG:32643",
                channel_continuity="UNAVAILABLE",
                limitations=["No river network datasets present in repository."],
            )

        from ml.spatial.hydrography import HydrographyProcessor, HydrographyClass
        gdf, report = HydrographyProcessor.validate_and_process(active_file, clip_to_corridor=True)
        main_gdf = gdf[gdf["hydro_class"] == HydrographyClass.MAIN_RIVER.value].copy()
        gap_report = HydrographyProcessor.analyze_channel_continuity(main_gdf)
        chainage = HydrographyProcessor.compute_river_chainage(main_gdf, gap_report=gap_report, interval_km=interval_km)
        return RiverChainageResponse(**chainage.to_dict())

    def inspect_hydrography_file(self, relative_file_name: str, clip_to_corridor: bool = True) -> HydrographyProcessingReportSchema:
        """Safely audits a specific file in data/raw/spatial/hydrography/ or data/processed/spatial/hydrography/."""
        from ml.spatial.hydrography import HydrographyProcessor
        clean_name = Path(relative_file_name).name
        if clean_name != relative_file_name.strip():
            raise ValueError("Directory traversal attempt blocked: supply a simple filename without path separators.")

        suffix = Path(clean_name).suffix.lower()
        if suffix not in HydrographyProcessor.ALLOWED_EXTENSIONS:
            raise ValueError(f"Invalid extension '{suffix}'. Allowed: {sorted(list(HydrographyProcessor.ALLOWED_EXTENSIONS))}")

        target_file = None
        for d in [self.proc_hydro_dir, self.hydro_dir]:
            candidate = (d / clean_name).resolve()
            if candidate.exists() and str(candidate).startswith(str(d.resolve())):
                target_file = candidate
                break

        if not target_file:
            raise FileNotFoundError(f"Requested hydrography dataset '{clean_name}' does not exist in hydrography folders.")

        _, report = HydrographyProcessor.validate_and_process(target_file, clip_to_corridor=clip_to_corridor)
        return HydrographyProcessingReportSchema(**report.to_dict())

