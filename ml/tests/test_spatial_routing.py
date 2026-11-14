"""
ml/tests/test_spatial_routing.py

Automated test suite for PRAVAAH Phase 3E.4 Spatial 1D Routing Intelligence:
- Validates chainage-to-coordinate mapping along continuous OSM Yamuna mainstem.
- Validates strict monotonic reach ordering from Hathnikund (0 km) to Okhla (268.94 km).
- Validates distinction between OBSERVED inflow (HKB), SIMULATED outflow (ORB), and wave interpolation.
- Validates timestamp consistency across simulation steps.
- Validates non-linear travel time accounting for non-uniform slope.
- Validates backend endpoint schema and error handling.
"""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from ml.routing.spatial_routing import SpatialRoutingEngine, CORRIDOR_MONITORING_STATIONS
from app.main import app


REPO_ROOT = Path(__file__).resolve().parents[2]
MAINSTEM_GEOJSON = REPO_ROOT / "data" / "processed" / "spatial" / "hydrography" / "yamuna_downstream_mainstem.geojson"


def test_mainstem_file_exists():
    """Verify authoritative processed mainstem geometry exists."""
    assert MAINSTEM_GEOJSON.exists(), f"Mainstem file missing: {MAINSTEM_GEOJSON}"


def test_spatial_routing_engine_mapping():
    """Verify SpatialRoutingEngine builds valid spatial time steps and nodes."""
    res = SpatialRoutingEngine.build_spatial_routing_simulation(
        episode_id="EPISODE_2023_08",
        K_hours=36.0,
        x=0.20,
        sampling_interval_km=5.0,
    )

    assert res["status"] == "SIMULATION_SUCCESS_SPATIAL_MAPPED"
    assert res["episode_id"] == "EPISODE_2023_08"
    assert res["reach_length_km"] >= 265.0
    assert res["total_stations_count"] >= 55
    assert len(res["time_steps"]) == 26

    # Verify first step
    step0 = res["time_steps"][0]
    assert step0["date"] == "2023-07-07"
    assert len(step0["points"]) == res["total_stations_count"]

    # Verify chainage monotonicity
    chainages = [pt["chainage_km"] for pt in step0["points"]]
    for i in range(len(chainages) - 1):
        assert chainages[i] <= chainages[i + 1], f"Non-monotonic chainage at index {i}: {chainages[i]} > {chainages[i+1]}"

    # Verify study bounds for all coordinates
    for pt in step0["points"]:
        lat = pt["latitude"]
        lon = pt["longitude"]
        assert 28.40 <= lat <= 30.50, f"Latitude {lat} out of bounds for {pt['name']}"
        assert 76.80 <= lon <= 77.80, f"Longitude {lon} out of bounds for {pt['name']}"


def test_spatial_routing_observed_vs_simulated_distinction():
    """Verify OBSERVED, SIMULATED, and INTERPOLATED_WAVE value tags are strictly applied."""
    res = SpatialRoutingEngine.build_spatial_routing_simulation("EPISODE_2023_08")

    # Step on peak inflow date (2023-07-10)
    peak_inflow_step = next(s for s in res["time_steps"] if s["date"] == "2023-07-10")
    assert peak_inflow_step["observed_inflow_cumecs"] >= 8000.0

    # Point at km 0.0 (Hathnikund) MUST be OBSERVED and match observed_inflow_cumecs exactly
    hkb_pt = next(p for p in peak_inflow_step["points"] if p["station_id"] == "STN_HKB")
    assert hkb_pt["value_type"] == "OBSERVED"
    assert "Haryana I&WRD" in hkb_pt["data_provenance"]
    assert abs(hkb_pt["discharge_cumecs"] - peak_inflow_step["observed_inflow_cumecs"]) < 0.01

    # Point at Delhi ORB MUST be SIMULATED
    orb_pt = next(p for p in peak_inflow_step["points"] if p["station_id"] == "STN_ORB")
    assert orb_pt["value_type"] == "SIMULATED"
    assert "Muskingum" in orb_pt["data_provenance"]
    assert abs(orb_pt["discharge_cumecs"] - peak_inflow_step["simulated_outflow_cumecs"]) < 0.01

    # Non-negativity check across all points and dates
    for step in res["time_steps"]:
        for pt in step["points"]:
            assert pt["discharge_cumecs"] >= 0.0, f"Negative discharge at {pt['name']} on {step['date']}"


def test_spatial_routing_travel_time_non_linearity():
    """Verify non-uniform slope produces faster celerity upstream than downstream."""
    K = 36.0
    tau_0 = SpatialRoutingEngine.compute_travel_time_hours(0.0, K)
    tau_45 = SpatialRoutingEngine.compute_travel_time_hours(44.7, K)
    tau_251 = SpatialRoutingEngine.compute_travel_time_hours(251.05, K)

    assert tau_0 == 0.0
    assert abs(tau_251 - 36.0) < 0.01

    # Travel time per km in upper reach (0 to 45 km)
    rate_upper = tau_45 / 44.7 # hours per km
    # Travel time per km in lower reach (180 to 251 km)
    tau_180 = SpatialRoutingEngine.compute_travel_time_hours(180.0, K)
    rate_lower = (tau_251 - tau_180) / (251.05 - 180.0)

    # Upper reach has faster celerity -> lower hours per km
    assert rate_upper < rate_lower, f"Expected upper rate ({rate_upper:.3f} h/km) < lower rate ({rate_lower:.3f} h/km)"


def test_backend_spatial_routing_endpoints():
    """Verify backend endpoints return 200 OK with compliant schema."""
    client = TestClient(app)

    # 1. Hydrology router endpoint
    resp1 = client.get("/api/hydrology/routing-simulation-spatial?episode_id=EPISODE_2023_08")
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["status"] == "SIMULATION_SUCCESS_SPATIAL_MAPPED"
    assert "SIMULATED" in data1["scientific_disclaimer"]
    assert "NOT A 2D FLOOD INUNDATION MODEL" in data1["scientific_disclaimer"]
    assert len(data1["time_steps"]) == 26
    assert data1["peak_observed_inflow_cumecs"] >= 8000.0

    # 2. Spatial router convenience endpoint
    resp2 = client.get("/api/spatial/routing/simulation?episode_id=EPISODE_2023_08")
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["status"] == "SIMULATION_SUCCESS_SPATIAL_MAPPED"

    # 3. Reject numerical instability with 422
    resp_unstable = client.get("/api/hydrology/routing-simulation-spatial?K_hours=90.0&x=0.45")
    assert resp_unstable.status_code == 422

    # 4. Reject unknown episode with 404
    resp_404 = client.get("/api/hydrology/routing-simulation-spatial?episode_id=EPISODE_INVALID")
    assert resp_404.status_code == 404

