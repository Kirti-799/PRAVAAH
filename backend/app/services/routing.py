"""
backend/app/services/routing.py

Backend Service for PRAVAAH Hydrological Routing Readiness & Simulation.
Provides typed business logic bridging ML routing components with FastAPI endpoints.
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Ensure repository root is in sys.path
_repo_root = Path(__file__).resolve().parents[3]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from ml.routing.readiness import RoutingReadinessEvaluator
from ml.routing.historical_simulation import HistoricalEpisodeRouter
from ml.routing.spatial_routing import SpatialRoutingEngine
from ml.routing.tabletop_scenario import (
    TabletopScenarioSimulator,
    get_default_tabletop_presets,
)
from ml.routing.parameters import DOCUMENTED_ROUTING_CONFIGS
from app.schemas.routing import (
    RoutingReadinessResponse,
    RoutingSimulationResponse,
    ParameterAuditItem,
    MethodFeasibilitySchema,
    RoutingTimeSeriesItem,
    TabletopScenarioRequest,
    TabletopScenarioResponse,
    TabletopTimeSeriesItem,
    TabletopPresetItem,
    DocumentedParameterConfigItem,
    TabletopPresetsResponse,
    SpatialRoutingPoint,
    SpatialRoutingTimeStep,
    SpatialRoutingSimulationResponse,
)


class RoutingService:
    """Service providing read-only hydraulic readiness audits and uncalibrated routing prototypes."""


    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or (_repo_root / "data")
        self.episode_router = HistoricalEpisodeRouter(data_dir=self.data_dir)

    def get_readiness(self) -> RoutingReadinessResponse:
        """Evaluate hydraulic data completeness and routing readiness."""
        report = RoutingReadinessEvaluator.evaluate(has_upstream_discharge=True)
        report_dict = report.to_dict()

        return RoutingReadinessResponse(
            readiness_status=report_dict["readiness_status"],
            summary_verdict=report_dict["summary_verdict"],
            target_gauge_id=report_dict["target_gauge_id"],
            target_gauge_name=report_dict["target_gauge_name"],
            downstream_calibration_available=report_dict["downstream_calibration_available"],
            methods_evaluation=[
                MethodFeasibilitySchema(**m) for m in report_dict["methods_evaluation"]
            ],
            parameters_summary=report_dict["parameters_summary"],
            parameters_detail=[
                ParameterAuditItem(**p) for p in report_dict["parameters_detail"]
            ],
            critical_blockers=report_dict["critical_blockers"],
            scientific_limitations=report_dict["scientific_limitations"],
            next_recommended_actions=report_dict["next_recommended_actions"],
        )

    def simulate_episode(
        self,
        episode_id: str = "EPISODE_2023_08",
        K_hours: float = 36.0,
        x: float = 0.20,
        dt_hours: float = 24.0,
        subreaches: int = 1,
    ) -> RoutingSimulationResponse:
        """
        Execute Muskingum routing simulation for a verified historical episode.
        Validates parameters and returns structured simulation response.
        """
        sim_data = self.episode_router.simulate_episode(
            episode_id=episode_id,
            K_hours=K_hours,
            x=x,
            dt_hours=dt_hours,
            subreaches=subreaches,
        )

        ts_items = [
            RoutingTimeSeriesItem(
                date=pt["date"],
                observed_upstream_inflow_cumecs=pt["observed_upstream_inflow_cumecs"],
                observed_upstream_release_cumecs=pt["observed_upstream_release_cumecs"],
                simulated_downstream_discharge_cumecs=pt["simulated_downstream_discharge_cumecs"],
                observed_downstream_stage_m=None,  # Always None
            )
            for pt in sim_data["time_series"]
        ]

        return RoutingSimulationResponse(
            status="SIMULATION_SUCCESS_UNCALIBRATED_PROTOTYPE",
            routing_method="Hydrological Muskingum Storage Routing",
            episode_id=sim_data["episode_id"],
            episode_name=sim_data["episode_name"],
            reach_name="Yamuna River: Hathnikund Barrage to Delhi Old Railway Bridge",
            reach_length_km=220.0,
            parameters=sim_data["routing_parameters"],
            routing_coefficients=sim_data["routing_coefficients"],
            numerical_stability_verified=True,
            mass_balance_error_percent=round(sim_data["mass_balance_error_percent"], 4),
            observed_hathnikund_peak_inflow_cumecs=round(sim_data["observed_hathnikund_peak_inflow_cumecs"], 2),
            observed_hathnikund_peak_release_cumecs=round(sim_data["observed_hathnikund_peak_release_cumecs"], 2),
            observed_hathnikund_peak_date=sim_data["observed_hathnikund_peak_date"],
            simulated_peak_downstream_discharge_cumecs=round(sim_data["simulated_peak_downstream_discharge_cumecs"], 2),
            simulated_peak_downstream_date=sim_data["simulated_peak_downstream_date"],
            simulated_attenuation_cumecs=round(sim_data["simulated_attenuation_cumecs"], 2),
            simulated_attenuation_percent=round(sim_data["simulated_attenuation_percent"], 2),
            simulated_lag_hours=round(sim_data["simulated_lag_hours"], 1),
            documented_delhi_crest_stage_m=sim_data["documented_delhi_crest_stage_m"],
            documented_delhi_crest_date=sim_data["documented_delhi_crest_date"],
            documented_delhi_breach_status=sim_data["documented_delhi_breach_status"],
            time_series=ts_items,
            scientific_disclaimer=sim_data["scientific_disclaimer"],
            scientific_caveats=sim_data["scientific_caveats"],
        )

    def simulate_episode_spatial(
        self,
        episode_id: str = "EPISODE_2023_08",
        K_hours: float = 36.0,
        x: float = 0.20,
        sampling_interval_km: float = 5.0,
    ) -> SpatialRoutingSimulationResponse:
        """
        Execute Muskingum routing for an episode and map results spatially along the Yamuna river thalweg.
        """
        raw_res = SpatialRoutingEngine.build_spatial_routing_simulation(
            episode_id=episode_id,
            K_hours=K_hours,
            x=x,
            sampling_interval_km=sampling_interval_km,
        )
        return SpatialRoutingSimulationResponse(**raw_res)


    def get_tabletop_presets(self) -> TabletopPresetsResponse:
        """Return pre-configured tabletop scenarios and documented parameter catalog."""
        presets = get_default_tabletop_presets()
        preset_items = [
            TabletopPresetItem(
                preset_id=p.preset_id,
                preset_type=p.preset_type.value,
                name=p.name,
                description=p.description,
                inflow_hydrograph=p.inflow_hydrograph,
                time_labels=p.time_labels,
                time_step_hours=p.time_step_hours,
                recommended_K_hours=p.recommended_K_hours,
                recommended_x=p.recommended_x,
                purpose_and_expected_behavior=p.purpose_and_expected_behavior,
            )
            for p in presets.values()
        ]

        param_items = [
            DocumentedParameterConfigItem(**cfg.to_dict())
            for cfg in DOCUMENTED_ROUTING_CONFIGS.values()
        ]

        return TabletopPresetsResponse(
            presets=preset_items,
            documented_parameters=param_items,
        )

    def simulate_tabletop_scenario(self, req: TabletopScenarioRequest) -> TabletopScenarioResponse:
        """
        Execute Muskingum routing for an arbitrary hypothetical tabletop scenario.
        Strictly enforces physical invariants, numerical stability, and audit metadata.
        """
        result = TabletopScenarioSimulator.simulate(
            scenario_id=req.scenario_id or "SCENARIO_USER_01",
            scenario_name=req.scenario_name or "Tabletop Scenario",
            inflow_hydrograph=req.inflow_hydrograph,
            time_labels=req.time_labels,
            scenario_type=req.scenario_type or "CUSTOM",
            scenario_description=req.scenario_description or "Hypothetical tabletop scenario simulation",
            initial_outflow_cumecs=req.initial_outflow_cumecs,
            K_hours=req.K_hours,
            x=req.x,
            dt_hours=req.dt_hours,
            subreaches=req.subreaches,
            is_hypothetical=True,
            data_provenance="Hypothetical hydrograph input submitted for tabletop sensitivity exercise",
        )

        res_dict = result.to_dict()

        ts_items = [
            TabletopTimeSeriesItem(
                step=pt["step"],
                time_label=pt["time_label"],
                inflow_cumecs=pt["inflow_cumecs"],
                simulated_outflow_cumecs=pt["simulated_outflow_cumecs"],
                observed_downstream_stage_m=None,  # Always None
            )
            for pt in res_dict["time_series"]
        ]

        return TabletopScenarioResponse(
            scenario_id=res_dict["scenario_id"],
            scenario_name=res_dict["scenario_name"],
            scenario_type=res_dict["scenario_type"],
            scenario_description=res_dict["scenario_description"],
            is_hypothetical=res_dict["is_hypothetical"],
            data_provenance=res_dict["data_provenance"],
            time_step_hours=res_dict["time_step_hours"],
            duration_steps=res_dict["duration_steps"],
            duration_hours=res_dict["duration_hours"],
            routing_parameters=res_dict["routing_parameters"],
            routing_coefficients=res_dict["routing_coefficients"],
            numerical_validity_status=res_dict["numerical_validity_status"],
            stability_criteria_met=res_dict["stability_criteria_met"],
            reproducibility_hash=res_dict["reproducibility_hash"],
            timestamp_utc=res_dict["timestamp_utc"],
            model_version=res_dict["model_version"],
            peak_inflow_discharge_cumecs=res_dict["peak_inflow_discharge_cumecs"],
            peak_inflow_step=res_dict["peak_inflow_step"],
            peak_inflow_time_label=res_dict["peak_inflow_time_label"],
            peak_simulated_outflow_discharge_cumecs=res_dict["peak_simulated_outflow_discharge_cumecs"],
            peak_simulated_outflow_step=res_dict["peak_simulated_outflow_step"],
            peak_simulated_outflow_time_label=res_dict["peak_simulated_outflow_time_label"],
            peak_attenuation_cumecs=res_dict["peak_attenuation_cumecs"],
            peak_attenuation_percent=res_dict["peak_attenuation_percent"],
            apparent_lag_hours=res_dict["apparent_lag_hours"],
            apparent_lag_steps=res_dict["apparent_lag_steps"],
            total_inflow_volume_m3=res_dict["total_inflow_volume_m3"],
            total_outflow_volume_m3=res_dict["total_outflow_volume_m3"],
            reach_storage_change_m3=res_dict["reach_storage_change_m3"],
            mass_conservation_error_percent=res_dict["mass_conservation_error_percent"],
            time_series=ts_items,
            scientific_disclaimer=res_dict["scientific_disclaimer"],
            scientific_caveats=res_dict["scientific_caveats"],
        )

