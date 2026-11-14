"""
ml/tests/test_routing.py

Automated test suite for PRAVAAH Hydrological Routing Module.
Tests parameter validation, numerical stability criteria, mass conservation,
error handling for missing/negative inputs, readiness diagnostics,
and separation of simulated discharge from unobserved water levels.
"""

import pytest
import math
from ml.routing.parameters import (
    HydraulicParameterStatus,
    ReachHydraulicCatalog,
    MuskingumParameters,
)
from ml.routing.readiness import (
    RoutingReadinessStatus,
    RoutingReadinessEvaluator,
)
from ml.routing.muskingum import (
    MuskingumRouter,
    SimulationTimeSeriesPoint,
    RoutingSimulationResult,
)
from ml.routing.historical_simulation import HistoricalEpisodeRouter


# ==============================================================================
# 1. Parameter Validation & Numerical Stability Tests
# ==============================================================================

def test_muskingum_valid_parameters():
    """Verify standard stable parameters compute valid coefficients summing to 1.0."""
    params = MuskingumParameters(K_hours=36.0, x=0.20, dt_hours=24.0)
    c0, c1, c2 = params.compute_coefficients()

    assert math.isclose(c0 + c1 + c2, 1.0, rel_tol=1e-7)
    assert c0 >= 0.0
    assert c1 >= 0.0
    assert c2 >= 0.0


def test_muskingum_rejects_non_positive_k():
    """Verify K <= 0 is rejected."""
    with pytest.raises(ValueError, match="must be positive"):
        MuskingumParameters(K_hours=0.0, x=0.20, dt_hours=24.0)

    with pytest.raises(ValueError, match="must be positive"):
        MuskingumParameters(K_hours=-10.0, x=0.20, dt_hours=24.0)


def test_muskingum_rejects_out_of_bounds_x():
    """Verify x < 0 or x > 0.5 is rejected."""
    with pytest.raises(ValueError, match=r"\[0.0, 0.5\]"):
        MuskingumParameters(K_hours=36.0, x=-0.05, dt_hours=24.0)

    with pytest.raises(ValueError, match=r"\[0.0, 0.5\]"):
        MuskingumParameters(K_hours=36.0, x=0.55, dt_hours=24.0)


def test_muskingum_rejects_non_positive_dt():
    """Verify dt <= 0 is rejected."""
    with pytest.raises(ValueError, match="must be positive"):
        MuskingumParameters(K_hours=36.0, x=0.20, dt_hours=0.0)


def test_muskingum_numerical_instability_lower_bound():
    """
    Verify instability condition: dt < 2*K*x is rejected.
    Example: K=72h, x=0.3 -> 2*K*x = 43.2h. If dt=24h, 24 < 43.2 -> C0 < 0.
    """
    with pytest.raises(ValueError, match="Numerical instability: dt .* < 2\\*K\\*x"):
        MuskingumParameters(K_hours=72.0, x=0.30, dt_hours=24.0)


def test_muskingum_numerical_instability_upper_bound():
    """
    Verify instability condition: dt > 2*K*(1-x) is rejected.
    Example: K=10h, x=0.2 -> 2*K*(1-x) = 16h. If dt=24h, 24 > 16 -> C2 < 0.
    """
    with pytest.raises(ValueError, match="Numerical instability: dt .* > 2\\*K\\*\\(1-x\\)"):
        MuskingumParameters(K_hours=10.0, x=0.20, dt_hours=24.0)


# ==============================================================================
# 2. Synthetic Routing & Mass Conservation Tests
# ==============================================================================

def test_routing_mass_conservation_synthetic_fixture():
    """
    Route an idealized synthetic hydrograph (clearly labeled synthetic test fixture).
    Verify that mass is strictly conserved (error < 0.05%), peak is attenuated,
    and peak outflow lags peak inflow.
    """
    dates = [f"2025-07-{i:02d}" for i in range(1, 11)]
    # Idealized synthetic triangular hydrograph
    synthetic_inflows = [100.0, 150.0, 400.0, 1200.0, 3000.0, 1800.0, 700.0, 300.0, 150.0, 100.0]

    router = MuskingumRouter.create(K_hours=36.0, x=0.20, dt_hours=24.0)
    result = router.route(dates, synthetic_inflows)

    assert result.status == "SIMULATION_SUCCESS_UNCALIBRATED_PROTOTYPE"
    assert result.numerical_stability_verified is True
    # Mass conservation check
    assert result.mass_balance_error_percent < 0.05
    # Attenuation check: routed peak must be smaller than inflow peak
    assert result.peak_simulated_outflow_cumecs < result.peak_observed_inflow_cumecs
    assert result.simulated_attenuation_percent > 0.0
    # Lag check: peak outflow occurs at or after peak inflow
    assert result.simulated_lag_hours >= 0.0

    # Ensure water level is strictly None across every point
    for pt in result.time_series:
        assert pt.observed_downstream_stage_m is None


def test_multi_reach_routing_attenuation():
    """Verify that multi-reach subdivision preserves mass and produces smooth attenuation."""
    dates = [f"2025-07-{i:02d}" for i in range(1, 9)]
    synthetic_inflows = [100.0, 300.0, 1000.0, 2500.0, 1200.0, 500.0, 200.0, 100.0]

    # K=40h, subreaches=2 -> k_reach=20h. dt=24h.
    # 2*20*0.2 = 8h < 24h < 2*20*0.8 = 32h. Stable!
    router = MuskingumRouter.create(K_hours=40.0, x=0.20, dt_hours=24.0, subreaches=2)
    result = router.route(dates, synthetic_inflows)

    assert result.mass_balance_error_percent < 0.05
    assert result.peak_simulated_outflow_cumecs < 2500.0


