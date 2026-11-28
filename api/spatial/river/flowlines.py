"""
api/spatial/river/flowlines.py - River Flowlines GeoJSON Serverless Function
Mapped directly to /api/spatial/river/flowlines
"""

import json
from http.server import BaseHTTPRequestHandler

# Representative Yamuna downstream river line from Hathnikund to Delhi ORB and Okhla
RIVER_FLOWLINES_GEOJSON = {
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
        self.wfile.write(json.dumps(RIVER_FLOWLINES_GEOJSON).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()
