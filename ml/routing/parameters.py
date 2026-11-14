"""
ml/routing/parameters.py

Hydraulic Parameter Schemas, Provenance Tracking, and Validation for PRAVAAH.
Defines explicit typed models for reach geometry, bed slope, roughness,
storage characteristics, lateral boundary conditions, and Muskingum coefficients.

SCIENTIFIC INTEGRITY ENFORCEMENT:
- Every hydraulic parameter is assigned an explicit provenance status:
  MEASURED, DERIVED, ASSUMED, or UNAVAILABLE.
- Never invents bathymetry or silently substitutes uncalibrated roughness coefficients.
- Enforces strict physical bounds and numerical stability criteria:
  2Kx < dt < 2K(1-x).
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple


class HydraulicParameterStatus(str, Enum):
    MEASURED = "MEASURED"
    DERIVED = "DERIVED"
    ASSUMED = "ASSUMED"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class HydraulicParameter:
    """Representation of an individual hydraulic parameter with provenance and uncertainty."""
    name: str
    symbol: str
    unit: str
    value: Optional[float]
    status: HydraulicParameterStatus
    provenance: str
    spatial_applicability: str
    temporal_applicability: str
    uncertainty_description: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "symbol": self.symbol,
            "unit": self.unit,
            "value": self.value,
            "status": self.status.value,
            "provenance": self.provenance,
            "spatial_applicability": self.spatial_applicability,
            "temporal_applicability": self.temporal_applicability,
            "uncertainty_description": self.uncertainty_description,
        }


class ReachHydraulicCatalog:
    """
    Authoritative catalog of hydraulic parameters for the Yamuna River reach
    from Hathnikund Barrage (HKB) to Delhi Old Railway Bridge (ORB), ~220 km.
    """

    @classmethod
    def get_reach_parameters(cls) -> List[HydraulicParameter]:
        return [
            HydraulicParameter(
                name="Reach Thalweg Length",
                symbol="L",
                unit="km",
                value=220.0,
                status=HydraulicParameterStatus.DERIVED,
                provenance="Derived from Survey of India / CWC Yamuna Basin River Thalweg Trace",
                spatial_applicability="Hathnikund Barrage (30.315°N, 77.583°E) to Delhi ORB (28.663°N, 77.249°E)",
                temporal_applicability="Static reach geometry (low-to-high flow average)",
                uncertainty_description=(
                    "Thalweg sinuosity ranges from ~215 km (high-flow meander cutoff) "
                    "to ~225 km (low-flow braided thalweg). Nominal travel distance uncertainty ±5 km."
                ),
            ),
            HydraulicParameter(
                name="Average Bed Slope",
                symbol="S_0",
                unit="m/m",
                value=0.00034,
                status=HydraulicParameterStatus.DERIVED,
                provenance="Regional elevation difference (~280 m MSL at HKB to ~205 m MSL at ORB over 220 km)",
                spatial_applicability="Upper-to-Middle Yamuna Reach",
                temporal_applicability="Static regional topographic gradient",
                uncertainty_description=(
                    "Bed slope is non-uniform: steeper in gravel-bed upstream section near Yamunanagar "
                    "(S_0 > 0.001) and flattens to alluvial silt-sand bed near Delhi (S_0 ~ 0.0002). "
                    "Uniform slope assumption introduces localized velocity bias."
                ),
            ),
            HydraulicParameter(
                name="Channel Cross-Sections & Bathymetry",
                symbol="A(y), B(y)",
                unit="m, m²",
                value=None,
                status=HydraulicParameterStatus.UNAVAILABLE,
                provenance="Restricted across CWC, Haryana I&WRD, Delhi I&FC, and UYRB",
                spatial_applicability="220 km corridor",
                temporal_applicability="Dynamic seasonal post-monsoon bed siltation / aggradation",
                uncertainty_description=(
                    "No bathymetric surveys, cross-sectional soundings, or LiDAR DTMs exist in the repository. "
                    "Yamuna riverbed width varies from ~300 m at bridges to 1.5–3.0 km across unembanked plains. "
                    "Severe blocker for 1D/2D hydrodynamic modelling."
                ),
            ),
            HydraulicParameter(
                name="Manning's Roughness Coefficient",
                symbol="n",
                unit="s/m^(1/3)",
                value=None,
                status=HydraulicParameterStatus.UNAVAILABLE,
                provenance="Unmeasured / uncalibrated along the corridor",
                spatial_applicability="Main channel and overbank floodplain",
                temporal_applicability="Seasonal weed growth and stage-dependent inundation",
                uncertainty_description=(
                    "Literature ranges suggest 0.030–0.040 for low-flow sandy bed, "
                    "increasing to 0.050–0.085 for obstructed floodplains. "
                    "Without calibration against water surface profiles, selecting a single value is arbitrary."
                ),
            ),
            HydraulicParameter(
                name="Reach Floodplain Storage Characteristic",
                symbol="S(Q, y)",
                unit="m³",
                value=None,
                status=HydraulicParameterStatus.UNAVAILABLE,
                provenance="Requires calibrated digital elevation model and surveyed bund geometries",
                spatial_applicability="Floodplain zones across Yamunanagar, Karnal, Panipat, Sonipat",
                temporal_applicability="Active only during overbank discharge (Q > 2,000–3,000 m³/s)",
                uncertainty_description=(
                    "Unquantified storage volume attenuation. Major flood peaks breach or spill over "
                    "marginal agricultural bunds, attenuating flood waves non-linearly."
                ),
            ),
            HydraulicParameter(
                name="Upstream Regulated River Release",
                symbol="Q_in(t)",
                unit="m³/s",
                value=None,  # Dynamic time series
                status=HydraulicParameterStatus.MEASURED,
                provenance="Haryana I&WRD daily barrage observation records (HKB D/S, 2018–2025)",
                spatial_applicability="Hathnikund Barrage downstream release point",
                temporal_applicability="Daily observations (06:00/08:00 IST morning gauge)",
                uncertainty_description=(
                    "100% complete daily record (2,599 days). Daily aggregation smooths sub-daily flash flood peaks. "
                    "Accurate boundary condition for daily volume discharge."
                ),
            ),
            HydraulicParameter(
                name="Intermediate Tributaries & Lateral Inflows",
                symbol="q_lat(t)",
                unit="m³/s",
                value=None,
                status=HydraulicParameterStatus.UNAVAILABLE,
                provenance="Unmetered tributaries (Som, Pathrala, Boli) and agricultural return drains",
                spatial_applicability="Confluence points between Yamunanagar and Sonipat",
                temporal_applicability="Event-driven flash contributions",
                uncertainty_description=(
                    "Som and Pathrala can contribute sudden flash peaks (>500–1,000 m³/s) into Yamuna "
                    "downstream of Hathnikund. Currently omitted due to absence of telemetry."
                ),
            ),
            HydraulicParameter(
                name="Intermediate Barrage Operations & Regulators",
                symbol="Gate_status",
                unit="categorical",
                value=None,
                status=HydraulicParameterStatus.UNAVAILABLE,
                provenance="Wazirabad Barrage (Delhi Jal Board) and ITO Barrage (Delhi I&FC / Haryana)",
                spatial_applicability="Wazirabad (km ~210) and ITO (km ~225)",
                temporal_applicability="Operational during monsoon flood gates operation",
                uncertainty_description=(
                    "Backwater pondage and sluice gate jamming (as in July 2023 at ITO Barrage) "
                    "heavily alter downstream stage-discharge relationships at Delhi ORB."
                ),
            ),
            HydraulicParameter(
                name="Downstream Calibration Stage / Discharge",
                symbol="h_out(t), Q_out(t)",
                unit="m MSL, m³/s",
                value=None,
                status=HydraulicParameterStatus.UNAVAILABLE,
                provenance="CWC Station 028-MDD (Delhi Old Railway Bridge) continuous telemetry",
                spatial_applicability="Delhi Old Railway Bridge (28.6625°N, 77.2489°E)",
                temporal_applicability="Continuous hourly / daily",
                uncertainty_description=(
                    "Continuous non-flood water levels are restricted under CWC transboundary policies. "
                    "Without continuous downstream observations, routing model calibration is IMPOSSIBLE."
                ),
            ),
        ]


@dataclass
class MuskingumParameters:
    """
    Parameter container and validation logic for classical Muskingum storage routing.
    Governing equation: S = K * [x * I + (1 - x) * O]
    """
    K_hours: float
    x: float
    dt_hours: float = 24.0
    subreaches: int = 1

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        """
        Validate physical ranges and numerical stability conditions.
        Raises ValueError with specific diagnostic message upon violation.
        """
        if self.K_hours <= 0:
            raise ValueError(f"Muskingum travel time parameter K must be positive, got {self.K_hours} hours.")
        if not (0.0 <= self.x <= 0.5):
            raise ValueError(f"Muskingum weighting parameter x must be in [0.0, 0.5], got {self.x}.")
        if self.dt_hours <= 0:
            raise ValueError(f"Routing time step dt must be positive, got {self.dt_hours} hours.")
        if self.subreaches < 1:
            raise ValueError(f"Number of sub-reaches must be >= 1, got {self.subreaches}.")

        # Check numerical stability for each sub-reach
        k_reach = self.K_hours / self.subreaches
        lower_bound = 2.0 * k_reach * self.x
        upper_bound = 2.0 * k_reach * (1.0 - self.x)

        # Allow small epsilon tolerance for floating-point boundaries
        eps = 1e-6
        if self.dt_hours < lower_bound - eps:
            raise ValueError(
                f"Numerical instability: dt ({self.dt_hours} h) < 2*K*x ({lower_bound:.2f} h). "
                f"This produces a negative routing coefficient C0, causing spurious oscillatory outflow dips. "
                f"Increase dt, decrease x, or increase subreaches (m)."
            )
        if self.dt_hours > upper_bound + eps:
            raise ValueError(
                f"Numerical instability: dt ({self.dt_hours} h) > 2*K*(1-x) ({upper_bound:.2f} h). "
                f"This produces a negative routing coefficient C2, causing severe numerical dispersion. "
                f"Decrease dt, decrease subreaches, or adjust K."
            )

    def compute_coefficients(self) -> Tuple[float, float, float]:
        """
        Compute Muskingum routing coefficients (C0, C1, C2) for a single reach (or sub-reach).
        C0 = (dt - 2Kx) / (2K(1-x) + dt)
        C1 = (dt + 2Kx) / (2K(1-x) + dt)
        C2 = (2K(1-x) - dt) / (2K(1-x) + dt)
        Guaranteed by construction: C0 + C1 + C2 == 1.0.
        """
        k_reach = self.K_hours / self.subreaches
        denominator = 2.0 * k_reach * (1.0 - self.x) + self.dt_hours
        c0 = (self.dt_hours - 2.0 * k_reach * self.x) / denominator
        c1 = (self.dt_hours + 2.0 * k_reach * self.x) / denominator
        c2 = (2.0 * k_reach * (1.0 - self.x) - self.dt_hours) / denominator
        return c0, c1, c2


@dataclass(frozen=True)
class DocumentedParameterConfig:
    """Documented Muskingum parameter configuration with explicit provenance and calibration status."""
    config_id: str
    name: str
    K_hours: float
    x: float
    dt_hours: float
    subreaches: int
    is_authoritative_baseline: bool
    provenance: str
    calibration_status: str
    numerical_characteristics: str
    discrepancy_explanation: str

    def to_dict(self) -> Dict[str, Any]:
        params = MuskingumParameters(
            K_hours=self.K_hours,
            x=self.x,
            dt_hours=self.dt_hours,
            subreaches=self.subreaches,
        )
        c0, c1, c2 = params.compute_coefficients()
        return {
            "config_id": self.config_id,
            "name": self.name,
            "K_hours": self.K_hours,
            "x": self.x,
            "dt_hours": self.dt_hours,
            "subreaches": self.subreaches,
            "is_authoritative_baseline": self.is_authoritative_baseline,
            "provenance": self.provenance,
            "calibration_status": self.calibration_status,
            "numerical_characteristics": self.numerical_characteristics,
            "discrepancy_explanation": self.discrepancy_explanation,
            "coefficients": {
                "C0": round(c0, 6),
                "C1": round(c1, 6),
                "C2": round(c2, 6),
                "sum": round(c0 + c1 + c2, 6),
            },
            "stability_bounds": {
                "lower_bound_2Kx_hours": round(2.0 * (self.K_hours / self.subreaches) * self.x, 2),
                "time_step_dt_hours": self.dt_hours,
                "upper_bound_2K_1_minus_x_hours": round(2.0 * (self.K_hours / self.subreaches) * (1.0 - self.x), 2),
                "is_strictly_stable": bool(2.0 * (self.K_hours / self.subreaches) * self.x <= self.dt_hours <= 2.0 * (self.K_hours / self.subreaches) * (1.0 - self.x)),
            },
        }


DOCUMENTED_ROUTING_CONFIGS: Dict[str, DocumentedParameterConfig] = {
    "AUTHORITATIVE_BASELINE": DocumentedParameterConfig(
        config_id="AUTHORITATIVE_BASELINE",
        name="Authoritative Baseline Prototype (Phase 1F Codebase)",
        K_hours=36.0,
        x=0.20,
        dt_hours=24.0,
        subreaches=1,
        is_authoritative_baseline=True,
        provenance="Engineering estimate: 220 km corridor / ~6 km/h mean flood-wave celerity (~36.7 h); x=0.20 for natural sand-bed alluvial channel.",
        calibration_status="UNCALIBRATED (assumed literature heuristic; not fitted to Delhi stage/discharge).",
        numerical_characteristics="Strictly stable (2Kx = 14.4h < dt = 24.0h < 2K(1-x) = 57.6h). C0=0.1176, C1=0.4706, C2=0.4118 (all > 0).",
        discrepancy_explanation=(
            "Implemented as default in Phase 1F codebase (MuskingumRouter.create). "
            "Provides balanced forward and backward weighting without setting C0 to 0."
        ),
    ),
    "ALTERNATIVE_UPPER_BOUND_HEURISTIC": DocumentedParameterConfig(
        config_id="ALTERNATIVE_UPPER_BOUND_HEURISTIC",
        name="Alternative Upper-Bound Wave Transit Heuristic (Phase 2C-A Narrative)",
        K_hours=48.0,
        x=0.25,
        dt_hours=24.0,
        subreaches=1,
        is_authoritative_baseline=False,
        provenance="Reported in Phase 2C-A narrative text as typical CWC flood bulletin heuristic (48h transit lag for moderate flows).",
        calibration_status="UNCALIBRATED (assumed literature heuristic; not fitted to Delhi stage/discharge).",
        numerical_characteristics="Boundary stable (2Kx = 24.0h == dt = 24.0h <= 2K(1-x) = 72.0h). C0=0.0000, C1=0.5000, C2=0.5000.",
        discrepancy_explanation=(
            "Referenced in Phase 2C-A text as a 48h travel time assumption. "
            "For dt=24h, 2Kx = 24h, which forces C0 to exactly zero. Any x > 0.25 or K > 48h causes C0 < 0 (instability). "
            "Kept as an alternative scenario configuration for parameter sensitivity testing."
        ),
    ),
}