# ==============================================================================
# 3. Input Validation & Error Handling Tests
# ==============================================================================

def test_routing_rejects_length_mismatch():
    """Verify mismatch between dates and inflows raises ValueError."""
    router = MuskingumRouter.create(K_hours=36.0, x=0.20)
    with pytest.raises(ValueError, match="Length mismatch"):
        router.route(["2025-07-01", "2025-07-02"], [100.0])


def test_routing_rejects_short_series():
    """Verify time series with fewer than 2 points is rejected."""
    router = MuskingumRouter.create(K_hours=36.0, x=0.20)
    with pytest.raises(ValueError, match="at least 2 points"):
        router.route(["2025-07-01"], [100.0])


def test_routing_rejects_missing_inflows_no_silent_zero():
    """Verify NaN / None is rejected with clear message; no silent zero-filling."""
    router = MuskingumRouter.create(K_hours=36.0, x=0.20)
    with pytest.raises(ValueError, match="Silent zero-filling is strictly prohibited"):
        router.route(["2025-07-01", "2025-07-02", "2025-07-03"], [100.0, float("nan"), 200.0])


def test_routing_rejects_negative_discharge():
    """Verify negative discharge values are rejected as physical violations."""
    router = MuskingumRouter.create(K_hours=36.0, x=0.20)
    with pytest.raises(ValueError, match="Physical violation: negative discharge"):
        router.route(["2025-07-01", "2025-07-02"], [100.0, -50.0])


# ==============================================================================
# 4. Routing Readiness & Hydraulic Catalog Tests
# ==============================================================================

def test_reach_hydraulic_catalog_audit():
    """Verify reach catalog enumerates all key parameters with valid statuses."""
    catalog = ReachHydraulicCatalog.get_reach_parameters()
    assert len(catalog) >= 8

    statuses = {p.status for p in catalog}
    assert HydraulicParameterStatus.DERIVED in statuses
    assert HydraulicParameterStatus.UNAVAILABLE in statuses
    assert HydraulicParameterStatus.MEASURED in statuses

    # Bathymetry must be explicitly UNAVAILABLE
    bathymetry = next(p for p in catalog if p.symbol == "A(y), B(y)")
    assert bathymetry.status == HydraulicParameterStatus.UNAVAILABLE

    # Downstream target stage must be explicitly UNAVAILABLE
    target_stage = next(p for p in catalog if "028-MDD" in p.provenance)
    assert target_stage.status == HydraulicParameterStatus.UNAVAILABLE


def test_routing_readiness_evaluation():
    """Verify readiness evaluator correctly flags prototype as uncalibrated."""
    report = RoutingReadinessEvaluator.evaluate(has_upstream_discharge=True)

    assert report.readiness_status == RoutingReadinessStatus.ROUTING_PARAMETRIC_PROTOTYPE_UNCALIBRATED
    assert report.downstream_calibration_available is False
    assert len(report.critical_blockers) >= 3

    # Dynamic wave and Muskingum-Cunge must be marked infeasible
    st_venant = next(m for m in report.methods_evaluation if "Dynamic Wave" in m.method_name)
    assert st_venant.is_feasible is False

    cunge = next(m for m in report.methods_evaluation if "Muskingum-Cunge" in m.method_name)
    assert cunge.is_feasible is False

    calibrated_musk = next(m for m in report.methods_evaluation if "Calibrated" in m.method_name)
    assert calibrated_musk.is_feasible is False

    prototype = next(m for m in report.methods_evaluation if "Prototype" in m.method_name)
    assert prototype.is_feasible is True


def test_routing_readiness_missing_upstream():
    """Verify that if upstream discharge is absent, status is ROUTING_NOT_READY."""
    report = RoutingReadinessEvaluator.evaluate(has_upstream_discharge=False)
    assert report.readiness_status == RoutingReadinessStatus.ROUTING_NOT_READY_MISSING_HYDRAULIC_DATA


# ==============================================================================
# 5. Historical Episode Simulation Verification
# ==============================================================================

def test_historical_episode_2023_simulation():
    """
    Verify routing simulation on the historic July 2023 flood episode.
    Checks mass balance, peak dates, and ensures stage remains unestimated.
    """
    router = HistoricalEpisodeRouter()
    sim = router.simulate_episode("EPISODE_2023_08")

    assert sim["episode_id"] == "EPISODE_2023_08"
    assert sim["observed_hathnikund_peak_release_cumecs"] >= 8000.0
    assert sim["simulated_peak_downstream_discharge_cumecs"] > 5000.0
    assert sim["mass_balance_error_percent"] < 0.1
    assert sim["documented_delhi_crest_stage_m"] == 208.66

    # Verify no downstream stage is simulated in time series
    for pt in sim["time_series"]:
        assert pt["observed_downstream_stage_m"] is None
        assert pt["simulated_downstream_discharge_cumecs"] >= 0.0

    assert "SIMULATED DOWNSTREAM DISCHARGE" in sim["scientific_disclaimer"]
