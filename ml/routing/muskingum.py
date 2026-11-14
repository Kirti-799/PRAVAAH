"""
ml/routing/muskingum.py

Non-ML Hydrological Muskingum Routing Prototype for PRAVAAH.
Implements classical storage routing for the Hathnikund-to-Delhi reach
with rigorous parameter validation, numerical stability enforcement,
and mass conservation auditing.

MATHEMATICAL FORMULATION:
Governing storage equation:
    S = K * [x * I + (1 - x) * O]

Discrete routing equation:
    O_{t+1} = C0 * I_{t+1} + C1 * I_t + C2 * O_t

Where:
    D = 2 * K * (1 - x) + dt
    C0 = (dt - 2 * K * x) / D
    C1 = (dt + 2 * K * x) / D
    C2 = (2 * K * (1 - x) - dt) / D
    C0 + C1 + C2 = 1.0 (exact mass continuity)

Stability Condition:
    2 * K * x < dt < 2 * K * (1 - x)

SCIENTIFIC INTEGRITY SAFEGUARDS:
- Output is explicitly labeled as SIMULATED DOWNSTREAM DISCHARGE.
- NEVER outputs or estimates downstream water levels (m MSL).
- NEVER fabricates negative labels, flood probabilities, or evacuation decisions.
- Enforces strict input validation: rejects missing values, negative discharges,
  and non-positive time steps.
"""

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from ml.routing.parameters import MuskingumParameters


@dataclass(frozen=True)
class SimulationTimeSeriesPoint:
    """Individual time step of routing simulation."""
    date: str
    observed_inflow_cumecs: float
    simulated_outflow_cumecs: float
    observed_downstream_stage_m: Optional[float] = None  # STRICTLY None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "date": self.date,
            "observed_inflow_cumecs": round(self.observed_inflow_cumecs, 2),
            "simulated_outflow_cumecs": round(self.simulated_outflow_cumecs, 2),
            "observed_downstream_stage_m": self.observed_downstream_stage_m,
        }


@dataclass
class RoutingSimulationResult:
    """Full structured output of the Muskingum routing prototype."""
    status: str
    routing_method: str
    reach_name: str
    reach_length_km: float
    parameters: Dict[str, Any]
    routing_coefficients: Dict[str, float]
    numerical_stability_verified: bool
    mass_balance_error_percent: float
    inflow_volume_m3: float
    outflow_volume_m3: float
    storage_change_m3: float
    peak_observed_inflow_cumecs: float
    peak_observed_inflow_date: str
    peak_simulated_outflow_cumecs: float
    peak_simulated_outflow_date: str
    simulated_attenuation_cumecs: float
    simulated_attenuation_percent: float
    simulated_lag_hours: float
    time_series: List[SimulationTimeSeriesPoint]
    scientific_disclaimer: str
    scientific_caveats: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "routing_method": self.routing_method,
            "reach_name": self.reach_name,
            "reach_length_km": self.reach_length_km,
            "parameters": self.parameters,
            "routing_coefficients": self.routing_coefficients,
            "numerical_stability_verified": self.numerical_stability_verified,
            "mass_balance_error_percent": round(self.mass_balance_error_percent, 4),
            "inflow_volume_m3": round(self.inflow_volume_m3, 2),
            "outflow_volume_m3": round(self.outflow_volume_m3, 2),
            "storage_change_m3": round(self.storage_change_m3, 2),
            "peak_observed_inflow_cumecs": round(self.peak_observed_inflow_cumecs, 2),
            "peak_observed_inflow_date": self.peak_observed_inflow_date,
            "peak_simulated_outflow_cumecs": round(self.peak_simulated_outflow_cumecs, 2),
            "peak_simulated_outflow_date": self.peak_simulated_outflow_date,
            "simulated_attenuation_cumecs": round(self.simulated_attenuation_cumecs, 2),
            "simulated_attenuation_percent": round(self.simulated_attenuation_percent, 2),
            "simulated_lag_hours": round(self.simulated_lag_hours, 1),
            "time_series": [pt.to_dict() for pt in self.time_series],
            "scientific_disclaimer": self.scientific_disclaimer,
            "scientific_caveats": self.scientific_caveats,
        }


