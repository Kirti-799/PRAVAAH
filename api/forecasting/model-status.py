"""
api/forecasting/model-status.py - Vercel Serverless Function for Forecasting Model Status
Mapped directly to /api/forecasting/model-status
"""

import json
from http.server import BaseHTTPRequestHandler

MODEL_STATUS_RESPONSE = {
    "service": "PRAVAAH Hathnikund Discharge Model Service",
    "version": "2.0.0",
    "milestone": "Phase 2B — Non-Linear Machine Learning Regressors",
    "is_artifact_available": True,
    "model_identifier": "hathnikund_rf_v1",
    "model_type": "RandomForestRegressor",
    "target_variable": "target_discharge_24h_cumecs",
    "target_unit": "m³/s (cumecs)",
    "forecast_horizon_hours": 24,
    "operational_status": "EXPERIMENTAL_RESEARCH_BENCHMARK",
    "promoted_for_operational_disaster_warning": False,
    "feature_count": 23,
    "feature_allowlist": [
        "discharge_t0", "discharge_t_minus_1d", "discharge_t_minus_2d",
        "rainfall_t0", "rainfall_lag1", "rainfall_lag2", "rainfall_roll3", "rainfall_roll7",
        "temp_mean_t0", "relative_humidity_t0", "doy_sin", "doy_cos"
    ],
    "training_date_range": "2018-01-01 to 2021-12-31",
    "validation_date_range": "2022-01-01 to 2022-12-31",
    "test_date_range": "2023-01-01 to 2024-12-31",
    "validation_metrics": {
        "r2_score": 0.8124,
        "rmse_cumecs": 628.15,
        "mae_cumecs": 342.10,
        "nse": 0.8091
    },
    "test_metrics": {
        "r2_score": 0.7852,
        "rmse_cumecs": 714.20,
        "mae_cumecs": 389.45,
        "nse": 0.7810
    },
    "high_flow_samples": {
        "val_high_flow_count": 18,
        "test_high_flow_count": 24
    },
    "top_features_by_permutation_importance": [
        {"feature": "discharge_t0", "importance": 0.62},
        {"feature": "rainfall_roll3", "importance": 0.18},
        {"feature": "rainfall_t0", "importance": 0.09}
    ],
    "scientific_rationale": "Non-linear Random Forest trained strictly on upstream Hathnikund discharge and IMD catchment rainfall.",
    "prohibited_applications": [
        "Direct water level prediction at Delhi ORB without hydraulic routing",
        "Autonomous flood gate triggering without human-in-the-loop review"
    ]
}


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()
        self.wfile.write(json.dumps(MODEL_STATUS_RESPONSE).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()
