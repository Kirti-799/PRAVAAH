"""
backend/app/schemas/spatial.py

Pydantic schemas for the PRAVAAH Spatial Data Infrastructure & Terrain Processing Service.
Defines typed models for dataset inventories, study-area contracts, DEM validation reports,
and terrain slope summaries.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class SpatialDatasetSchema(BaseModel):
    dataset_id: str
    name: str
    category: str
    source_agency: str
    source_url: str
    license_terms: str
    geographic_coverage: str
    coordinate_reference_system: str
    spatial_resolution: str
    vertical_units: str
    nodata_representation: str
    current_status: str
    expected_local_path: str
    actual_local_path: Optional[str] = None
    acquisition_blockers: str
    scientific_limitations: List[str]


class SpatialInventoryResponse(BaseModel):
    service: str = "PRAVAAH Spatial Data Infrastructure"
    version: str = "1.0.0"
    milestone: str = "Phase 3A — Spatial Data Infrastructure & Terrain Processing"
    total_datasets: int
    datasets: List[SpatialDatasetSchema]
    scientific_disclaimer: str = (
        "Dataset inventory documents candidate geospatial repositories. Unacquired datasets "
        "are explicitly labeled UNAVAILABLE_IN_REPOSITORY. Synthetic substitution is prohibited."
    )


class StudyAreaBoundsSchema(BaseModel):
    west_lon: float
    south_lat: float
    east_lon: float
    north_lat: float
    bbox_standard_order: List[float] = Field(
        description="Standard [west_lon, south_lat, east_lon, north_lat] bounding box array."
    )


class StudyAreaMetadataResponse(BaseModel):
    service: str = "PRAVAAH Study Area & Geodetic Boundary Service"
    version: str = "1.0.0"
    milestone: str = "Phase 3A — Spatial Data Infrastructure & Terrain Processing"
    name: str
    description: str
    geometry_type: str
    geographic_crs: str
    projected_crs: str
    projected_crs_justification: str
    bounds: StudyAreaBoundsSchema
    geojson: Dict[str, Any]
    reach_length_km: float
    spatial_coverage: str
    validation_status: str
    provenance: str
    scientific_limitations: List[str]


class DEMValidationReportSchema(BaseModel):
    file_path: str
    file_name: str
    file_size_bytes: int
    validation_status: str
    dimensions: Dict[str, int]
    crs_epsg: Optional[int] = None
    crs_wkt_summary: str
    is_geographic: bool
    is_projected: bool
    pixel_resolution_x: float
    pixel_resolution_y: float
    pixel_units: str
    bounds_epsg4326: Dict[str, float]
    intersects_study_area: bool
    data_type: str
    nodata_value: Optional[float] = None
    total_cells: int
    valid_cells: int
    missing_cells: int
    missing_cells_percentage: float
    has_non_finite_values: bool
    non_finite_count: int
    min_elevation_m: Optional[float] = None
    max_elevation_m: Optional[float] = None
    mean_elevation_m: Optional[float] = None
    std_elevation_m: Optional[float] = None
    p10_elevation_m: Optional[float] = None
    p50_elevation_m: Optional[float] = None
    p90_elevation_m: Optional[float] = None
    plausible_yamuna_range_check: bool
    diagnostic_warnings: List[str]
    scientific_caveats: List[str]


class DEMStatusResponse(BaseModel):
    service: str = "PRAVAAH DEM Ingestion & Validation Inspector"
    version: str = "1.0.0"
    dem_availability: str  # AVAILABLE or UNAVAILABLE
    scanned_directory: str
    total_files_found: int
    all_files: List[str] = Field(default_factory=list)
    active_dem_file: Optional[str] = None
    validation_report: Optional[DEMValidationReportSchema] = None
    acquisition_guide: Optional[Dict[str, Any]] = None
    scientific_notice: str


class TerrainSlopeSummarySchema(BaseModel):
    min_slope_deg: float
    max_slope_deg: float
    mean_slope_deg: float
    std_slope_deg: float
    mean_slope_percent: float
    computation_method: str
    horizontal_resolution_m: float
    vertical_units: str
    scientific_disclaimer: str


class TerrainSummaryResponse(BaseModel):
    service: str = "PRAVAAH Topographical Terrain Analysis Engine"
    version: str = "1.0.0"
    status: str  # AVAILABLE or UNAVAILABLE
    source_dem_file: Optional[str] = None
    elevation_summary: Optional[Dict[str, Any]] = None
    slope_summary: Optional[TerrainSlopeSummarySchema] = None
    valid_coverage_summary: Optional[Dict[str, Any]] = None
    scientific_disclaimer: str
    scientific_caveats: List[str]


class SafeInspectDEMRequest(BaseModel):
    relative_file_name: str = Field(
        ...,
        description="Relative filename inside data/raw/spatial/dem/ (e.g. 'srtm_yamuna_30m.tif'). Directory traversal is blocked.",
    )


class RiverNetworkReportSchema(BaseModel):
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
    validation_status: str
    warnings: List[str]
    provenance: str
    scientific_limitations: List[str]


class RiverNetworkStatusResponse(BaseModel):
    service: str = "PRAVAAH River Network & Hydrography Inspector"
    version: str = "1.0.0"
    milestone: str = "Phase 3B — River Network & Geospatial Layer Integration"
    river_data_availability: str  # AVAILABLE or UNAVAILABLE
    scanned_directory: str
    total_files_found: int
    all_files: List[str] = Field(default_factory=list)
    active_river_file: Optional[str] = None
    validation_report: Optional[RiverNetworkReportSchema] = None
    acquisition_guide: Optional[Dict[str, Any]] = None
    scientific_notice: str


class RiverGeoJSONResponse(BaseModel):
    type: str = "FeatureCollection"
    features: List[Dict[str, Any]] = Field(default_factory=list)
    crs: Optional[Dict[str, Any]] = None
    properties: Dict[str, Any] = Field(default_factory=dict)


class SafeInspectRiverRequest(BaseModel):
    relative_file_name: str = Field(
        ...,
        description="Relative filename inside data/raw/spatial/hydrography/ (e.g. 'osm_yamuna_waterways.geojson'). Directory traversal is blocked.",
    )


# --- Phase 3B: Advanced Hydrography & Network Topology Schemas ---

class ChannelGapReportSchema(BaseModel):
    gap_count: int
    max_gap_distance_m: float
    total_gap_distance_m: float
    gap_locations: List[Dict[str, Any]] = Field(default_factory=list)
    continuity_status: str
    is_continuous: bool
    diagnostic_notes: List[str] = Field(default_factory=list)


class ChainageStationSchema(BaseModel):
    station_id: str
    chainage_km: float
    chainage_m: float
    latitude: float
    longitude: float
    reach_name: str
    is_landmark: bool
    landmark_name: Optional[str] = None


class RiverChainageResponse(BaseModel):
    service: str = "PRAVAAH River Chainage & Stationing Service"
    version: str = "1.0.0"
    status: str  # "AVAILABLE", "UNAVAILABLE", "DISCONNECTED_REFUSED"
    origin_point_name: str
    terminus_point_name: str
    total_chainage_km: float
    station_interval_km: float
    stations_count: int
    stations: List[ChainageStationSchema] = Field(default_factory=list)
    calculation_crs: str
    channel_continuity: str
    limitations: List[str] = Field(default_factory=list)


class NetworkTopologySummarySchema(BaseModel):
    total_nodes: int
    total_edges: int
    connected_components_count: int
    giant_component_nodes: int
    giant_component_ratio: float
    isolated_edges_count: int
    confluence_junctions_count: int
    dead_end_nodes_count: int
    has_cycles_or_braids: bool
    cycles_count: int
    flow_direction_verified: bool
    scientific_notes: List[str] = Field(default_factory=list)


class RiverNetworkGraphResponse(BaseModel):
    service: str = "PRAVAAH Hydrographic Reach Network Graph Service"
    version: str = "1.0.0"
    status: str
    source_file: Optional[str] = None
    metric_crs: str = "EPSG:32643"
    topology: Optional[NetworkTopologySummarySchema] = None
    nodes_count: int = 0
    edges_count: int = 0
    sample_nodes: List[Dict[str, Any]] = Field(default_factory=list)
    sample_edges: List[Dict[str, Any]] = Field(default_factory=list)
    scientific_notice: str


class HydrographyProcessingReportSchema(BaseModel):
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
    validation_status: str
    main_channel_continuity: str
    main_channel_length_km: float
    topology_summary: Optional[NetworkTopologySummarySchema] = None
    chainage_summary: Optional[RiverChainageResponse] = None
    transformation_log: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    scientific_limitations: List[str] = Field(default_factory=list)


class HydrographyStatusResponse(BaseModel):
    service: str = "PRAVAAH River Hydrography & Network Inspector"
    version: str = "1.0.0"
    milestone: str = "Phase 3B — River Hydrography & Network Integration"
    hydrography_availability: str  # AVAILABLE or UNAVAILABLE
    scanned_directories: List[str]
    total_files_found: int
    all_files: List[str] = Field(default_factory=list)
    active_hydrography_file: Optional[str] = None
    processing_report: Optional[HydrographyProcessingReportSchema] = None
    acquisition_guide: Optional[Dict[str, Any]] = None
    scientific_notice: str


class HydrographyLayersResponse(BaseModel):
    service: str = "PRAVAAH Hydrographic Layer Catalog"
    version: str = "1.0.0"
    status: str  # AVAILABLE or UNAVAILABLE
    active_file: Optional[str] = None
    layers: Dict[str, RiverGeoJSONResponse]
    features_by_class: Dict[str, int]
    length_by_class_km: Dict[str, float]
    metric_crs: str = "EPSG:32643"
    scientific_disclaimer: str


class HydrographySummaryResponse(BaseModel):
    service: str = "PRAVAAH Hydrographic Synthesis Engine"
    version: str = "1.0.0"
    status: str
    active_file: Optional[str] = None
    total_features: int
    total_network_length_km: float
    features_by_class: Dict[str, int]
    length_by_class_km: Dict[str, float]
    main_channel_continuity: str
    main_channel_length_km: float
    topology: Optional[NetworkTopologySummarySchema] = None
    chainage: Optional[RiverChainageResponse] = None
    scientific_disclaimer: str
    scientific_limitations: List[str] = Field(default_factory=list)

