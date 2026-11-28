"""
api/spatial.py - Vercel Serverless Function for Spatial Data Services
Handles:
- /api/spatial/river/flowlines
- /api/spatial/river/features
- /api/spatial/catchment/geometry
- /api/spatial/catchment/boundary
"""

import json
from pathlib import Path
from http.server import BaseHTTPRequestHandler

# River centerline GeoJSON
RIVER_GEOJSON = {
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

# Catchment basin GeoJSON
CATCHMENT_GEOJSON = {
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
        if "catchment" in self.path:
            payload = CATCHMENT_GEOJSON
        else:
            payload = RIVER_GEOJSON

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()
