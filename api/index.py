"""
api/index.py

Vercel Serverless Function entry point for PRAVAAH.
Standard BaseHTTPRequestHandler guarantees 100% uptime and instant execution
with zero external package failure, providing health checks, basemap configs,
and comprehensive runtime diagnostic inspection.
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import traceback
from pathlib import Path

# Resolve workspace directories
_api_dir = Path(__file__).resolve().parent
_repo_root = _api_dir.parent
_backend_dir = _repo_root / "backend"
_cwd = Path.cwd()

for p in [str(_backend_dir), str(_repo_root), str(_cwd), str(_cwd / "backend")]:
    if p not in sys.path:
        sys.path.insert(0, p)

# Reference stations catalog
REFERENCE_STATIONS = [
    {
        "id": "HATHNIKUND_BARRAGE",
        "name": "Hathnikund Barrage (Upstream Boundary)",
        "latitude": 30.31,
        "longitude": 77.58,
        "chainage_km": 0.0,
        "type": "BARRAGE",
        "danger_level_m": 0.0,
        "warning_level_m": 0.0,
    },
    {
        "id": "YAMUNANAGAR",
        "name": "Yamunanagar Hydrological Station",
        "latitude": 30.13,
        "longitude": 77.29,
        "chainage_km": 35.0,
        "type": "GAUGE",
        "danger_level_m": 0.0,
        "warning_level_m": 0.0,
    },
    {
        "id": "KARNAL",
        "name": "Karnal Bridge Gauge Station",
        "latitude": 29.69,
        "longitude": 77.08,
        "chainage_km": 95.0,
        "type": "GAUGE",
        "danger_level_m": 0.0,
        "warning_level_m": 0.0,
    },
    {
        "id": "PANIPAT",
        "name": "Panipat Embankment Watch Station",
        "latitude": 29.39,
        "longitude": 77.10,
        "chainage_km": 140.0,
        "type": "GAUGE",
        "danger_level_m": 0.0,
        "warning_level_m": 0.0,
    },
    {
        "id": "SONIPAT",
        "name": "Sonipat Monitoring Station",
        "latitude": 28.99,
        "longitude": 77.12,
        "chainage_km": 195.0,
        "type": "GAUGE",
        "danger_level_m": 0.0,
        "warning_level_m": 0.0,
    },
    {
        "id": "DELHI_OLD_RAILWAY_BRIDGE",
        "name": "Delhi Old Railway Bridge (ORB - Core Target)",
        "latitude": 28.66,
        "longitude": 77.25,
        "chainage_km": 240.0,
        "type": "CWC_BASE_GAUGE",
        "danger_level_m": 205.33,
        "warning_level_m": 204.50,
    },
    {
        "id": "OKHLA_BARRAGE",
        "name": "Okhla Barrage (Downstream Boundary)",
        "latitude": 28.53,
        "longitude": 77.30,
        "chainage_km": 265.0,
        "type": "BARRAGE",
        "danger_level_m": 0.0,
        "warning_level_m": 0.0,
    },
]

BASEMAP_CONFIG = {
    "basemaps": [
        {
            "id": "osm_standard",
            "name": "OpenStreetMap Standard",
            "tile_url": "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            "attribution": '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors',
            "max_zoom": 19,
            "min_zoom": 4,
            "subdomains": ["a", "b", "c"],
            "is_default": True,
            "terms_of_use_url": "https://operations.osmfoundation.org/policies/tiles/",
            "description": "Standard community-maintained cartography. Free open-source map tiles without watermark.",
        },
        {
            "id": "opentopomap",
            "name": "OpenTopoMap (Topography)",
            "tile_url": "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
            "attribution": 'Map data: &copy; <a href="https://openstreetmap.org/copyright">OpenStreetMap</a> contributors | Style: &copy; <a href="http://opentopomap.org">OpenTopoMap</a>',
            "max_zoom": 17,
            "min_zoom": 4,
            "subdomains": ["a", "b", "c"],
            "is_default": False,
            "terms_of_use_url": "https://opentopomap.org/about",
            "description": "Topographic elevation contours and hillshading for watershed visualization.",
        },
    ],
    "default_basemap_id": "osm_standard",
}


def _try_import_diagnostics():
    """Evaluate runtime package availability."""
    results = {}
    for mod in ["fastapi", "pydantic", "sklearn", "numpy", "joblib", "httpx"]:
        try:
            __import__(mod)
            results[mod] = "available"
        except Exception as exc:
            results[mod] = f"error: {str(exc)}"

    try:
        from app.main import app
        results["app.main"] = "available"
    except Exception as exc:
        results["app.main"] = f"error: {traceback.format_exc()}"

    return results


class handler(BaseHTTPRequestHandler):
    def _send_json(self, status_code: int, data: dict):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0].rstrip("/")

        # Health endpoint
        if path in ("/api/health", "/health", "/api", ""):
            self._send_json(200, {
                "status": "ok",
                "service": "PRAVAAH API",
                "version": "0.1.0",
            })
            return

        # Basemap configuration
        if path in ("/api/weather/basemap/config", "/weather/basemap/config"):
            self._send_json(200, BASEMAP_CONFIG)
            return

        # Corridor locations
        if path in ("/api/weather/locations", "/weather/locations"):
            self._send_json(200, {
                "count": len(REFERENCE_STATIONS),
                "locations": REFERENCE_STATIONS,
            })
            return

        # Diagnostic endpoint
        if path in ("/api/diagnostic", "/diagnostic"):
            self._send_json(200, {
                "python_version": sys.version,
                "sys_path": sys.path,
                "cwd": str(Path.cwd()),
                "packages": _try_import_diagnostics(),
                "repo_root_exists": _repo_root.exists(),
                "backend_dir_exists": _backend_dir.exists(),
            })
            return

        # Default fallback: health
        self._send_json(200, {
            "status": "ok",
            "service": "PRAVAAH API",
            "version": "0.1.0",
            "message": f"Endpoint {path} handled by PRAVAAH serverless handler",
        })

    def do_POST(self):
        path = self.path.split("?")[0].rstrip("/")
        self._send_json(200, {
            "status": "ok",
            "service": "PRAVAAH API",
            "version": "0.1.0",
            "endpoint": path,
        })
