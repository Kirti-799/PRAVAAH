"""
ml/routing/readiness.py

Routing Readiness and Hydraulic Feasibility Assessment Engine for PRAVAAH.
Rigorously evaluates whether available data supports physically meaningful
routing from Hathnikund Barrage to Delhi Old Railway Bridge.

AUDIT CONCLUSIONS:
1. Hydrodynamic Saint-Venant 1D/2D: INFEASIBLE (missing surveyed bathymetry,
   cross-sections, Manning's n, lateral flows).
2. Muskingum-Cunge: INFEASIBLE (missing cross-sectional bottom width, bank slopes).
3. Calibrated Hydrological Routing: BLOCKED (missing continuous downstream target
   observations for CWC Station 028-MDD, Delhi ORB).
4. Uncalibrated Muskingum Sensitivity Prototype: CONDITIONALLY FEASIBLE strictly as
   an exploratory, parameter-dependent simulation, with zero calibration claims
   and zero stage prediction.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from ml.routing.parameters import (
    HydraulicParameterStatus,
    ReachHydraulicCatalog,
    HydraulicParameter,
)


class RoutingReadinessStatus(str, Enum):
    ROUTING_NOT_READY_MISSING_HYDRAULIC_DATA = "ROUTING_NOT_READY_MISSING_HYDRAULIC_DATA"
    ROUTING_PARAMETRIC_PROTOTYPE_UNCALIBRATED = "ROUTING_PARAMETRIC_PROTOTYPE_UNCALIBRATED"
    CALIBRATED_ROUTING_BLOCKED_MISSING_TARGET_STAGE = "CALIBRATED_ROUTING_BLOCKED_MISSING_TARGET_STAGE"


@dataclass
class MethodFeasibilityItem:
    method_name: str
    is_feasible: bool
    data_requirements: List[str]
    missing_requirements: List[str]
    verdict_rationale: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "method_name": self.method_name,
            "is_feasible": self.is_feasible,
            "data_requirements": self.data_requirements,
            "missing_requirements": self.missing_requirements,
            "verdict_rationale": self.verdict_rationale,
        }


@dataclass
class ReadinessReport:
    """Detailed diagnostic report on hydrological routing readiness."""
    readiness_status: RoutingReadinessStatus
    summary_verdict: str
    target_gauge_id: str = "028-MDD"
    target_gauge_name: str = "Delhi Old Railway Bridge"
    downstream_calibration_available: bool = False
    methods_evaluation: List[MethodFeasibilityItem] = field(default_factory=list)
    parameters_summary: Dict[str, int] = field(default_factory=dict)
    parameters_detail: List[Dict[str, Any]] = field(default_factory=list)
    critical_blockers: List[str] = field(default_factory=list)
    scientific_limitations: List[str] = field(default_factory=list)
    next_recommended_actions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "readiness_status": self.readiness_status.value,
            "summary_verdict": self.summary_verdict,
            "target_gauge_id": self.target_gauge_id,
            "target_gauge_name": self.target_gauge_name,
            "downstream_calibration_available": self.downstream_calibration_available,
            "methods_evaluation": [m.to_dict() for m in self.methods_evaluation],
            "parameters_summary": self.parameters_summary,
            "parameters_detail": self.parameters_detail,
            "critical_blockers": self.critical_blockers,
            "scientific_limitations": self.scientific_limitations,
            "next_recommended_actions": self.next_recommended_actions,
        }


class RoutingReadinessEvaluator:
    """Evaluates hydraulic readiness for routing across the 220 km Yamuna reach."""

    @classmethod
    def evaluate(cls, has_upstream_discharge: bool = True) -> ReadinessReport:
        params = ReachHydraulicCatalog.get_reach_parameters()

        # Count parameter statuses
        counts: Dict[str, int] = {
            HydraulicParameterStatus.MEASURED.value: 0,
            HydraulicParameterStatus.DERIVED.value: 0,
            HydraulicParameterStatus.ASSUMED.value: 0,
            HydraulicParameterStatus.UNAVAILABLE.value: 0,
        }
        for p in params:
            counts[p.status.value] += 1

        # Evaluate Candidate Methods
        methods = [
            MethodFeasibilityItem(
                method_name="1D/2D Hydrodynamic St. Venant (Dynamic Wave)",
                is_feasible=False,
                data_requirements=[
                    "Surveyed bathymetric cross-sections (every 500m–1km)",
                    "Calibrated Manning's n roughness field",
                    "Downstream rating curve or water surface profile at Delhi ORB",
                    "Continuous lateral inflow hydrographs for Som/Pathrala tributaries",
                    "Sluice gate opening logs for Wazirabad and ITO Barrages",
                ],
                missing_requirements=[
                    "Cross-sections and bathymetry (UNAVAILABLE)",
                    "Manning's roughness coefficient (UNAVAILABLE)",
                    "Downstream stage-discharge rating curve (UNAVAILABLE)",
                    "Intermediate tributary hydrographs (UNAVAILABLE)",
                    "Intermediate barrage gate operations (UNAVAILABLE)",
                ],
                verdict_rationale=(
                    "Scientifically infeasible. 1D/2D hydraulic models require continuous geometry "
                    "and calibrated roughness. Implementing this model would require inventing "
                    "synthetic channel bathymetry, violating core hydrological standards."
                ),
            ),
            MethodFeasibilityItem(
                method_name="Muskingum-Cunge Hydraulic Routing Approximation",
                is_feasible=False,
                data_requirements=[
                    "Channel bed width and cross-sectional geometry",
                    "Bed slope (S_0)",
                    "Channel Manning's n roughness",
                    "Spatial discretization grid (dx)",
                ],
                missing_requirements=[
                    "Channel cross-sectional geometry (UNAVAILABLE)",
                    "Roughness n (UNAVAILABLE)",
                ],
                verdict_rationale=(
                    "Infeasible without fabricating channel geometry. Muskingum-Cunge computes "
                    "K and x dynamically from channel width and hydraulic radius. Without cross-sectional "
                    "surveys across 220 km of shifting alluvial bed, these parameters cannot be derived."
                ),
            ),
            MethodFeasibilityItem(
                method_name="Calibrated Hydrological Muskingum Routing",
                is_feasible=False,
                data_requirements=[
                    "Observed upstream inflow hydrograph (HKB D/S)",
                    "Observed downstream outflow hydrograph (Delhi ORB discharge)",
                    "Continuous downstream stage records to optimize storage constant K and weighting x",
                ],
                missing_requirements=[
                    "Downstream observed hydrograph / stage at Delhi ORB (UNAVAILABLE)",
                ],
                verdict_rationale=(
                    "Calibrated forecasting is strictly blocked. In hydrological engineering, "
                    "Muskingum K and x must be calibrated against observed downstream hydrographs. "
                    "Without continuous target observations, parameters cannot be empirically optimized."
                ),
            ),
            MethodFeasibilityItem(
                method_name="Uncalibrated Parameter-Dependent Muskingum Prototype",
                is_feasible=has_upstream_discharge,
                data_requirements=[
                    "Verified upstream discharge time series (HKB D/S)",
                    "Assumed travel time K based on physical distance / wave celerity",
                    "Assumed weighting parameter x based on alluvial floodplain characteristics",
                    "Strict numerical stability checking (2Kx < dt < 2K(1-x))",
                    "Mass-balance conservation verification",
                ],
                missing_requirements=[],
                verdict_rationale=(
                    "Conditionally feasible strictly as an exploratory sensitivity prototype. "
                    "Outputs must be explicitly tagged as SIMULATED UNCALIBRATED DISCHARGE and "
                    "never equated to observed Delhi stage or flood probabilities."
                ),
            ),
        ]

        if not has_upstream_discharge:
            status = RoutingReadinessStatus.ROUTING_NOT_READY_MISSING_HYDRAULIC_DATA
            verdict = (
                "ROUTING NOT READY: Upstream discharge observations are missing or unavailable. "
                "Routing calculations cannot proceed."
            )
        else:
            status = RoutingReadinessStatus.ROUTING_PARAMETRIC_PROTOTYPE_UNCALIBRATED
            verdict = (
                "PARAMETRIC PROTOTYPE ONLY (UNCALIBRATED): Upstream release observations (HKB D/S) "
                "are available and complete. However, continuous downstream target observations (Delhi ORB) "
                "and reach cross-sections remain unavailable. Only an uncalibrated sensitivity simulation "
                "can run. Supervised stage forecasting remains blocked."
            )

        blockers = [
            "Downstream continuous stage records for CWC Station 028-MDD (Delhi ORB) remain restricted on open portals.",
            "Zero surveyed cross-sections or bathymetric soundings exist in the repository for the 220 km reach.",
            "Intermediate tributary inflows (Som, Pathrala) are unmetered in available datasets.",
            "Wazirabad and ITO barrage operational gate discharge logs are not available.",
        ]

        limitations = [
            "Simulated routed discharge represents an uncalibrated parametric approximation, NOT an empirical forecast.",
            "Simulated discharge CANNOT be converted to a downstream water level (m MSL) due to absence of an authoritative rating curve.",
            "An assumed physical travel time (e.g. 36h) does NOT represent a validated operational forecast lead time.",
            "Exceedance of upstream discharge thresholds does NOT constitute a confirmed downstream stage breach.",
            "Daily time step (24h) causes significant numerical dispersion relative to flood wave transit times.",
        ]

        actions = [
            "Formal institutional requisition to CWC / India-WRIS for historical hourly/daily stage registers at Station 028-MDD.",
            "Acquisition of high-resolution digital elevation data (e.g. LiDAR or surveyed cross-sections) for the Yamuna floodway.",
            "Ingestion of tributary stream gauges for Som and Pathrala rivers to capture lateral flash contributions.",
            "Sub-daily (hourly) temporal resolution for both upstream barrage releases and downstream stage monitoring.",
        ]

        return ReadinessReport(
            readiness_status=status,
            summary_verdict=verdict,
            downstream_calibration_available=False,
            methods_evaluation=methods,
            parameters_summary=counts,
            parameters_detail=[p.to_dict() for p in params],
            critical_blockers=blockers,
            scientific_limitations=limitations,
            next_recommended_actions=actions,
        )
