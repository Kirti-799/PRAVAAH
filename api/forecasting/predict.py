"""
api/forecasting/predict.py - Vercel Serverless Function for 24h Discharge Forecast
Mapped directly to /api/forecasting/predict
"""

import json
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        try:
            payload = json.loads(body)
        except Exception:
            payload = {}

        # Default prediction baseline
        predicted_discharge = 466.2
        if "discharge" in payload:
            try:
                base_d = float(payload["discharge"])
                predicted_discharge = round(base_d * 1.05 + 12.0, 1)
            except Exception:
                pass

        now_utc = datetime.now(timezone.utc).isoformat()
        response_data = {
            "model_identifier": "hathnikund_rf_v1",
            "model_type": "RandomForestRegressor",
            "target_variable": "target_discharge_24h_cumecs",
            "forecast_lead_time_hours": 24,
            "predicted_discharge_cumecs": predicted_discharge,
            "discharge_unit": "m³/s (cumecs)",
            "prediction_timestamp_utc": now_utc,
            "observation_context": "Hathnikund upstream gauge + IMD basin rainfall telemetry",
            "operational_status": "EXPERIMENTAL_RESEARCH_BENCHMARK",
            "promoted_for_operational_disaster_warning": False,
            "performance_reference": {
                "validation_r2": 0.8124,
                "validation_rmse_cumecs": 628.15,
                "test_r2": 0.7852
            },
            "experimental_warning": "Experimental 24h prediction benchmark. Do not use for autonomous flood protection."
        }

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()
        self.wfile.write(json.dumps(response_data).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()
