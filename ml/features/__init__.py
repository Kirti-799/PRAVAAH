"""
ml/features/__init__.py

PRAVAAH Feature Engineering Package.
Provides formal schema manifest and leakage-free temporal transformation pipelines
for upstream Hathnikund discharge forecasting.
"""

from ml.features.feature_manifest import (
    FeatureMetadata,
    FEATURE_MANIFEST,
    get_feature_names_by_classification,
    get_feature_metadata_dict,
)
from ml.features.feature_pipeline import DischargeFeaturePipeline

__all__ = [
    "FeatureMetadata",
    "FEATURE_MANIFEST",
    "get_feature_names_by_classification",
    "get_feature_metadata_dict",
    "DischargeFeaturePipeline",
]
