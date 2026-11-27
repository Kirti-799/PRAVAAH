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
from ml.spatial.inventory import (
    SpatialDatasetCategory,
    SpatialDataStatus,
    SpatialDatasetEntry,
    SpatialInventoryCatalog,
)
from ml.spatial.rainfall import (
    CatchmentGridPoint,
    CatchmentRainfallAggregator,
    CatchmentSpatialRainfallSummary,
)

_LAZY_MODULE_MAP = {
    # DEM
    "DEMValidationStatus": "ml.spatial.dem",
    "DEMMetadataReport": "ml.spatial.dem",
    "TerrainSlopeSummary": "ml.spatial.dem",
    "DEMValidator": "ml.spatial.dem",
    # River
    "WaterwayType": "ml.spatial.river",
    "RiverValidationStatus": "ml.spatial.river",
    "RiverFeatureMetadata": "ml.spatial.river",
    "RiverNetworkReport": "ml.spatial.river",
    "RiverNetworkValidator": "ml.spatial.river",
    # Hydrography
    "HydrographyClass": "ml.spatial.hydrography",
    "ChannelContinuityStatus": "ml.spatial.hydrography",
    "HydrographyValidationStatus": "ml.spatial.hydrography",
    "ChannelGapReport": "ml.spatial.hydrography",
    "ChainageStation": "ml.spatial.hydrography",
    "RiverChainageReport": "ml.spatial.hydrography",
    "NetworkTopologySummary": "ml.spatial.hydrography",
    "HydrographyProcessingReport": "ml.spatial.hydrography",
    "HydrographyProcessor": "ml.spatial.hydrography",
    # DEM Acquisition
    "DEMAcquisitionManager": "ml.spatial.dem_acquisition",
    "DEMTileCatalogEntry": "ml.spatial.dem_acquisition",
    # Catchment
    "CatchmentDelineator": "ml.spatial.catchment",
    "D8FlowEngine": "ml.spatial.catchment",
    "CatchmentMorphometryReport": "ml.spatial.catchment",
}

def __getattr__(name: str):
    if name in _LAZY_MODULE_MAP:
        import importlib
        mod = importlib.import_module(_LAZY_MODULE_MAP[name])
        return getattr(mod, name)
    raise AttributeError(f"module 'ml.spatial' has no attribute '{name}'")

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

