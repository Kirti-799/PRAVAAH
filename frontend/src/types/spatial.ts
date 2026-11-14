/**
 * frontend/src/types/spatial.ts
 *
 * TypeScript interface definitions for PRAVAAH Spatial Data Infrastructure & Terrain Processing.
 * Matches backend Pydantic schemas in backend/app/schemas/spatial.py.
 */

export interface SpatialDatasetItem {
  dataset_id: string;
  name: string;
  category: 'ELEVATION_DEM' | 'HYDROGRAPHY_RIVER' | 'ADMINISTRATIVE_BOUNDARY' | 'SATELLITE_INUNDATION' | 'EXPOSURE_INFRASTRUCTURE';
  source_agency: string;
  source_url: string;
  license_terms: string;
  geographic_coverage: string;
  coordinate_reference_system: string;
  spatial_resolution: string;
  vertical_units: string;
  nodata_representation: string;
  current_status: 'UNAVAILABLE_IN_REPOSITORY' | 'CANDIDATE_UNACQUIRED' | 'LOCAL_PRESENT_UNVALIDATED' | 'LOCAL_PRESENT_VALIDATED';
  expected_local_path: string;
  actual_local_path: string | null;
  acquisition_blockers: string;
  scientific_limitations: string[];
}

export interface SpatialInventoryResponse {
  service: string;
  version: string;
  milestone: string;
  total_datasets: number;
  datasets: SpatialDatasetItem[];
  scientific_disclaimer: string;
}

export interface StudyAreaBounds {
  west_lon: number;
  south_lat: number;
  east_lon: number;
  north_lat: number;
  bbox_standard_order: [number, number, number, number];
}

export interface StudyAreaMetadataResponse {
  service: string;
  version: string;
  milestone: string;
  name: string;
  description: string;
  geometry_type: string;
  geographic_crs: string;
  projected_crs: string;
  projected_crs_justification: string;
  bounds: StudyAreaBounds;
  geojson: {
    type: string;
    coordinates: number[][][];
  };
  reach_length_km: number;
  spatial_coverage: string;
  validation_status: string;
  provenance: string;
  scientific_limitations: string[];
}

export interface DEMValidationReport {
  file_path: string;
  file_name: string;
  file_size_bytes: number;
  validation_status: 'VALID' | 'VALID_WITH_DIAGNOSTIC_WARNINGS' | 'INVALID' | 'UNAVAILABLE';
  dimensions: {
    width: number;
    height: number;
    bands: number;
  };
  crs_epsg: number | null;
  crs_wkt_summary: string;
  is_geographic: boolean;
  is_projected: boolean;
  pixel_resolution_x: number;
  pixel_resolution_y: number;
  pixel_units: string;
  bounds_epsg4326: {
    west: number;
    south: number;
    east: number;
    north: number;
  };
  intersects_study_area: boolean;
  data_type: string;
  nodata_value: number | null;
  total_cells: number;
  valid_cells: number;
  missing_cells: number;
  missing_cells_percentage: number;
  has_non_finite_values: boolean;
  non_finite_count: number;

  min_elevation_m: number | null;
  max_elevation_m: number | null;
  mean_elevation_m: number | null;
  std_elevation_m: number | null;
  p10_elevation_m: number | null;
  p50_elevation_m: number | null;
  p90_elevation_m: number | null;
  plausible_yamuna_range_check: boolean;
  diagnostic_warnings: string[];
  scientific_caveats: string[];
}

export interface DEMStatusResponse {
  service: string;
  version: string;
  dem_availability: 'AVAILABLE' | 'UNAVAILABLE';
  scanned_directory: string;
  total_files_found: number;
  all_files: string[];
  active_dem_file: string | null;
  validation_report: DEMValidationReport | null;
  acquisition_guide?: {
    instructions: string;
    accepted_formats: string[];
    required_properties: string[];
  };
  scientific_notice: string;
}

export interface TerrainSlopeSummary {
  min_slope_deg: number;
  max_slope_deg: number;
  mean_slope_deg: number;
  std_slope_deg: number;
  mean_slope_percent: number;
  computation_method: string;
  horizontal_resolution_m: number;
  vertical_units: string;
  scientific_disclaimer: string;
}

export interface TerrainSummaryResponse {
  service: string;
  version: string;
  status: 'AVAILABLE' | 'UNAVAILABLE';
  source_dem_file: string | null;
  elevation_summary: {
    min_elevation_m: number | null;
    max_elevation_m: number | null;
    mean_elevation_m: number | null;
    std_elevation_m: number | null;
    p10_elevation_m: number | null;
    p50_elevation_m: number | null;
    p90_elevation_m: number | null;
    vertical_units: string;
  } | null;
  slope_summary: TerrainSlopeSummary | null;
  valid_coverage_summary: {
    total_cells: number;
    valid_cells: number;
    missing_cells: number;
    missing_cells_percentage: number;
    has_non_finite_values: boolean;
  } | null;
  scientific_disclaimer: string;
  scientific_caveats: string[];
}

