"""
backend/app/services/forecasting.py

Backend Service for PRAVAAH Upstream Forecasting (Phase 2A & Phase 2B).
Provides:
1. Upstream dataset readiness and baseline benchmarks (Phase 2A).
2. Random Forest Regressor status, metadata, validation/test metrics (Phase 2B).
3. Validated experimental 24h discharge predictions for Hathnikund Barrage (Phase 2B).

STRICT SCIENTIFIC SAFEGUARDS:
- Downstream Delhi water level prediction is STRICTLY GATED.
- No synthetic observations or unverified real-time claims.
- Returns explicit error states if artifacts are missing.
"""

import csv
import json
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

_repo_root = Path(__file__).resolve().parents[3]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from app.schemas.forecasting import (
    ForecastingReadinessResponse,
    BaselineMetricSummary,
    DischargeModelStatusResponse,
    ExperimentalDischargeForecastRequest,
    ExperimentalDischargeForecastResponse,
    HydrometCouplingStatusResponse,
    LiveCoupledForecastRequest,
    LiveCoupledForecastResponse,
)
from ml.features.dataset_generator import ForecastingDatasetGenerator
from ml.evaluation.run_baseline_evaluation import BaselineEvaluator
from ml.models.inference import (
    HathnikundDischargeInferenceEngine,
    ModelArtifactNotFoundError,
    InvalidFeatureSchemaError,
)
from ml.features.hydromet_adapter import (
    Rolling24hAccumulator,
    HydrometAntecedentCalculator,
    AstronomicalCalendarCalculator,
    DischargeFeatureCalculator,
    HydrometCouplingAuditor,
    HydrometFeatureAdapter,
    FeatureCompatibilityError,
)
from app.services.rainfall_service import rainfall_service



