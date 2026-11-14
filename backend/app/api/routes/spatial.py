"""
backend/app/api/routes/spatial.py

FastAPI router exposing read-only Spatial Data Infrastructure & Terrain Processing endpoints:
- GET /api/spatial/inventory: Catalog of spatial datasets, coverage, resolution, and availability.
- GET /api/spatial/study-area: Authoritative rectangular bounding extent and CRS definitions.
- GET /api/spatial/dem/status: Current DEM availability, detected files, and acquisition guidelines.
- GET /api/spatial/terrain/summary: Topographical elevation and slope summary statistics.
- GET /api/spatial/river/status: River network availability and format validation status.
- GET /api/spatial/river/features: Validated river centerline GeoJSON FeatureCollection.
- POST /api/spatial/river/inspect: Sandboxed inspection of local vector hydrography files.
"""

from fastapi import APIRouter, HTTPException, status, Query
from app.schemas.spatial import (
    SpatialInventoryResponse,
    StudyAreaMetadataResponse,
    DEMStatusResponse,
    DEMValidationReportSchema,
    TerrainSummaryResponse,
    SafeInspectDEMRequest,
    RiverNetworkStatusResponse,
    RiverNetworkReportSchema,
    RiverGeoJSONResponse,
    SafeInspectRiverRequest,
    HydrographyStatusResponse,
    HydrographyLayersResponse,
    HydrographySummaryResponse,
    RiverNetworkGraphResponse,
    RiverChainageResponse,
    HydrographyProcessingReportSchema,
)
from app.schemas.routing import SpatialRoutingSimulationResponse
from app.services.spatial import SpatialService
from app.services.routing import RoutingService

router = APIRouter(prefix="/spatial", tags=["spatial"])
spatial_service = SpatialService()
routing_service = RoutingService()



@router.get(
    "/inventory",
    response_model=SpatialInventoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Spatial Dataset Inventory & Provenance",
    description=(
        "Returns the authoritative catalog of candidate geospatial datasets (SRTM, Copernicus, CartoDEM, OSM) "
        "covering the Yamuna River reach with exact acquisition status and scientific limitations."
    ),
)
def get_spatial_inventory() -> SpatialInventoryResponse:
    try:
        return spatial_service.get_inventory()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving spatial inventory: {str(exc)}",
        )


@router.get(
    "/study-area",
    response_model=StudyAreaMetadataResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Study Area Metadata & CRS Contract",
    description=(
        "Returns the verified rectangular bounding box metadata enclosing the 220 km Yamuna transit reach. "
        "Documents EPSG:4326 geographic and EPSG:32643 projected coordinates and explicit limitations."
    ),
)
def get_study_area_metadata() -> StudyAreaMetadataResponse:
    try:
        return spatial_service.get_study_area()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving study area metadata: {str(exc)}",
        )


@router.get(
    "/dem/status",
    response_model=DEMStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get DEM Ingestion & Availability Status",
    description=(
        "Scans data/raw/spatial/dem/ for physical DEM rasters. Reports whether elevation data is available "
        "or unavailable, with explicit tile placement and formatting requirements."
    ),
)
def get_dem_status() -> DEMStatusResponse:
    try:
        return spatial_service.get_dem_status()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error scanning DEM directory: {str(exc)}",
        )


@router.post(
    "/dem/inspect",
    response_model=DEMValidationReportSchema,
    status_code=status.HTTP_200_OK,
    summary="Validate and Inspect Local DEM GeoTIFF",
    description=(
        "Performs geodetic and numerical validation of a DEM raster located within data/raw/spatial/dem/. "
        "Checks CRS, geotransform, NoData masks, cell statistics, and plausible Yamuna elevation ranges."
    ),
)
def inspect_dem_file(request: SafeInspectDEMRequest) -> DEMValidationReportSchema:
    try:
        return spatial_service.inspect_dem_file(request.relative_file_name)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"DEM inspection failed: {str(exc)}",
        )