export interface RiverNetworkReport {
  dataset_file: string;
  total_features: number;
  valid_features_count: number;
  invalid_features_count: number;
  empty_features_count: number;
  total_length_km: number;
  features_by_type: Record<string, number>;
  length_by_type_km: Record<string, number>;
  native_crs: string;
  projected_metric_crs: string;
  bounding_box: {
    west: number;
    south: number;
    east: number;
    north: number;
  };
  intersects_study_area: boolean;
  study_area_containment_ratio: number;
  validation_status: 'VALID' | 'VALID_WITH_WARNINGS' | 'INVALID' | 'EMPTY' | 'MISSING_CRS';
  warnings: string[];
  provenance: string;
  scientific_limitations: string[];
}

export interface RiverNetworkStatusResponse {
  service: string;
  version: string;
  milestone: string;
  river_data_availability: 'AVAILABLE' | 'UNAVAILABLE';
  scanned_directory: string;
  total_files_found: number;
  all_files: string[];
  active_river_file: string | null;
  validation_report: RiverNetworkReport | null;
  acquisition_guide?: {
    instructions: string;
    accepted_formats: string[];
    required_properties: string[];
  };
  scientific_notice: string;
}

export interface RiverGeoJSONFeature {
  type: 'Feature';
  id: string;
  geometry: {
    type: string;
    coordinates: any;
  };
  properties: {
    feature_id: string;
    name: string;
    waterway_type: string;
    length_km: number;
    source_dataset: string;
    study_corridor: string;
  };
}

export interface RiverGeoJSONResponse {
  type: 'FeatureCollection';
  features: RiverGeoJSONFeature[];
  crs?: {
    type: string;
    properties: Record<string, any>;
  };
  properties: {
    status?: string;
    total_features?: number;
    source_file?: string;
    metric_crs?: string;
    disclaimer?: string;
    layer_class?: string;
    features_count?: number;
    total_length_km?: number;
  };
}

// --- Phase 3B: Advanced Hydrography & Network Interfaces ---

export interface ChannelGapReport {
  gap_count: number;
  max_gap_distance_m: number;
  total_gap_distance_m: number;
  gap_locations: Array<{
    segment_index: number;
    gap_distance_m: number;
    segment_a_end: [number, number];
    segment_b_start: [number, number];
  }>;
  continuity_status: 'CONTINUOUS' | 'FRAGMENTED' | 'DISCONNECTED' | 'UNAVAILABLE';
  is_continuous: boolean;
  diagnostic_notes: string[];
}

export interface ChainageStation {
  station_id: string;
  chainage_km: number;
  chainage_m: number;
  latitude: number;
  longitude: number;
  reach_name: string;
  is_landmark: boolean;
  landmark_name: string | null;
}

export interface RiverChainageResponse {
  service: string;
  version: string;
  status: 'AVAILABLE' | 'UNAVAILABLE' | 'DISCONNECTED_REFUSED' | 'FRAGMENTED_LIMITED';
  origin_point_name: string;
  terminus_point_name: string;
  total_chainage_km: number;
  station_interval_km: number;
  stations_count: number;
  stations: ChainageStation[];
  calculation_crs: string;
  channel_continuity: 'CONTINUOUS' | 'FRAGMENTED' | 'DISCONNECTED' | 'UNAVAILABLE';
  limitations: string[];
}

export interface NetworkTopologySummary {
  total_nodes: number;
  total_edges: number;
  connected_components_count: number;
  giant_component_nodes: number;
  giant_component_ratio: number;
  isolated_edges_count: number;
  confluence_junctions_count: number;
  dead_end_nodes_count: number;
  has_cycles_or_braids: boolean;
  cycles_count: number;
  flow_direction_verified: boolean;
  scientific_notes: string[];
}

export interface RiverNetworkGraphResponse {
  service: string;
  version: string;
  status: string;
  source_file: string | null;
  metric_crs: string;
  topology: NetworkTopologySummary | null;
  nodes_count: number;
  edges_count: number;
  sample_nodes: Array<{ id: string; utm_x: number; utm_y: number }>;
  sample_edges: Array<{
    source: string;
    target: string;
    feature_id?: string;
    name?: string;
    waterway_class?: string;
    length_km?: number;
  }>;
  scientific_notice: string;
}