class ForecastingService:
    """Service providing upstream forecasting readiness, model status, and experimental inference."""

    def __init__(self, data_dir: Optional[Path] = None):
        self.root = _repo_root
        self.dataset_csv = self.root / "data" / "processed" / "modelling" / "hathnikund_discharge_forecasting_24h.csv"
        self.metadata_json = self.root / "data" / "processed" / "modelling" / "forecasting_metadata.json"
        self.phase2a_eval_json = self.root / "data" / "processed" / "analysis" / "phase_2a_baseline_evaluation.json"
        self.phase2b_eval_json = self.root / "data" / "processed" / "analysis" / "phase_2b_model_evaluation.json"
        self.model_metadata_json = self.root / "ml" / "models" / "hathnikund_rf_v1_metadata.json"
        self.model_artifact_path = self.root / "ml" / "models" / "hathnikund_rf_v1.joblib"

        self._inference_engine = HathnikundDischargeInferenceEngine(repo_root=self.root)

    def get_readiness(self) -> ForecastingReadinessResponse:
        """Retrieve forecasting dataset readiness and baseline evaluation results (Phase 2A)."""
        if not self.metadata_json.exists():
            generator = ForecastingDatasetGenerator(repo_root=self.root)
            generator.generate()

        if not self.phase2a_eval_json.exists():
            evaluator = BaselineEvaluator(repo_root=self.root)
            evaluator.run()

        with open(self.metadata_json, mode="r", encoding="utf-8") as f:
            meta = json.load(f)

        with open(self.phase2a_eval_json, mode="r", encoding="utf-8") as f:
            eval_data = json.load(f)

        benchmarks: List[BaselineMetricSummary] = []
        for partition in ["VAL", "TEST"]:
            part_evals = eval_data.get("evaluations", {}).get(partition, {})
            for m_name in ["persistence", "linear_regression_ols", "trailing_3d_mean", "seasonal_naive_doy"]:
                if m_name in part_evals:
                    m_dict = part_evals[m_name].get("overall", {})
                    benchmarks.append(
                        BaselineMetricSummary(
                            model_name=m_name,
                            partition=partition,
                            sample_count=m_dict.get("sample_count", 0),
                            mae_cumecs=m_dict.get("mae_cumecs", 0.0),
                            rmse_cumecs=m_dict.get("rmse_cumecs", 0.0),
                            r2_score=m_dict.get("r2_score", 0.0),
                            skill_score_vs_persistence=m_dict.get("skill_score_vs_persistence"),
                        )
                    )

        caveats = [
            "THIS IS AN UPSTREAM DISCHARGE FORECASTING DATASET — NOT A DELHI FLOOD PREDICTION.",
            "Continuous downstream stage observations for CWC Station 028-MDD (Delhi ORB) remain unacquired; stage prediction is STRICTLY GATED.",
            "Target definition: next contiguous calendar day (24h) release at Hathnikund Barrage (HKB D/S).",
            "Precipitation predictors strictly end on date D-1 to ensure zero operational lookahead leakage.",
            "Baselines are preliminary benchmarks (Persistence, Trailing Mean, Seasonal Naive, Linear OLS) and not validated for operational dispatch.",
        ]

        return ForecastingReadinessResponse(
            status="PRELIMINARY_BASELINES_EVALUATED_NOT_VALIDATED_FOR_OPERATIONS",
            dataset_available=True,
            dataset_rows_total=meta["total_generated_rows"],
            valid_target_rows=meta["valid_24h_target_rows"],
            complete_operational_rows=meta["complete_operational_rows"],
            partitions=meta["partition_counts_complete"],
            baseline_benchmarks=benchmarks,
            linear_model_coefficients=eval_data.get("linear_model_coefficients", {}),
            scientific_caveats=caveats,
        )

    def get_model_status(self) -> DischargeModelStatusResponse:
        """Retrieve model status, validation/test metrics, and operational governance (Phase 2B)."""
        if not self.model_metadata_json.exists():
            raise FileNotFoundError(
                f"Model metadata not found at: {self.model_metadata_json}. Please run model training pipeline first."
            )

        with open(self.model_metadata_json, mode="r", encoding="utf-8") as f:
            meta = json.load(f)

        partitions = meta.get("chronological_partitions", {})
        train_range = f"{partitions.get('TRAIN', {}).get('start_date')} to {partitions.get('TRAIN', {}).get('end_date')}"
        val_range = f"{partitions.get('VAL', {}).get('start_date')} to {partitions.get('VAL', {}).get('end_date')}"
        test_range = f"{partitions.get('TEST', {}).get('start_date')} to {partitions.get('TEST', {}).get('end_date')}"

        high_flows = {
            "train_samples_ge_1500": partitions.get("TRAIN", {}).get("high_flow_samples_ge_1500_cumecs", 0),
            "val_samples_ge_1500": partitions.get("VAL", {}).get("high_flow_samples_ge_1500_cumecs", 0),
            "test_samples_ge_1500": partitions.get("TEST", {}).get("high_flow_samples_ge_1500_cumecs", 0),
        }

        perf = meta.get("performance_summary", {})
        rec = meta.get("operational_recommendation", {})

        return DischargeModelStatusResponse(
            is_artifact_available=self.model_artifact_path.exists(),
            model_identifier=meta.get("model_identifier", "hathnikund_rf_v1"),
            model_type=meta.get("model_type", "RandomForestRegressor"),
            target_variable=meta.get("target_variable", "target_discharge_24h_cumecs"),
            target_unit=meta.get("target_unit", "m³/s (cumecs)"),
            forecast_horizon_hours=meta.get("forecast_horizon_hours", 24),
            operational_status=rec.get("promotion_status", "EXPERIMENTAL_RESEARCH_BENCHMARK"),
            promoted_for_operational_disaster_warning=rec.get("promoted_for_operational_disaster_warning", False),
            feature_count=meta.get("feature_count", 23),
            feature_allowlist=meta.get("feature_allowlist", []),
            training_date_range=train_range,
            validation_date_range=val_range,
            test_date_range=test_range,
            validation_metrics=perf.get("validation_2022", {}),
            test_metrics=perf.get("test_2023_2024", {}),
            high_flow_samples=high_flows,
            top_features_by_permutation_importance=meta.get("permutation_importance_validation_top5", []),
            scientific_rationale=rec.get("scientific_rationale", ""),
            prohibited_applications=rec.get("prohibited_applications", []),
        )

    def predict_discharge(
        self, request: ExperimentalDischargeForecastRequest
    ) -> ExperimentalDischargeForecastResponse:
        """Runs validated inference for Hathnikund Barrage downstream release."""
        result = self._inference_engine.predict(request.features)

        return ExperimentalDischargeForecastResponse(
            model_identifier=result["model_identifier"],
            model_type=result["model_type"],
            target_variable=result["target_variable"],
            forecast_lead_time_hours=result["forecast_lead_time_hours"],
            predicted_discharge_cumecs=result["predicted_discharge_cumecs"],
            discharge_unit=result["discharge_unit"],
            prediction_timestamp_utc=result["prediction_timestamp_utc"],
            observation_context="Custom User/API Observation Vector",
            operational_status=result["operational_status"],
            promoted_for_operational_disaster_warning=result["promoted_for_operational_disaster_warning"],
            performance_reference=result["performance_reference"],
            experimental_warning=result["experimental_warning"],
        )

    def get_sample_historical_forecast(self) -> ExperimentalDischargeForecastResponse:
        """
        Executes demonstration forecast using the latest complete historical observation
        from the verified dataset. Clearly labels observation as historical (not live telemetry).
        """
        if not self.dataset_csv.exists():
            raise FileNotFoundError(f"Dataset missing: {self.dataset_csv}")

        latest_complete_row: Optional[Dict[str, Any]] = None
        with open(self.dataset_csv, mode="r", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if r.get("is_complete_operational_row") == "True":
                    latest_complete_row = r

        if not latest_complete_row:
            raise ValueError("No complete operational rows found in dataset")

        feature_allowlist = self._inference_engine.get_metadata().get("feature_allowlist", [])
        features: Dict[str, float] = {}
        for feat in feature_allowlist:
            val_str = latest_complete_row.get(feat, "")
            features[feat] = float(val_str) if val_str != "" else None

        result = self._inference_engine.predict(features)

        obs_date = latest_complete_row.get("date", "Unknown")
        target_date = latest_complete_row.get("target_date", "Unknown")
        actual_target = latest_complete_row.get("target_discharge_24h_cumecs", "N/A")

        obs_context = (
            f"Historical Observation Date: {obs_date} (Target Date: {target_date}). "
            f"Actual Verified Downstream Release: {actual_target} m³/s."
        )

        return ExperimentalDischargeForecastResponse(
            model_identifier=result["model_identifier"],
            model_type=result["model_type"],
            target_variable=result["target_variable"],
            forecast_lead_time_hours=result["forecast_lead_time_hours"],
            predicted_discharge_cumecs=result["predicted_discharge_cumecs"],
            discharge_unit=result["discharge_unit"],
            prediction_timestamp_utc=result["prediction_timestamp_utc"],
            observation_context=obs_context,
            operational_status=result["operational_status"],
            promoted_for_operational_disaster_warning=result["promoted_for_operational_disaster_warning"],
            performance_reference=result["performance_reference"],
            experimental_warning=result["experimental_warning"],
        )

    def get_hydromet_status(self) -> HydrometCouplingStatusResponse:
        """
        Retrieves comprehensive status of hydrometeorological feature coupling (Phase 3E.2).
        Audits temporal alignment, spatial domains, feature compatibility, and telemetry availability.
        """
        audit = HydrometCouplingAuditor.audit_coupling(
            has_live_discharge_telemetry=False,
            has_operator_discharge_inputs=False,
            rainfall_provider_type="NWP_FORECAST_DOWNSCALED",
            spatial_sampling_node_count=20,
        )

        temporal_summary = {
            "imd_reporting_window": "08:30 IST to 08:30 IST accumulation (ending 03:00 UTC)",
            "open_meteo_daily_window": "00:00 to 24:00 IST (midnight to midnight)",
            "phase_shift_hours": 8.5,
            "rolling_24h_reconstruction_method": "Discrete summation of 24 hourly increments [09:00 IST (D-1) to 08:00 IST (D)]",
            "is_aligned_without_hourly_slicing": False,
        }

        spatial_comparison = {
            "training_dataset_footprint": "91 IMD grid cells across [28.0°N–31.0°N, 76.5°E–78.0°E] (Plains + Hills)",
            "live_sampling_footprint": "20 elevational point nodes across Upper Yamuna basin [30.3°N–31.45°N, 77.25°E–78.55°E]",
            "spatial_domain_match": False,
            "orographic_effect": "20-node basin average captures high-relief mountain rainfall; 91-cell IMD box diluted mountain peaks with dry plain cells.",
        }

        compatibility_matrix = [
            {
                "feature": "discharge_current_cumecs",
                "category": "DISCHARGE",
                "training_source": "Haryana I&WRD (08:00 IST gauge)",
                "live_availability": "UNAVAILABLE_LIVE",
                "compatibility": "REQUIRES_OPERATOR_INPUT_OR_HISTORICAL_REPLAY",
                "importance_rank": 1,
            },
            {
                "feature": "inflow_current_cumecs",
                "category": "DISCHARGE",
                "training_source": "Haryana I&WRD (08:00 IST gauge)",
                "live_availability": "UNAVAILABLE_LIVE",
                "compatibility": "REQUIRES_OPERATOR_INPUT_OR_HISTORICAL_REPLAY",
                "importance_rank": 2,
            },
            {
                "feature": "rainfall_mean_d_minus_1_mm",
                "category": "RAINFALL",
                "training_source": "IMD 0.25° Gridded 91-Cell Mean",
                "live_availability": "AVAILABLE_LIVE_VIA_OPEN_METEO",
                "compatibility": "COVARIATE_SHIFT_CAVEAT (20-node mountain mean vs 91-cell regional mean)",
                "importance_rank": 7,
            },
            {
                "feature": "rainfall_accum_3d_prior_mm",
                "category": "RAINFALL",
                "training_source": "3-day unweighted linear sum (IMD)",
                "live_availability": "AVAILABLE_LIVE_VIA_OPEN_METEO",
                "compatibility": "LINEAR_SUM_REQUIRED (Strictly not equal to decayed API-3)",
                "importance_rank": 4,
            },
            {
                "feature": "rainfall_accum_7d_prior_mm",
                "category": "RAINFALL",
                "training_source": "7-day unweighted linear sum (IMD)",
                "live_availability": "AVAILABLE_LIVE_VIA_OPEN_METEO",
                "compatibility": "LINEAR_SUM_REQUIRED (Strictly not equal to decayed API-7)",
                "importance_rank": 6,
            },
            {
                "feature": "rainfall_max_cell_3d_prior_mm",
                "category": "RAINFALL",
                "training_source": "3-day max across 91 grid cells",
                "live_availability": "AVAILABLE_LIVE_VIA_OPEN_METEO",
                "compatibility": "COVARIATE_SHIFT_CAVEAT (Max across 20 nodes vs max across 91 cells)",
                "importance_rank": 3,
            },
            {
                "feature": "day_of_year",
                "category": "CALENDAR",
                "training_source": "Calendar date t",
                "live_availability": "AVAILABLE_DETERMINISTIC",
                "compatibility": "IDENTICAL",
                "importance_rank": 8,
            },
        ]

        return HydrometCouplingStatusResponse(
            service="PRAVAAH Hydrometeorological Coupling Service",
            version="1.0.0",
            milestone="Phase 3E.2 — Hydro-Meteorological Feature Coupling",
            coupling_status=audit["coupling_status"],
            decision_rationale=audit["decision_rationale"],
            has_live_discharge_telemetry=False,
            has_live_meteorological_feed=True,
            rainfall_provider="open_meteo_catchment",
            sampling_nodes_count=20,
            temporal_alignment_summary=temporal_summary,
            spatial_domain_comparison=spatial_comparison,
            feature_compatibility_matrix=compatibility_matrix,
            missing_telemetry_inputs=audit["missing_inputs"],
            covariate_shift_warnings=audit["covariate_shift_warnings"],
            governance_caveats=audit["governance_caveats"],
            promoted_for_operational_disaster_warning=False,
        )

    async def predict_coupled(
        self, request: LiveCoupledForecastRequest
    ) -> LiveCoupledForecastResponse:
        """
        Executes coupled inference leveraging live meteorological feeds and validated hydrometric inputs.
        Explicitly documents and distinguishes historical observations, live meteorological feeds,
        and missing/imputed telemetry.
        """
        adapter = HydrometFeatureAdapter()
        missing_inputs: Dict[str, Any] = {}
        historical_used: Dict[str, Any] = {}
        meteo_used: Dict[str, Any] = {}

        # 1. Discharge Feature Resolution
        if request.current_discharge_cumecs is not None:
            # User / Operator supplied current discharge
            q_curr = float(request.current_discharge_cumecs)
            q_in = float(request.current_inflow_cumecs) if request.current_inflow_cumecs is not None else q_curr
            history = request.discharge_history_cumecs or [q_curr]
            discharge_feats = adapter.discharge_calc.compute_discharge_features(
                discharge_history_cumecs=history,
                inflow_current_cumecs=q_in,
            )
            historical_used["discharge_source"] = "OPERATOR_OR_EXTERNAL_INPUT"
            historical_used["discharge_current_cumecs"] = q_curr
            historical_used["inflow_current_cumecs"] = q_in
            historical_used["history_length_days"] = len(history)
        else:
            # Fall back to latest verified historical complete row
            latest_complete_row: Optional[Dict[str, Any]] = None
            if self.dataset_csv.exists():
                with open(self.dataset_csv, mode="r", encoding="utf-8") as f:
                    for r in csv.DictReader(f):
                        if r.get("is_complete_operational_row") == "True":
                            latest_complete_row = r

            if latest_complete_row is not None:
                discharge_feats = {
                    feat: float(latest_complete_row[feat]) if latest_complete_row.get(feat, "") != "" else None
                    for feat in self._inference_engine.get_metadata().get("feature_allowlist", [])
                    if "discharge" in feat or "inflow" in feat
                }
                historical_used["discharge_source"] = "HISTORICAL_DATASET_LATEST_COMPLETE_ROW"
                historical_used["observation_date"] = latest_complete_row.get("date", "Unknown")
                historical_used["discharge_current_cumecs"] = float(latest_complete_row.get("discharge_current_cumecs", 0.0))
                historical_used["inflow_current_cumecs"] = float(latest_complete_row.get("inflow_current_cumecs", 0.0))
                missing_inputs["live_discharge_telemetry"] = "UNAVAILABLE_LIVE (Substituted latest complete historical record for research demonstration)"
            else:
                discharge_feats = adapter.discharge_calc.compute_discharge_features([])
                missing_inputs["live_discharge_telemetry"] = "UNAVAILABLE_LIVE (Passed to imputer)"

        # 2. Meteorological Feature Resolution
        rainfall_feats: Dict[str, Optional[float]] = {}
        if request.use_live_catchment_rainfall:
            try:
                catchment_summary = await rainfall_service.get_catchment_rainfall_summary()
                # Aggregate from 20 nodes
                nodes = catchment_summary.sample_grid_points
                if nodes:
                    # D-1 daily rainfall across 20 nodes
                    d1_vals = [p.daily_history_mm[0] if p.daily_history_mm else 0.0 for p in nodes]
                    mean_d1 = float(np.mean(d1_vals))
                    max_d1 = float(np.max(d1_vals))

                    # 3-day and 7-day linear sums per node
                    sums_3d = [sum(p.daily_history_mm[:3]) if len(p.daily_history_mm) >= 3 else sum(p.daily_history_mm) for p in nodes]
                    sums_7d = [sum(p.daily_history_mm[:7]) if len(p.daily_history_mm) >= 7 else sum(p.daily_history_mm) for p in nodes]
                    mean_3d = float(np.mean(sums_3d))
                    mean_7d = float(np.mean(sums_7d))
                    max_cell_3d = float(np.max(sums_3d))

                    rainfall_feats = {
                        "rainfall_mean_d_minus_1_mm": round(mean_d1, 2),
                        "rainfall_max_cell_d_minus_1_mm": round(max_d1, 2),
                        "rainfall_accum_3d_prior_mm": round(mean_3d, 2),
                        "rainfall_accum_7d_prior_mm": round(mean_7d, 2),
                        "rainfall_max_cell_3d_prior_mm": round(max_cell_3d, 2),
                    }
                    meteo_used["provider"] = catchment_summary.provider
                    meteo_used["timestamp"] = catchment_summary.timestamp
                    meteo_used["contributing_nodes_count"] = catchment_summary.contributing_points_count
                    meteo_used["spatial_coverage_pct"] = catchment_summary.spatial_coverage_percentage
                    meteo_used["computed_rainfall_features"] = rainfall_feats
                else:
                    rainfall_feats = {
                        "rainfall_mean_d_minus_1_mm": 0.0,
                        "rainfall_max_cell_d_minus_1_mm": 0.0,
                        "rainfall_accum_3d_prior_mm": 0.0,
                        "rainfall_accum_7d_prior_mm": 0.0,
                        "rainfall_max_cell_3d_prior_mm": 0.0,
                    }
                    missing_inputs["live_meteorological_feed"] = "EMPTY_GRID_NODES"
            except Exception as e:
                rainfall_feats = {
                    "rainfall_mean_d_minus_1_mm": None,
                    "rainfall_max_cell_d_minus_1_mm": None,
                    "rainfall_accum_3d_prior_mm": None,
                    "rainfall_accum_7d_prior_mm": None,
                    "rainfall_max_cell_3d_prior_mm": None,
                }
                missing_inputs["live_meteorological_feed"] = f"PROVIDER_CALL_FAILED: {str(e)}"
        else:
            rainfall_feats = {
                "rainfall_mean_d_minus_1_mm": None,
                "rainfall_max_cell_d_minus_1_mm": None,
                "rainfall_accum_3d_prior_mm": None,
                "rainfall_accum_7d_prior_mm": None,
                "rainfall_max_cell_3d_prior_mm": None,
            }

        # Apply manual rainfall overrides if supplied
        if request.custom_rainfall_mean_d_minus_1_mm is not None:
            rainfall_feats["rainfall_mean_d_minus_1_mm"] = float(request.custom_rainfall_mean_d_minus_1_mm)
            meteo_used["custom_rainfall_mean_d_minus_1_mm"] = request.custom_rainfall_mean_d_minus_1_mm
        if request.custom_rainfall_accum_3d_prior_mm is not None:
            rainfall_feats["rainfall_accum_3d_prior_mm"] = float(request.custom_rainfall_accum_3d_prior_mm)
            meteo_used["custom_rainfall_accum_3d_prior_mm"] = request.custom_rainfall_accum_3d_prior_mm
        if request.custom_rainfall_accum_7d_prior_mm is not None:
            rainfall_feats["rainfall_accum_7d_prior_mm"] = float(request.custom_rainfall_accum_7d_prior_mm)
            meteo_used["custom_rainfall_accum_7d_prior_mm"] = request.custom_rainfall_accum_7d_prior_mm
        if request.custom_rainfall_max_cell_3d_prior_mm is not None:
            rainfall_feats["rainfall_max_cell_3d_prior_mm"] = float(request.custom_rainfall_max_cell_3d_prior_mm)
            meteo_used["custom_rainfall_max_cell_3d_prior_mm"] = request.custom_rainfall_max_cell_3d_prior_mm

        # 3. Calendar Features
        calendar_feats = adapter.calendar_calc.compute_calendar_features()

        # 4. Assemble 23-Feature Vector
        assembled_vector, audit_meta = adapter.assemble_feature_vector(
            discharge_features=discharge_feats,
            rainfall_features=rainfall_feats,
            calendar_features=calendar_feats,
        )

        # 5. Run Validated Inference
        pred_result = self._inference_engine.predict(assembled_vector)

        readiness_status = "COUPLED_RESEARCH_BENCHMARK" if not missing_inputs.get("live_discharge_telemetry") else "DEMONSTRATION_HYBRID_COUPLING"

        caveats = [
            "EXPERIMENTAL BENCHMARK ONLY: Evaluated under Phase 2B Decision Gate.",
            "Live discharge telemetry is unavailable in real-time; predictions without verified morning gauge readings are strictly demonstration benchmarks.",
            "Meteorological features from the 20-node high-relief catchment grid exhibit domain shift from the 91-cell regional IMD training set.",
            "Under no circumstances predicts Delhi Old Railway Bridge flood levels or breach probabilities.",
        ]

        warning_str = (
            "EXPERIMENTAL RESEARCH PREDICTION: Generated using coupled meteorological inputs. "
            "This model must NEVER be used as an autonomous flood warning or for emergency evacuation decisions."
        )

        return LiveCoupledForecastResponse(
            model_identifier=pred_result["model_identifier"],
            model_type=pred_result["model_type"],
            target_variable=pred_result["target_variable"],
            forecast_lead_time_hours=24,
            predicted_discharge_cumecs=pred_result["predicted_discharge_cumecs"],
            discharge_unit=pred_result["discharge_unit"],
            prediction_timestamp_utc=pred_result["prediction_timestamp_utc"],
            inference_readiness_status=readiness_status,
            historical_observations_used=historical_used,
            live_meteorological_inputs_used=meteo_used,
            missing_or_imputed_inputs=missing_inputs,
            operational_status="EXPERIMENTAL_RESEARCH_BENCHMARK",
            promoted_for_operational_disaster_warning=False,
            scientific_caveats=caveats,
            experimental_warning=warning_str,
        )

