"""
api/spatial/catchment/boundary.py - Catchment Boundary GeoJSON Serverless Function
Mapped directly to /api/spatial/catchment/boundary
"""

import json
from http.server import BaseHTTPRequestHandler

CATCHMENT_BOUNDARY_GEOJSON = {
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
        self.wfile.write(json.dumps(CATCHMENT_BOUNDARY_GEOJSON).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()