class MuskingumRouter:
    """Non-ML Muskingum Routing Engine."""

    def __init__(self, params: MuskingumParameters):
        self.params = params
        self.c0, self.c1, self.c2 = params.compute_coefficients()

    @classmethod
    def create(
        cls,
        K_hours: float = 36.0,
        x: float = 0.20,
        dt_hours: float = 24.0,
        subreaches: int = 1,
    ) -> "MuskingumRouter":
        params = MuskingumParameters(
            K_hours=K_hours,
            x=x,
            dt_hours=dt_hours,
            subreaches=subreaches,
        )
        return cls(params)

    def route_reach(self, inflows: List[float], initial_outflow: Optional[float] = None) -> List[float]:
        """
        Route inflow hydrograph through a single reach (or sub-reach).
        Assumes initial steady state O_0 = I_0 unless initial_outflow is explicitly specified.
        """
        n = len(inflows)
        if n < 2:
            raise ValueError(f"Inflow series must contain at least 2 points for routing, got {n}.")

        outflows = [0.0] * n
        outflows[0] = initial_outflow if initial_outflow is not None else inflows[0]

        for t in range(n - 1):
            next_o = self.c0 * inflows[t + 1] + self.c1 * inflows[t] + self.c2 * outflows[t]
            outflows[t + 1] = next_o

        return outflows

    def route(
        self,
        dates: List[str],
        inflows: List[float],
        initial_outflow: Optional[float] = None,
    ) -> RoutingSimulationResult:
        """
        Execute routing simulation with input validation, multi-reach support,
        and rigorous mass conservation auditing.
        """
        # 1. Input Validation
        if len(dates) != len(inflows):
            raise ValueError(f"Length mismatch: {len(dates)} dates vs {len(inflows)} inflows.")
        if len(inflows) < 2:
            raise ValueError(f"Inflow series must contain at least 2 points, got {len(inflows)}.")

        for i, val in enumerate(inflows):
            if val is None or math.isnan(val):
                raise ValueError(
                    f"Invalid missing inflow value at index {i} (date: {dates[i]}). "
                    f"Silent zero-filling is strictly prohibited."
                )
            if val < 0.0:
                raise ValueError(
                    f"Physical violation: negative discharge ({val} m³/s) at index {i} (date: {dates[i]})."
                )

        # 2. Multi-reach routing
        reach_hydrographs = [list(inflows)]
        current_initial = initial_outflow

        for reach_idx in range(self.params.subreaches):
            current_inflow = reach_hydrographs[-1]
            current_outflow = self.route_reach(current_inflow, initial_outflow=current_initial)
            reach_hydrographs.append(current_outflow)
            current_initial = current_outflow[0]

        final_outflows = reach_hydrographs[-1]

        # 3. Mass-Balance Calculation (Trapezoidal integration)
        dt_seconds = self.params.dt_hours * 3600.0
        n = len(inflows)

        # Trapezoidal volume
        inflow_vol = sum((inflows[t] + inflows[t + 1]) / 2.0 for t in range(n - 1)) * dt_seconds
        outflow_vol = sum((final_outflows[t] + final_outflows[t + 1]) / 2.0 for t in range(n - 1)) * dt_seconds

        # Storage change across all subreaches:
        # For each sub-reach j: dS_j = K_reach * [x * (I_final - I_init) + (1-x) * (O_final - O_init)]
        k_reach_seconds = (self.params.K_hours / self.params.subreaches) * 3600.0
        storage_change = 0.0
        for j in range(self.params.subreaches):
            r_in = reach_hydrographs[j]
            r_out = reach_hydrographs[j + 1]
            ds_j = k_reach_seconds * (
                self.params.x * (r_in[-1] - r_in[0])
                + (1.0 - self.params.x) * (r_out[-1] - r_out[0])
            )
            storage_change += ds_j

        # Mass conservation: Inflow = Outflow + dS
        mass_discrepancy = abs(inflow_vol - (outflow_vol + storage_change))
        mass_balance_error_pct = (mass_discrepancy / inflow_vol * 100.0) if inflow_vol > 0 else 0.0

        # 4. Attenuation and Peak Tracking
        peak_in_idx = max(range(n), key=lambda i: inflows[i])
        peak_in_val = inflows[peak_in_idx]
        peak_in_date = dates[peak_in_idx]

        peak_out_idx = max(range(n), key=lambda i: final_outflows[i])
        peak_out_val = final_outflows[peak_out_idx]
        peak_out_date = dates[peak_out_idx]

        attenuation_cumecs = max(0.0, peak_in_val - peak_out_val)
        attenuation_pct = (attenuation_cumecs / peak_in_val * 100.0) if peak_in_val > 0 else 0.0
        lag_hours = (peak_out_idx - peak_in_idx) * self.params.dt_hours

        # 5. Build structured points
        time_series_points = [
            SimulationTimeSeriesPoint(
                date=dates[i],
                observed_inflow_cumecs=inflows[i],
                simulated_outflow_cumecs=final_outflows[i],
                observed_downstream_stage_m=None,  # Strictly None
            )
            for i in range(n)
        ]

        caveats = [
            "SIMULATED DOWNSTREAM DISCHARGE — NOT OBSERVED DELHI WATER LEVEL.",
            "This calculation is a parameter-dependent sensitivity prototype, NOT an empirically calibrated forecast.",
            "Storage constant K and weighting factor x are based on engineering literature approximations, not local gauge optimization.",
            "Intermediate tributary inflows (Som, Pathrala) and intermediate barrages (Wazirabad, ITO) are not represented.",
            "No conversion from simulated discharge to downstream stage (m MSL) is performed due to absence of an authoritative CWC rating curve.",
        ]

        return RoutingSimulationResult(
            status="SIMULATION_SUCCESS_UNCALIBRATED_PROTOTYPE",
            routing_method="Hydrological Muskingum Storage Routing",
            reach_name="Yamuna River: Hathnikund Barrage to Delhi Old Railway Bridge",
            reach_length_km=220.0,
            parameters={
                "K_hours": self.params.K_hours,
                "x": self.params.x,
                "dt_hours": self.params.dt_hours,
                "subreaches": self.params.subreaches,
            },
            routing_coefficients={
                "C0": round(self.c0, 6),
                "C1": round(self.c1, 6),
                "C2": round(self.c2, 6),
                "sum_coefficients": round(self.c0 + self.c1 + self.c2, 6),
            },
            numerical_stability_verified=True,
            mass_balance_error_percent=mass_balance_error_pct,
            inflow_volume_m3=inflow_vol,
            outflow_volume_m3=outflow_vol,
            storage_change_m3=storage_change,
            peak_observed_inflow_cumecs=peak_in_val,
            peak_observed_inflow_date=peak_in_date,
            peak_simulated_outflow_cumecs=peak_out_val,
            peak_simulated_outflow_date=peak_out_date,
            simulated_attenuation_cumecs=attenuation_cumecs,
            simulated_attenuation_percent=attenuation_pct,
            simulated_lag_hours=lag_hours,
            time_series=time_series_points,
            scientific_disclaimer="SIMULATED DOWNSTREAM DISCHARGE — NOT OBSERVED DELHI WATER LEVEL",
            scientific_caveats=caveats,
        )
