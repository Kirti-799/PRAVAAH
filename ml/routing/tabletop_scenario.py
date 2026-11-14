"""
ml/routing/tabletop_scenario.py

Tabletop Scenario Simulation Engine for PRAVAAH Hydrological Routing.
Allows exploring hypothetical flood-wave scenarios (constant inflow, gradual rise,
sharp pulse, sustained elevated release, and user-defined hydrographs) under
strictly audited mathematical parameters.

SCIENTIFIC INTEGRITY ENFORCEMENT:
- Tabletop scenarios are purely mathematical stress-tests, NOT operational flood forecasts.
- Output discharge is strictly labeled SIMULATED DOWNSTREAM DISCHARGE.
- Delhi water levels (stage in m MSL) and flood inundation are strictly UNAVAILABLE.
- Strictly rejects negative discharge, non-finite values (NaN/Inf), and unstable parameters.
- Re-running with identical inputs and configuration produces identical results (deterministic hash).
"""

import math
import hashlib
import json
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple

from ml.routing.parameters import (
    MuskingumParameters,
    DOCUMENTED_ROUTING_CONFIGS,
    DocumentedParameterConfig,
)
from ml.routing.muskingum import (
    MuskingumRouter,
    SimulationTimeSeriesPoint,
)


class ScenarioPresetType(str, Enum):
    CONSTANT = "CONSTANT"
    GRADUALLY_RISING = "GRADUALLY_RISING"
    PULSE = "PULSE"
    SUSTAINED_ELEVATED = "SUSTAINED_ELEVATED"
    CUSTOM = "CUSTOM"


@dataclass(frozen=True)
class TabletopScenarioPreset:
    """Pre-configured hypothetical scenario definition for tabletop exercises."""
    preset_id: str
    preset_type: ScenarioPresetType
    name: str
    description: str
    inflow_hydrograph: List[float]
    time_labels: List[str]
    time_step_hours: float
    recommended_K_hours: float
    recommended_x: float
    purpose_and_expected_behavior: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "preset_id": self.preset_id,
            "preset_type": self.preset_type.value,
            "name": self.name,
            "description": self.description,
            "inflow_hydrograph": self.inflow_hydrograph,
            "time_labels": self.time_labels,
            "time_step_hours": self.time_step_hours,
            "recommended_K_hours": self.recommended_K_hours,
            "recommended_x": self.recommended_x,
            "purpose_and_expected_behavior": self.purpose_and_expected_behavior,
        }


