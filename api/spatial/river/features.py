"""
api/spatial/river/features.py & flowlines.py - River Geometry GeoJSON Serverless Function
Mapped directly to /api/spatial/river/features and /api/spatial/river/flowlines
"""

import json
from pathlib import Path
from http.server import BaseHTTPRequestHandler

_api_dir = Path(__file__).resolve().parent
_repo_root = _api_dir.parent.parent.parent
_geojson_candidates = [
    _repo_root / "frontend" / "public" / "data" / "spatial" / "hydrography" / "yamuna_downstream_mainstem.geojson",
    _repo_root / "dist" / "data" / "spatial" / "hydrography" / "yamuna_downstream_mainstem.geojson",
    _repo_root / "data" / "processed" / "spatial" / "hydrography" / "yamuna_downstream_mainstem.geojson",
]

_RIVER_CACHE = None
for p in _geojson_candidates:
    if p.exists():
        try:
            with open(p, "r", encoding="utf-8") as f:
                _RIVER_CACHE = json.load(f)
            break
        except Exception:
            pass

if not _RIVER_CACHE:
    # Representative fallback line from Hathnikund (30.31, 77.58) to Delhi ORB (28.66, 77.25)
    _RIVER_CACHE = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "river_name": "Yamuna River",
                    "reach": "Hathnikund to Delhi ORB and Okhla",
                    "total_length_km": 268.94,
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [77.5800, 30.3100],
                        [77.3000, 30.1000],
                        [77.1800, 29.8500],
                        [77.1100, 29.1900],
                        [77.2312, 28.8969],
                        [77.2358, 28.6690],
                        [77.2800, 28.5900],
                        [77.3050, 28.5440],
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
        self.wfile.write(json.dumps(_RIVER_CACHE).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()
