"""
api/spatial/catchment/geometry.py & boundary.py - Catchment Boundary GeoJSON Serverless Function
Mapped directly to /api/spatial/catchment/geometry and /api/spatial/catchment/boundary
"""

import json
from pathlib import Path
from http.server import BaseHTTPRequestHandler

_api_dir = Path(__file__).resolve().parent
_repo_root = _api_dir.parent.parent.parent
_geojson_candidates = [
    _repo_root / "frontend" / "public" / "data" / "spatial" / "catchment" / "hathnikund_upstream_catchment.geojson",
    _repo_root / "dist" / "data" / "spatial" / "catchment" / "hathnikund_upstream_catchment.geojson",
    _repo_root / "data" / "processed" / "spatial" / "catchment" / "hathnikund_upstream_catchment.geojson",
]

_CATCHMENT_CACHE = None
for p in _geojson_candidates:
    if p.exists():
        try:
            with open(p, "r", encoding="utf-8") as f:
                _CATCHMENT_CACHE = json.load(f)
            break
        except Exception:
            pass

if not _CATCHMENT_CACHE:
    _CATCHMENT_CACHE = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "basin_name": "Hathnikund Upstream Catchment",
                    "area_km2": 11365.12,
                    "outlet_station": "HATHNIKUND_BARRAGE",
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [77.30, 30.25],
                            [77.60, 30.50],
                            [78.10, 31.00],
                            [78.50, 31.20],
                            [78.60, 30.80],
                            [78.10, 30.40],
                            [77.58, 30.31],
                            [77.30, 30.25],
                        ]
                    ],
                },
            }
        ],
    }


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()
        self.wfile.write(json.dumps(_CATCHMENT_CACHE).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()