def get_default_tabletop_presets() -> Dict[str, TabletopScenarioPreset]:
    """Generates standard deterministic scenario presets for tabletop exploration."""
    return {
        "PRESET_CONSTANT": TabletopScenarioPreset(
            preset_id="PRESET_CONSTANT",
            preset_type=ScenarioPresetType.CONSTANT,
            name="Constant Steady Inflow (1,000 m³/s)",
            description="Continuous uniform upstream release of 1,000 m³/s over 7 days (168 h).",
            inflow_hydrograph=[1000.0] * 7,
            time_labels=[f"Day {i+1} (T+{i*24:02d}h)" for i in range(7)],
            time_step_hours=24.0,
            recommended_K_hours=36.0,
            recommended_x=0.20,
            purpose_and_expected_behavior=(
                "Numerical invariant verification: Under constant inflow, the routed outflow "
                "must exactly equal inflow (1,000 m³/s) at all steps. Attenuation must be 0 m³/s (0%), "
                "and mass continuity error must be < 1e-4%."
            ),
        ),
        "PRESET_GRADUAL_RISE": TabletopScenarioPreset(
            preset_id="PRESET_GRADUAL_RISE",
            preset_type=ScenarioPresetType.GRADUALLY_RISING,
            name="Gradually Rising Monsoon Wave (500 to 4,500 m³/s)",
            description="Smooth sinusoidal-style rise from 500 m³/s to 4,500 m³/s peak on Day 4, followed by steady recession over 8 days.",
            inflow_hydrograph=[500.0, 900.0, 2200.0, 4500.0, 3100.0, 1800.0, 950.0, 500.0],
            time_labels=[f"Day {i+1} (T+{i*24:02d}h)" for i in range(8)],
            time_step_hours=24.0,
            recommended_K_hours=36.0,
            recommended_x=0.20,
            purpose_and_expected_behavior=(
                "Smooth wave propagation: Tests moderate wave attenuation (~10–18%) and transit lag (~24–48 h) "
                "typical of sustained upper catchment runoff."
            ),
        ),
        "PRESET_FLASH_PULSE": TabletopScenarioPreset(
            preset_id="PRESET_FLASH_PULSE",
            preset_type=ScenarioPresetType.PULSE,
            name="Short-Duration Inflow Pulse (6,500 m³/s Flash Surge)",
            description="Single-day extreme release pulse mimicking sudden cloudburst opening (500 -> 6,500 -> 900 m³/s).",
            inflow_hydrograph=[400.0, 600.0, 6500.0, 1800.0, 800.0, 500.0, 400.0],
            time_labels=[f"Day {i+1} (T+{i*24:02d}h)" for i in range(7)],
            time_step_hours=24.0,
            recommended_K_hours=36.0,
            recommended_x=0.20,
            purpose_and_expected_behavior=(
                "Dispersion and attenuation stress test: Sharp singular pulses experience pronounced channel storage attenuation "
                "(~25–40% peak reduction) and elongated hydrograph base."
            ),
        ),
        "PRESET_SUSTAINED_HIGH": TabletopScenarioPreset(
            preset_id="PRESET_SUSTAINED_HIGH",
            preset_type=ScenarioPresetType.SUSTAINED_ELEVATED,
            name="Sustained Elevated Inflow Plateau (4,000 m³/s for 3 Days)",
            description="Multi-day high discharge plateau representative of consecutive multi-basin barrage releases.",
            inflow_hydrograph=[600.0, 1500.0, 4000.0, 4200.0, 4000.0, 2200.0, 1100.0, 700.0],
            time_labels=[f"Day {i+1} (T+{i*24:02d}h)" for i in range(8)],
            time_step_hours=24.0,
            recommended_K_hours=36.0,
            recommended_x=0.20,
            purpose_and_expected_behavior=(
                "Storage saturation behavior: Prolonged plateau fills channel storage; outflow peak closely approaches "
                "inflow plateau with diminished percentage attenuation compared to a short pulse."
            ),
        ),
    }


