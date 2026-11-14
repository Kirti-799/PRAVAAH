"""
ml/tests/test_routing_tabletop.py

Unit and invariant test suite for PRAVAAH Tabletop Scenario Simulation Engine.
Verifies mathematical correctness, numerical stability constraints, physical invariants
(constant inflow conservation, pulse attenuation, lag), input rejection, and reproducibility.
"""

import math
import pytest
from ml.routing.parameters import (
    MuskingumParameters,
    DOCUMENTED_ROUTING_CONFIGS,
    ReachHydraulicCatalog,
    HydraulicParameterStatus,
)
from ml.routing.tabletop_scenario import (
    TabletopScenarioSimulator,
    TabletopSimulationResult,
    get_default_tabletop_presets,
    ScenarioPresetType,
)


# ==============================================================================
# 1. Muskingum Numerical Correctness & Invariants
# ==============================================================================

def test_muskingum_coefficients_sum_to_unity():
    """Verify that C0 + C1 + C2 strictly equals 1.0 across diverse stable parameter sets."""
    test_cases = [
        (36.0, 0.20, 24.0, 1),
        (48.0, 0.25, 24.0, 1),
        (24.0, 0.15, 6.0, 2),
        (72.0, 0.10, 24.0, 2),
    ]
    for K, x, dt, sub in test_cases:
        p = MuskingumParameters(K_hours=K, x=x, dt_hours=dt, subreaches=sub)
        c0, c1, c2 = p.compute_coefficients()
        assert math.isclose(c0 + c1 + c2, 1.0, rel_tol=1e-9), f"Failed sum for K={K}, x={x}, dt={dt}"


def test_parameter_discrepancy_audit():
    """
    Verify the two documented parameter configurations:
    1. Authoritative Baseline (Phase 1F): K=36h, x=0.20, dt=24h -> strictly stable, C0 > 0.
    2. Alternative Heuristic (Phase 2C-A): K=48h, x=0.25, dt=24h -> boundary stable, C0 == 0.
    """
    base = DOCUMENTED_ROUTING_CONFIGS["AUTHORITATIVE_BASELINE"]
    assert base.K_hours == 36.0
    assert base.x == 0.20
    assert base.is_authoritative_baseline is True
    assert "UNCALIBRATED" in base.calibration_status

    base_p = MuskingumParameters(K_hours=base.K_hours, x=base.x, dt_hours=base.dt_hours)
    c0, c1, c2 = base_p.compute_coefficients()
    assert c0 > 0.0  # C0 approx 0.1176
    assert c1 > 0.0
    assert c2 > 0.0

    alt = DOCUMENTED_ROUTING_CONFIGS["ALTERNATIVE_UPPER_BOUND_HEURISTIC"]
    assert alt.K_hours == 48.0
    assert alt.x == 0.25
    assert alt.is_authoritative_baseline is False
    assert "UNCALIBRATED" in alt.calibration_status

    alt_p = MuskingumParameters(K_hours=alt.K_hours, x=alt.x, dt_hours=alt.dt_hours)
    alt_c0, alt_c1, alt_c2 = alt_p.compute_coefficients()
    assert math.isclose(alt_c0, 0.0, abs_tol=1e-7)  # dt == 2Kx -> C0 == 0.0
    assert math.isclose(alt_c1, 0.5, abs_tol=1e-7)
    assert math.isclose(alt_c2, 0.5, abs_tol=1e-7)


def test_constant_inflow_preserves_steady_state():
    """
    Physical invariant: Under continuous constant inflow (e.g. 1,000 m³/s),
    routed outflow must remain exactly constant (1,000 m³/s).
    Peak attenuation must be 0.0 m³/s (0%), and mass error < 1e-4%.
    """
    inflows = [1000.0] * 8
    res = TabletopScenarioSimulator.simulate(
        scenario_id="TEST_CONSTANT",
        scenario_name="Constant Inflow Test",
        inflow_hydrograph=inflows,
        K_hours=36.0,
        x=0.20,
        dt_hours=24.0,
    )

    for pt in res.time_series:
        assert math.isclose(pt["simulated_outflow_cumecs"], 1000.0, rel_tol=1e-4)

    assert math.isclose(res.peak_attenuation_cumecs, 0.0, abs_tol=1e-4)
    assert math.isclose(res.peak_attenuation_percent, 0.0, abs_tol=1e-4)
    assert res.mass_conservation_error_percent < 0.001


def test_pulse_inflow_attenuation_and_lag():
    """
    Physical invariant: A singular extreme pulse must experience attenuation
    and the output peak must lag the input peak.
    """
    # 400 -> 600 -> 6500 -> 1800 -> 800 -> 500 -> 400
    inflows = [400.0, 600.0, 6500.0, 1800.0, 800.0, 500.0, 400.0]
    res = TabletopScenarioSimulator.simulate(
        scenario_id="TEST_PULSE",
        scenario_name="Pulse Test",
        inflow_hydrograph=inflows,
        K_hours=36.0,
        x=0.20,
        dt_hours=24.0,
    )

    assert res.peak_inflow_discharge_cumecs == 6500.0
    assert res.peak_simulated_outflow_discharge_cumecs < 6500.0
    assert res.peak_attenuation_cumecs > 1500.0  # Significant attenuation
    assert res.peak_attenuation_percent > 20.0
    assert res.apparent_lag_hours >= 24.0  # At least 1 step lag
    assert res.mass_conservation_error_percent < 0.01