export interface HydrographyProcessingReport {
  source_file: string;
  total_raw_features: number;
  valid_features_count: number;
  invalid_features_count: number;
  empty_features_count: number;
  duplicate_features_count: number;
  features_within_corridor: number;
  total_network_length_km: number;
  features_by_class: Record<string, number>;
  length_by_class_km: Record<string, number>;
  native_crs: string;
  metric_crs: string;
  bounding_box: {
    west: number;
    south: number;
    east: number;
    north: number;
  };
  validation_status: 'VALID' | 'VALID_WITH_WARNINGS' | 'INVALID' | 'EMPTY';
  main_channel_continuity: 'CONTINUOUS' | 'FRAGMENTED' | 'DISCONNECTED' | 'UNAVAILABLE';
  main_channel_length_km: number;
  topology_summary: NetworkTopologySummary | null;
  chainage_summary: RiverChainageResponse | null;
  transformation_log: string[];
  warnings: string[];
  scientific_limitations: string[];
}

export interface HydrographyStatusResponse {
  service: string;
  version: string;
  milestone: string;
  hydrography_availability: 'AVAILABLE' | 'UNAVAILABLE';
  scanned_directories: string[];
  total_files_found: number;
  all_files: string[];
  active_hydrography_file: string | null;
  processing_report: HydrographyProcessingReport | null;
  acquisition_guide?: {
    required_coverage: string;
    recommended_sources: string[];
    target_placement_directory: string;
    accepted_formats: string[];
  };
  scientific_notice: string;
}

export interface HydrographyLayersResponse {
  service: string;
  version: string;
  status: 'AVAILABLE' | 'UNAVAILABLE';
  active_file: string | null;
  layers: Record<string, RiverGeoJSONResponse>;
  features_by_class: Record<string, number>;
  length_by_class_km: Record<string, number>;
  metric_crs: string;
  scientific_disclaimer: string;
}

export interface HydrographySummaryResponse {
  service: string;
  version: string;
  status: 'AVAILABLE' | 'UNAVAILABLE';
  active_file: string | null;
  total_features: number;
  total_network_length_km: number;
  features_by_class: Record<string, number>;
  length_by_class_km: Record<string, number>;
  main_channel_continuity: string;
  main_channel_length_km: number;
  topology: NetworkTopologySummary | null;
  chainage: RiverChainageResponse | null;
  scientific_disclaimer: string;
  scientific_limitations: string[];
}

// --- Phase 3D: Upstream Catchment & Spatial Rainfall Interfaces ---

export interface PourPointInfo {
  name: string;
  nominal_coordinates: [number, number];
  snapped_coordinates: [number, number];
  distance_snapped_m: number;
  provenance: string;
}

export interface CatchmentSummaryResponse {
  catchment_id: string;
  catchment_name: string;
  pour_point: PourPointInfo;
  area_sq_km: number;
  perimeter_km: number;
  elevation_min_m: number;
  elevation_max_m: number;
  elevation_mean_m: number;
  elevation_median_m: number;
  elevation_std_m: number;
  hypsometry_percentiles: Record<string, number>;
  bounding_box: {
    south: number;
    north: number;
    west: number;
    east: number;
  };
  contributing_cells_count: number;
  stream_length_total_km: number;
  drainage_density_km_per_sq_km: number;
  major_tributaries: string[];
  scientific_caveats: string[];
}

export interface CatchmentStatusResponse {
  service: string;
  delineation_status: string;
  area_sq_km: number;
  pour_point_name: string;
  pour_point_lat: number;
  pour_point_lon: number;
  raw_dem_tiles_acquired: number;
  raw_dem_tiles_required: number;
  has_drainage_network: boolean;
  scientific_integrity_note: string;
}

export interface RainfallRateSummary {
  mean_mm: number;
  min_mm: number;
  max_mm: number;
  std_mm: number;
}

export interface RainfallAccumulationSummary {
  acc_24h_mm: number;
  acc_72h_mm: number;
  acc_168h_mm: number;
}

export interface AntecedentPrecipitationSummary {
  api_3_mm: number;
  api_7_mm: number;
  api_14_mm: number;
  decay_factor_k: number;
}

export interface CatchmentRainfallPoint {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  elevation_m: number;
  current_mm: number;
  forecast_24h_mm: number;
  api_3_mm: number;
}

export interface CatchmentRainfallSummaryResponse {
  catchment_id: string;
  provider: string;
  timestamp: string;
  observation_or_forecast: string;
  contributing_points_count: number;
  spatial_coverage_percentage: number;
  missing_data_percentage: number;
  current_rate: RainfallRateSummary;
  accumulations: RainfallAccumulationSummary;
  antecedent_indices: AntecedentPrecipitationSummary;
  sample_grid_points: CatchmentRainfallPoint[];
  scientific_disclaimer: string;
}

export interface RainfallStatusResponse {
  provider_name: string;
  is_available: boolean;
  status_code?: number;
  latency_ms?: number;
  spatial_sampling_nodes_count: number;
  catchment_bounding_box: {
    south: number;
    north: number;
    west: number;
    east: number;
  };
  active_aggregation_window_hours: number[];
  notes: string[];
}