@dataclass
class TabletopSimulationResult:
    """Comprehensive, fully reproducible tabletop scenario simulation result."""
    scenario_id: str
    scenario_name: str
    scenario_type: str
    scenario_description: str
    is_hypothetical: bool
    data_provenance: str
    time_step_hours: float
    duration_steps: int
    duration_hours: float
    routing_parameters: Dict[str, Any]
    routing_coefficients: Dict[str, float]
    numerical_validity_status: str
    stability_criteria_met: bool
    reproducibility_hash: str
    timestamp_utc: str
    model_version: str

    # Quantitative metrics
    peak_inflow_discharge_cumecs: float
    peak_inflow_step: int
    peak_inflow_time_label: str
    peak_simulated_outflow_discharge_cumecs: float
    peak_simulated_outflow_step: int
    peak_simulated_outflow_time_label: str
    peak_attenuation_cumecs: float
    peak_attenuation_percent: float
    apparent_lag_hours: float
    apparent_lag_steps: int

    # Volume & Mass Balance
    total_inflow_volume_m3: float
    total_outflow_volume_m3: float
    reach_storage_change_m3: float
    mass_conservation_error_percent: float

    # Hydrograph Series
    time_series: List[Dict[str, Any]]

    # Explicit Disclaimers and Limitations
    scientific_disclaimer: str
    scientific_caveats: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "scenario_name": self.scenario_name,
            "scenario_type": self.scenario_type,
            "scenario_description": self.scenario_description,
            "is_hypothetical": self.is_hypothetical,
            "data_provenance": self.data_provenance,
            "time_step_hours": self.time_step_hours,
            "duration_steps": self.duration_steps,
            "duration_hours": self.duration_hours,
            "routing_parameters": self.routing_parameters,
            "routing_coefficients": self.routing_coefficients,
            "numerical_validity_status": self.numerical_validity_status,
            "stability_criteria_met": self.stability_criteria_met,
            "reproducibility_hash": self.reproducibility_hash,
            "timestamp_utc": self.timestamp_utc,
            "model_version": self.model_version,
            "peak_inflow_discharge_cumecs": round(self.peak_inflow_discharge_cumecs, 2),
            "peak_inflow_step": self.peak_inflow_step,
            "peak_inflow_time_label": self.peak_inflow_time_label,
            "peak_simulated_outflow_discharge_cumecs": round(self.peak_simulated_outflow_discharge_cumecs, 2),
            "peak_simulated_outflow_step": self.peak_simulated_outflow_step,
            "peak_simulated_outflow_time_label": self.peak_simulated_outflow_time_label,
            "peak_attenuation_cumecs": round(self.peak_attenuation_cumecs, 2),
            "peak_attenuation_percent": round(self.peak_attenuation_percent, 2),
            "apparent_lag_hours": round(self.apparent_lag_hours, 1),
            "apparent_lag_steps": self.apparent_lag_steps,
            "total_inflow_volume_m3": round(self.total_inflow_volume_m3, 2),
            "total_outflow_volume_m3": round(self.total_outflow_volume_m3, 2),
            "reach_storage_change_m3": round(self.reach_storage_change_m3, 2),
            "mass_conservation_error_percent": round(self.mass_conservation_error_percent, 5),
            "time_series": self.time_series,
            "scientific_disclaimer": self.scientific_disclaimer,
            "scientific_caveats": self.scientific_caveats,
        }