@router.get(
    "/terrain/summary",
    response_model=TerrainSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Topographical Elevation & Slope Summary",
    description=(
        "Computes elevation statistics and metric finite-difference slope summary if an active DEM is present. "
        "If unavailable, returns a structured UNAVAILABLE response with explicit scientific caveats."
    ),
)
def get_terrain_summary() -> TerrainSummaryResponse:
    try:
        return spatial_service.get_terrain_summary()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error computing terrain summary: {str(exc)}",
        )


@router.get(
    "/river/status",
    response_model=RiverNetworkStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get River Network & Hydrography Status",
    description=(
        "Scans data/raw/spatial/hydrography/ for physical vector river datasets. Reports availability, "
        "format validation status, metric reach lengths in EPSG:32643, and ingestion requirements."
    ),
)
def get_river_status() -> RiverNetworkStatusResponse:
    try:
        return spatial_service.get_river_status()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking river network status: {str(exc)}",
        )


@router.get(
    "/river/features",
    response_model=RiverGeoJSONResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Validated River Network GeoJSON Features",
    description=(
        "Returns validated river network lines as a standard GeoJSON FeatureCollection in EPSG:4326. "
        "Optionally clipped to the Yamuna study extent. If unacquired, returns empty collection with disclaimer."
    ),
)
def get_river_features(
    clip_to_corridor: bool = Query(
        default=True,
        description="Whether to clip features to the authoritative Yamuna study area bounding box.",
    )
) -> RiverGeoJSONResponse:
    try:
        return spatial_service.get_river_features(clip_to_corridor=clip_to_corridor)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error loading river features: {str(exc)}",
        )


@router.post(
    "/river/inspect",
    response_model=RiverNetworkReportSchema,
    status_code=status.HTTP_200_OK,
    summary="Validate and Inspect Local River Vector Dataset",
    description=(
        "Conducts geodetic and topological validation of a vector file in data/raw/spatial/hydrography/. "
        "Checks CRS, geometry validity, coordinate ranges, and metric lengths in EPSG:32643."
    ),
)
def inspect_river_file(request: SafeInspectRiverRequest) -> RiverNetworkReportSchema:
    try:
        report = spatial_service.inspect_river_file(request.relative_file_name)
        return report
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"River dataset inspection failed: {str(exc)}",
        )


# ==============================================================================
# Phase 3B: Advanced Hydrography & Network Topology Endpoints
# ==============================================================================

@router.get(
    "/hydrography/status",
    response_model=HydrographyStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Hydrography & River Network Status",
    description=(
        "Scans data/raw/spatial/hydrography/ and data/processed/spatial/hydrography/ for physical "
        "vector datasets. Reports availability, provenance, classification breakdown, and acquisition guide."
    ),
)
def get_hydrography_status() -> HydrographyStatusResponse:
    try:
        return spatial_service.get_hydrography_status()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking hydrography status: {str(exc)}",
        )


@router.get(
    "/hydrography/layers",
    response_model=HydrographyLayersResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Partitioned Hydrography Layers",
    description=(
        "Returns vector hydrography features partitioned into discrete semantic layers "
        "(main_river, tributary, canal, drain_minor, embankment). Features reflect centerline geometry in EPSG:4326."
    ),
)
def get_hydrography_layers(
    clip_to_corridor: bool = Query(
        default=True,
        description="Whether to clip features to the authoritative Yamuna study area bounding box.",
    )
) -> HydrographyLayersResponse:
    try:
        return spatial_service.get_hydrography_layers(clip_to_corridor=clip_to_corridor)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error loading hydrography layers: {str(exc)}",
        )


@router.get(
    "/hydrography/summary",
    response_model=HydrographySummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Hydrographic Synthesis & Continuity Summary",
    description=(
        "Returns high-level synthesis of network topology, channel length, and continuity diagnostics. "
        "Calculates metric lengths in EPSG:32643 (UTM Zone 43N)."
    ),
)
def get_hydrography_summary() -> HydrographySummaryResponse:
    try:
        return spatial_service.get_hydrography_summary()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving hydrography summary: {str(exc)}",
        )