def test_gradual_rising_inflow_mass_conservation():
    """Verify gradual rise and fall satisfies mass conservation."""
    inflows = [500.0, 900.0, 2200.0, 4500.0, 3100.0, 1800.0, 950.0, 500.0]
    res = TabletopScenarioSimulator.simulate(
        scenario_id="TEST_RISING",
        scenario_name="Rising Wave Test",
        inflow_hydrograph=inflows,
        K_hours=36.0,
        x=0.20,
        dt_hours=24.0,
    )

    assert res.peak_inflow_discharge_cumecs == 4500.0
    assert res.peak_simulated_outflow_discharge_cumecs < 4500.0
    assert res.apparent_lag_hours >= 24.0
    assert res.mass_conservation_error_percent < 0.01


# ==============================================================================
# 2. Input Rejection & Stability Guards
# ==============================================================================

def test_rejects_negative_inflow():
    """Reject any negative inflow values."""
    with pytest.raises(ValueError, match="violates physical non-negativity"):
        TabletopScenarioSimulator.simulate(
            scenario_id="TEST_NEG",
            scenario_name="Negative Test",
            inflow_hydrograph=[500.0, -100.0, 600.0],
        )


def test_rejects_non_finite_inflow():
    """Reject NaN or Inf in inflow hydrograph."""
    with pytest.raises(ValueError, match="non-finite"):
        TabletopScenarioSimulator.simulate(
            scenario_id="TEST_NAN",
            scenario_name="NaN Test",
            inflow_hydrograph=[500.0, float("nan"), 600.0],
        )

    with pytest.raises(ValueError, match="non-finite"):
        TabletopScenarioSimulator.simulate(
            scenario_id="TEST_INF",
            scenario_name="Inf Test",
            inflow_hydrograph=[500.0, float("inf"), 600.0],
        )


def test_rejects_single_point_or_empty_hydrograph():
    """Hydrograph must contain at least 2 points."""
    with pytest.raises(ValueError, match="at least 2 time points"):
        TabletopScenarioSimulator.simulate(
            scenario_id="TEST_SINGLE",
            scenario_name="Single Point Test",
            inflow_hydrograph=[500.0],
        )

    with pytest.raises(ValueError, match="at least 2 time points"):
        TabletopScenarioSimulator.simulate(
            scenario_id="TEST_EMPTY",
            scenario_name="Empty Test",
            inflow_hydrograph=[],
        )


def test_rejects_unstable_parameters():
    """Reject dt < 2Kx or dt > 2K(1-x)."""
    # K=72, x=0.3 -> 2Kx = 43.2h. If dt=24h -> 24 < 43.2 (unstable)
    with pytest.raises(ValueError, match="Numerical instability: dt .* < 2\\*K\\*x"):
        TabletopScenarioSimulator.simulate(
            scenario_id="TEST_UNSTABLE",
            scenario_name="Unstable Test",
            inflow_hydrograph=[500.0, 1000.0, 800.0],
            K_hours=72.0,
            x=0.30,
            dt_hours=24.0,
        )


# ==============================================================================
# 3. Determinism, Reproducibility & Safety Disclaimers
# ==============================================================================

def test_scenario_reproducibility():
    """Identical inputs must yield identical numerical results and reproducibility hash."""
    inflow = [500.0, 1200.0, 3500.0, 2000.0, 700.0]
    res1 = TabletopScenarioSimulator.simulate(
        scenario_id="SCENARIO_REPEAT",
        scenario_name="Repeat Test",
        inflow_hydrograph=inflow,
        K_hours=36.0,
        x=0.20,
    )
    res2 = TabletopScenarioSimulator.simulate(
        scenario_id="SCENARIO_REPEAT",
        scenario_name="Repeat Test",
        inflow_hydrograph=inflow,
        K_hours=36.0,
        x=0.20,
    )

    assert res1.reproducibility_hash == res2.reproducibility_hash
    assert res1.peak_simulated_outflow_discharge_cumecs == res2.peak_simulated_outflow_discharge_cumecs
    assert res1.peak_attenuation_percent == res2.peak_attenuation_percent
    assert res1.total_outflow_volume_m3 == res2.total_outflow_volume_m3


def test_tabletop_presets_availability():
    """Verify standard tabletop presets are properly structured and valid."""
    presets = get_default_tabletop_presets()
    assert "PRESET_CONSTANT" in presets
    assert "PRESET_GRADUAL_RISE" in presets
    assert "PRESET_FLASH_PULSE" in presets
    assert "PRESET_SUSTAINED_HIGH" in presets

    for p in presets.values():
        assert len(p.inflow_hydrograph) >= 5
        assert p.recommended_K_hours > 0
        assert 0.0 <= p.recommended_x <= 0.5


def test_scientific_disclaimer_and_no_delhi_stage():
    """Verify that all output points strictly contain observed_downstream_stage_m = None."""
    inflows = [500.0, 1000.0, 700.0]
    res = TabletopScenarioSimulator.simulate(
        scenario_id="TEST_DISCLAIMER",
        scenario_name="Disclaimer Test",
        inflow_hydrograph=inflows,
    )

    for pt in res.time_series:
        assert pt["observed_downstream_stage_m"] is None

    assert "UNCALIBRATED" in res.scientific_disclaimer
    assert any("NOT OBSERVED DELHI WATER LEVEL" in c or "NEVER observed water levels" in c for c in res.scientific_caveats)
