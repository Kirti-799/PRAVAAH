"""
ml/spatial/__init__.py

PRAVAAH Spatial Data Infrastructure & Terrain Processing Module.
Provides study area contracts, geodetic bounds validation, DEM inspection,
and terrain slope analysis.
"""

from ml.spatial.study_area import (
    GeometryType,
    StudyAreaBounds,
    StudyAreaMetadata,
    StudyAreaCatalog,
    validate_spatial_bounds,
)
from ml.spatial.dem import (
    DEMValidationStatus,
    DEMMetadataReport,
    TerrainSlopeSummary,
    DEMValidator,
)
from ml.spatial.inventory import (
    SpatialDatasetCategory,
    SpatialDataStatus,
    SpatialDatasetEntry,
    SpatialInventoryCatalog,
)
from ml.spatial.river import (
    WaterwayType,
    RiverValidationStatus,
    RiverFeatureMetadata,
    RiverNetworkReport,
    RiverNetworkValidator,
)
from ml.spatial.hydrography import (
    HydrographyClass,
    ChannelContinuityStatus,
    HydrographyValidationStatus,
    ChannelGapReport,
    ChainageStation,
    RiverChainageReport,
    NetworkTopologySummary,
    HydrographyProcessingReport,
    HydrographyProcessor,
)
from ml.spatial.dem_acquisition import (
    DEMAcquisitionManager,
    DEMTileCatalogEntry,
)
from ml.spatial.catchment import (
    CatchmentDelineator,
    D8FlowEngine,
    CatchmentMorphometryReport,
)
from ml.spatial.rainfall import (
    CatchmentGridPoint,
    CatchmentRainfallAggregator,
    CatchmentSpatialRainfallSummary,
)

__all__ = [
    "GeometryType",
    "StudyAreaBounds",
    "StudyAreaMetadata",
    "StudyAreaCatalog",
    "validate_spatial_bounds",
    "DEMValidationStatus",
    "DEMMetadataReport",
    "TerrainSlopeSummary",
    "DEMValidator",
    "SpatialDatasetCategory",
    "SpatialDataStatus",
    "SpatialDatasetEntry",
    "SpatialInventoryCatalog",
    "WaterwayType",
    "RiverValidationStatus",
    "RiverFeatureMetadata",
    "RiverNetworkReport",
    "RiverNetworkValidator",
    "HydrographyClass",
    "ChannelContinuityStatus",
    "HydrographyValidationStatus",
    "ChannelGapReport",
    "ChainageStation",
    "RiverChainageReport",
    "NetworkTopologySummary",
    "HydrographyProcessingReport",
    "HydrographyProcessor",
    "DEMAcquisitionManager",
    "DEMTileCatalogEntry",
    "CatchmentDelineator",
    "D8FlowEngine",
    "CatchmentMorphometryReport",
    "CatchmentGridPoint",
    "CatchmentRainfallAggregator",
    "CatchmentSpatialRainfallSummary",
]