class TabletopScenarioSimulator:
    """
    Simulates hypothetical tabletop flood-wave routing scenarios over the
    Hathnikund-to-Delhi corridor with deterministic reproducibility.
    """

    MODEL_VERSION = "PRAVAAH-Muskingum-Tabletop-v2.0"

    @classmethod
    def simulate(
        cls,
        scenario_id: str,
        scenario_name: str,
        inflow_hydrograph: List[float],
        time_labels: Optional[List[str]] = None,
        scenario_type: str = "CUSTOM",
        scenario_description: str = "Hypothetical tabletop routing scenario",
        initial_outflow_cumecs: Optional[float] = None,
        K_hours: float = 36.0,
        x: float = 0.20,
        dt_hours: float = 24.0,
        subreaches: int = 1,
        is_hypothetical: bool = True,
        data_provenance: str = "Hypothetical test hydrograph specified for tabletop sensitivity exploration",
    ) -> TabletopSimulationResult:
        """
        Execute tabletop routing with strict input validation, stability bounds enforcement,
        mass continuity auditing, and cryptographic hash verification.
        """
        # 1. Input Validation
        if not inflow_hydrograph or len(inflow_hydrograph) < 2:
            raise ValueError(
                f"Inflow hydrograph must contain at least 2 time points for routing, got {len(inflow_hydrograph) if inflow_hydrograph else 0}."
            )

        n = len(inflow_hydrograph)

        for i, q in enumerate(inflow_hydrograph):
            if q is None:
                raise ValueError(f"Hydrograph point at index {i} is None. Missing values are strictly rejected.")
            if not isinstance(q, (int, float)):
                raise ValueError(f"Hydrograph point at index {i} is not a valid number: {q}.")
            if math.isnan(q) or math.isinf(q):
                raise ValueError(f"Hydrograph point at index {i} is non-finite ({q}). Non-finite inputs are strictly prohibited.")
            if q < 0.0:
                raise ValueError(f"Hydrograph point at index {i} violates physical non-negativity: {q} m³/s < 0.")

        if initial_outflow_cumecs is not None:
            if math.isnan(initial_outflow_cumecs) or math.isinf(initial_outflow_cumecs) or initial_outflow_cumecs < 0.0:
                raise ValueError(f"Invalid initial outflow value: {initial_outflow_cumecs} m³/s.")

        # Construct or validate time labels
        if time_labels is None or len(time_labels) == 0:
            time_labels = [f"T+{int(i * dt_hours):02d}h" for i in range(n)]
        elif len(time_labels) != n:
            raise ValueError(
                f"Length mismatch: {len(time_labels)} time labels provided for {n} inflow hydrograph points."
            )

        # 2. Parameter Validation and Stability Verification
        # MuskingumParameters.__post_init__ strictly verifies K > 0, 0 <= x <= 0.5, dt > 0, subreaches >= 1,
        # and stability condition 2Kx <= dt <= 2K(1-x).
        params = MuskingumParameters(
            K_hours=K_hours,
            x=x,
            dt_hours=dt_hours,
            subreaches=subreaches,
        )
        c0, c1, c2 = params.compute_coefficients()

        # 3. Multi-reach routing execution
        router = MuskingumRouter(params)
        reach_hydrographs = [list(inflow_hydrograph)]
        current_initial = initial_outflow_cumecs

        for r_idx in range(subreaches):
            current_in = reach_hydrographs[-1]
            current_out = router.route_reach(current_in, initial_outflow=current_initial)
            reach_hydrographs.append(current_out)
            current_initial = current_out[0]

        final_outflows = reach_hydrographs[-1]

        # Check for spurious negative outflows
        min_outflow = min(final_outflows)
        if min_outflow < -1e-5:
            raise ValueError(
                f"Numerical artifact: Routed outflow produced negative discharge ({min_outflow:.3f} m³/s). "
                f"This indicates coefficient C0 is severely negative or input gradient exceeds stability capacity."
            )

        # Clean tiny floating-point zeros (e.g. -0.0 -> 0.0)
        final_outflows = [max(0.0, q) for q in final_outflows]

        # 4. Volume Integration & Mass Conservation (Trapezoidal rule)
        dt_seconds = dt_hours * 3600.0
        inflow_vol_m3 = sum((inflow_hydrograph[t] + inflow_hydrograph[t + 1]) / 2.0 for t in range(n - 1)) * dt_seconds
        outflow_vol_m3 = sum((final_outflows[t] + final_outflows[t + 1]) / 2.0 for t in range(n - 1)) * dt_seconds

        # Storage change across all reaches
        k_reach_sec = (K_hours / subreaches) * 3600.0
        total_storage_change = 0.0
        for j in range(subreaches):
            r_in = reach_hydrographs[j]
            r_out = reach_hydrographs[j + 1]
            ds_j = k_reach_sec * (
                x * (r_in[-1] - r_in[0]) + (1.0 - x) * (r_out[-1] - r_out[0])
            )
            total_storage_change += ds_j

        mass_discrepancy = abs(inflow_vol_m3 - (outflow_vol_m3 + total_storage_change))
        mass_balance_error_pct = (mass_discrepancy / inflow_vol_m3 * 100.0) if inflow_vol_m3 > 0 else 0.0

        # 5. Attenuation and Peak Identification
        peak_in_idx = max(range(n), key=lambda i: inflow_hydrograph[i])
        peak_in_val = inflow_hydrograph[peak_in_idx]
        peak_in_label = time_labels[peak_in_idx]

        peak_out_idx = max(range(n), key=lambda i: final_outflows[i])
        peak_out_val = final_outflows[peak_out_idx]
        peak_out_label = time_labels[peak_out_idx]

        attenuation_cumecs = max(0.0, peak_in_val - peak_out_val)
        attenuation_pct = (attenuation_cumecs / peak_in_val * 100.0) if peak_in_val > 0 else 0.0
        lag_steps = peak_out_idx - peak_in_idx
        lag_hours = lag_steps * dt_hours

        # 6. Structured Time Series Points
        series_points = [
            {
                "step": i,
                "time_label": time_labels[i],
                "inflow_cumecs": round(inflow_hydrograph[i], 2),
                "simulated_outflow_cumecs": round(final_outflows[i], 2),
                "observed_downstream_stage_m": None,  # Strictly None
            }
            for i in range(n)
        ]

        # 7. Reproducibility Hash
        canonical_input = {
            "scenario_id": scenario_id,
            "inflows": [round(q, 4) for q in inflow_hydrograph],
            "dt_hours": dt_hours,
            "K_hours": K_hours,
            "x": x,
            "subreaches": subreaches,
            "initial_outflow": initial_outflow_cumecs,
        }
        repro_hash = hashlib.sha256(json.dumps(canonical_input, sort_keys=True).encode("utf-8")).hexdigest()[:16]

        caveats = [
            "TABLETOP SCENARIO SIMULATION — EXPLORATORY STRESS-TEST ONLY.",
            "Input hydrograph is hypothetical unless explicitly tied to an authenticated historical episode.",
            "Routing parameters (K, x) are uncalibrated literature values; changing them demonstrates parameter sensitivity, NOT river calibration.",
            "Outputs represent simulated discharge (m³/s) at the reach boundary, NEVER observed water levels (m MSL) at Delhi Old Railway Bridge.",
            "Does not represent intermediate tributary inflows (Som, Pathrala) or intermediate barrage operations (Wazirabad, ITO).",
            "This tabletop simulation MUST NOT be used for operational flood warning, evacuation zoning, or infrastructure safety clearance.",
        ]

        disclaimer = (
            "MODE: TABLETOP SCENARIO SIMULATION (UNCALIBRATED). "
            "Simulated outputs are mathematical approximations of reach storage routing and are NOT official flood forecasts."
        )

        return TabletopSimulationResult(
            scenario_id=scenario_id,
            scenario_name=scenario_name,
            scenario_type=scenario_type,
            scenario_description=scenario_description,
            is_hypothetical=is_hypothetical,
            data_provenance=data_provenance,
            time_step_hours=dt_hours,
            duration_steps=n,
            duration_hours=n * dt_hours,
            routing_parameters={
                "K_hours": K_hours,
                "x": x,
                "dt_hours": dt_hours,
                "subreaches": subreaches,
                "is_authoritative_baseline": (K_hours == 36.0 and x == 0.20 and dt_hours == 24.0),
                "is_alternative_heuristic": (K_hours == 48.0 and x == 0.25 and dt_hours == 24.0),
            },
            routing_coefficients={
                "C0": round(c0, 6),
                "C1": round(c1, 6),
                "C2": round(c2, 6),
                "sum": round(c0 + c1 + c2, 6),
            },
            numerical_validity_status="VALID",
            stability_criteria_met=True,
            reproducibility_hash=f"sha256:{repro_hash}",
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            model_version=cls.MODEL_VERSION,
            peak_inflow_discharge_cumecs=peak_in_val,
            peak_inflow_step=peak_in_idx,
            peak_inflow_time_label=peak_in_label,
            peak_simulated_outflow_discharge_cumecs=peak_out_val,
            peak_simulated_outflow_step=peak_out_idx,
            peak_simulated_outflow_time_label=peak_out_label,
            peak_attenuation_cumecs=attenuation_cumecs,
            peak_attenuation_percent=attenuation_pct,
            apparent_lag_hours=lag_hours,
            apparent_lag_steps=lag_steps,
            total_inflow_volume_m3=inflow_vol_m3,
            total_outflow_volume_m3=outflow_vol_m3,
            reach_storage_change_m3=total_storage_change,
            mass_conservation_error_percent=mass_balance_error_pct,
            time_series=series_points,
            scientific_disclaimer=disclaimer,
            scientific_caveats=caveats,
        )