@router.get(
    "/hydrography/network",
    response_model=RiverNetworkGraphResponse,
    status_code=status.HTTP_200_OK,
    summary="Get River Reach Network Topology Graph",
    description=(
        "Returns NetworkX topological graph analysis of the river network: node/edge counts, "
        "connected components, confluence junctions (degree >= 3), dead ends, and cycles/braids."
    ),
)
def get_hydrography_network() -> RiverNetworkGraphResponse:
    try:
        return spatial_service.get_hydrography_network()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing network topology: {str(exc)}",
        )


@router.get(
    "/hydrography/chainage",
    response_model=RiverChainageResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Downstream River Station Chainage",
    description=(
        "Computes cumulative downstream chainage (km) along the Yamuna main channel from Hathnikund Barrage "
        "towards Delhi Old Railway Bridge. If channel exhibits geometric disconnects, refuses to compute misleading chainage."
    ),
)
def get_hydrography_chainage(
    interval_km: float = Query(
        default=5.0,
        ge=1.0,
        le=50.0,
        description="Distance interval in kilometers between generated chainage stations.",
    )
) -> RiverChainageResponse:
    try:
        return spatial_service.get_hydrography_chainage(interval_km=interval_km)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error computing river chainage: {str(exc)}",
        )


@router.post(
    "/hydrography/inspect",
    response_model=HydrographyProcessingReportSchema,
    status_code=status.HTTP_200_OK,
    summary="Inspect and Validate Candidate Hydrography Vector File",
    description=(
        "Performs complete validation, coordinate check, corridor clipping, and classification "
        "of a specific vector file located inside data/raw/spatial/hydrography/ or data/processed/spatial/hydrography/."
    ),
)
def inspect_hydrography_file(
    request: SafeInspectRiverRequest,
    clip_to_corridor: bool = Query(default=True),
) -> HydrographyProcessingReportSchema:
    try:
        return spatial_service.inspect_hydrography_file(
            request.relative_file_name,
            clip_to_corridor=clip_to_corridor,
        )
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Hydrography inspection failed: {str(exc)}",
        )


@router.get(
    "/routing/simulation",
    response_model=SpatialRoutingSimulationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Spatially Referenced 1D Routing Wave Progression",
    description=(
        "Exposes 1D Muskingum routing results mapped onto continuous OSM Yamuna thalweg geometry. "
        "Strictly labels values as 1D volumetric discharge (m³/s) and NEVER estimates flood inundation or water stage."
    ),
)
def get_spatial_routing_simulation(
    episode_id: str = Query(
        default="EPISODE_2023_08",
        description="Historical episode ID to route (e.g. EPISODE_2019_04, EPISODE_2022_07, EPISODE_2023_08)",
    ),
    K_hours: float = Query(
        default=36.0,
        ge=1.0,
        le=120.0,
        description="Muskingum storage constant K in hours (wave transit time).",
    ),
    x: float = Query(
        default=0.20,
        ge=0.0,
        le=0.50,
        description="Muskingum dimensionless weighting factor x [0.0, 0.5].",
    ),
    interval_km: float = Query(
        default=5.0,
        ge=1.0,
        le=50.0,
        description="Sampling station interval in kilometers along the river centreline.",
    ),
) -> SpatialRoutingSimulationResponse:
    try:
        return routing_service.simulate_episode_spatial(
            episode_id=episode_id,
            K_hours=K_hours,
            x=x,
            sampling_interval_km=interval_km,
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Episode not found: {str(exc)}",
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Parameter validation / numerical stability error: {str(exc)}",
        )
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Required dataset unavailable: {str(exc)}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Spatial routing simulation error: {str(exc)}",
        )


