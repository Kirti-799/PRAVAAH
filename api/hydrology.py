"""
api/hydrology.py - Vercel Serverless Function for Hydrological Intelligence Services
Handles:
- /api/hydrology/summary
- /api/hydrology/events
- /api/hydrology/routing-readiness
"""

import json
from http.server import BaseHTTPRequestHandler

HYDROLOGY_SUMMARY = {
    "service": "PRAVAAH Hydrological Intelligence Service",
    "version": "1.0.0",
    "milestone": "Phase 1E — Scientific Data Validation & Non-ML Hydrological Analysis",
    "latest_observations": {
        "timestamp_utc": "2025-08-12T06:00:00Z",
        "date": "2025-08-12",
        "upstream_station_inflow": "Hathnikund Barrage (HKB U/S)",
        "upstream_station_release": "Hathnikund Barrage (HKB D/S)",
        "inflow_discharge_cumecs": 1263.77,
        "inflow_discharge_cusecs": 44629.7,
        "release_discharge_cumecs": 844.06,
        "release_discharge_cusecs": 29807.7,
        "percentage_change_inflow_24h": 44.57,
        "percentage_change_release_24h": 85.74,
        "latest_rainfall_date": "2024-12-31",
        "latest_rainfall_spatial_mean_mm": 0.0,
        "latest_rainfall_spatial_max_mm": 0.0,
        "target_gauge": {
            "station_id": "028-MDD",
            "station_name": "Delhi Old Railway Bridge",
            "danger_mark_m": 205.33,
            "warning_mark_m": 204.5,
            "highest_flood_level_m": 208.66,
            "observation_status": "DATA_RESTRICTED_PENDING_CWC_REQUISITION",
            "latest_water_level_m": None,
            "status_note": "CWC Station 028-MDD continuous non-flood water-level records are restricted on public open CKAN endpoints under transboundary basin guidelines."
        }
    },
    "rainfall_accumulations": {
        "reference_date": "2024-12-31",
        "accum_1d_mm": 0.0,
        "accum_3d_mm": 5.72,
        "accum_5d_mm": 28.96,
        "accum_7d_mm": 29.15,
        "spatial_coverage_cells": 91,
        "aggregation_method": "unweighted_provisional_bbox_mean"
    },
    "discharge_statistics": {
        "period_start": "2018-01-01",
        "period_end": "2025-08-12",
        "total_days": 2599,
        "inflow_statistics_hkb_us": {
            "count": 2593,
            "mean_cumecs": 265.61,
            "p50_cumecs": 117.3,
            "p90_cumecs": 607.02,
            "p95_cumecs": 843.04,
            "p99_cumecs": 1768.13,
            "max_cumecs": 17623.08
        },
        "release_statistics_hkb_ds": {
            "count": 2599,
            "mean_cumecs": 85.14,
            "p50_cumecs": 9.96,
            "p90_cumecs": 133.47,
            "p95_cumecs": 336.79,
            "p99_cumecs": 1260.0,
            "max_cumecs": 8380.4
        }
    },
    "data_quality": {
        "upstream_missing_days": 7,
        "upstream_duplicate_records": 0,
        "rainfall_missing_days": 0,
        "valid_rainfall_cells_per_day": 91,
        "rainfall_grid_resolution": "0.25 deg x 0.25 deg (~27.5 km)",
        "data_freshness_status": "Historical archives complete (Rainfall 2018-2024; Discharge 2018-2025)."
    }
}


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()
        self.wfile.write(json.dumps(HYDROLOGY_SUMMARY).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()
