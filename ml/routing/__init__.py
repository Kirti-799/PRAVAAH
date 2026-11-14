"""
ml/routing/__init__.py

PRAVAAH Hydrological Routing Module.
Provides parameter schemas, hydraulic readiness evaluation,
and non-ML routing prototype algorithms for the Upper-to-Middle Yamuna River reach.
"""

from ml.routing.parameters import (
    HydraulicParameterStatus,
    HydraulicParameter,
    MuskingumParameters,
    ReachHydraulicCatalog,
    DOCUMENTED_ROUTING_CONFIGS,
    DocumentedParameterConfig,
)
from ml.routing.readiness import (
    RoutingReadinessStatus,
    RoutingReadinessEvaluator,
    ReadinessReport,
)
from ml.routing.muskingum import (
    MuskingumRouter,
    RoutingSimulationResult,
    SimulationTimeSeriesPoint,
)
from ml.routing.tabletop_scenario import (
    TabletopScenarioSimulator,
    TabletopSimulationResult,
    TabletopScenarioPreset,
    ScenarioPresetType,
    get_default_tabletop_presets,
)

__all__ = [
    "HydraulicParameterStatus",
    "HydraulicParameter",
    "MuskingumParameters",
    "ReachHydraulicCatalog",
    "DOCUMENTED_ROUTING_CONFIGS",
    "DocumentedParameterConfig",
    "RoutingReadinessStatus",
    "RoutingReadinessEvaluator",
    "ReadinessReport",
    "MuskingumRouter",
    "RoutingSimulationResult",
    "SimulationTimeSeriesPoint",
    "TabletopScenarioSimulator",
    "TabletopSimulationResult",
    "TabletopScenarioPreset",
    "ScenarioPresetType",
    "get_default_tabletop_presets",
]

