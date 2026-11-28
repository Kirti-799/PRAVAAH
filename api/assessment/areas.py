"""
api/assessment/areas.py - Vercel Serverless Function for Supported Areas Catalog
Mapped directly by Vercel file-system routing to /api/assessment/areas
"""

import json
from http.server import BaseHTTPRequestHandler

# Ensure boolean JSON literals are defined in case of raw evaluation
true = True
false = False
null = None

CATALOG_RESPONSE = {
    "rivers": [
        {
            "id": "yamuna",
            "name": "Yamuna River",
            "is_operational": True,
            "status_label": "Operational ML (24h Active)",
            "description": "Hathnikund to Delhi NCT and Okhla Reach (268.9 km operational corridor)",
        },
        {
            "id": "ganga",
            "name": "Ganga River",
            "is_operational": False,
            "status_label": "Planned Expansion Basin",
            "description": "Haridwar and Varanasi reaches — Live weather active; ML model in development",
        },
        {
            "id": "brahmaputra",
            "name": "Brahmaputra River",
            "is_operational": False,
            "status_label": "Planned Expansion Basin",
            "description": "Guwahati gorge reach — Live weather active; ML model in development",
        },
        {
            "id": "godavari",
            "name": "Godavari River",
            "is_operational": False,
            "status_label": "Planned Expansion Basin",
            "description": "Rajahmundry delta reach — Live weather active; ML model in development",
        },
    ],
    "areas": [
        {
            "id": "DELHI_CENTRAL",
            "name": "Delhi NCT Reach (Palla to Old Railway Bridge)",
            "river_id": "yamuna",
            "river_name": "Yamuna River",
            "is_operational": True,
            "area_type": "REACH",
            "coverage_description": "Primary metropolitan reach passing Wazirabad, ISBT Kashmere Gate, and Delhi Old Railway Bridge.",
            "length_km": 31.62,
            "representative_coord": [28.6690, 77.2358],
            "associated_stations": ["DELHI_OLD_RAILWAY_BRIDGE"],
        },
        {
            "id": "ALL_CORRIDOR",
            "name": "Entire Upper-Middle Yamuna Corridor (Hathnikund to Okhla)",
            "river_id": "yamuna",
            "river_name": "Yamuna River",
            "is_operational": True,
            "area_type": "CORRIDOR_ALL",
            "coverage_description": "Complete 268.9 km downstream river mainstem from Hathnikund Barrage to Okhla Barrage.",
            "length_km": 268.94,
            "representative_coord": [29.4500, 77.1500],
            "associated_stations": ["HATHNIKUND_BARRAGE", "DELHI_OLD_RAILWAY_BRIDGE"],
        },
        {
            "id": "UPSTREAM_CATCHMENT",
            "name": "Hathnikund Upstream Catchment Basin",
            "river_id": "yamuna",
            "river_name": "Yamuna River",
            "is_operational": True,
            "area_type": "BASIN",
            "coverage_description": "Contributing mountain catchment draining into Hathnikund Barrage.",
            "area_km2": 11365.12,
            "representative_coord": [30.7500, 77.8000],
            "associated_stations": ["HATHNIKUND_BARRAGE"],
        },
        {
            "id": "UPPER_CORRIDOR",
            "name": "Upper Reach (Hathnikund to Panipat)",
            "river_id": "yamuna",
            "river_name": "Yamuna River",
            "is_operational": True,
            "area_type": "REACH",
            "coverage_description": "Upper alluvial plain through Yamunanagar and Karnal districts.",
            "length_km": 154.81,
            "representative_coord": [29.8500, 77.1800],
            "associated_stations": ["HATHNIKUND_BARRAGE", "YAMUNANAGAR", "KARNAL"],
        },
        {
            "id": "MIDDLE_CORRIDOR",
            "name": "Middle Reach (Panipat to Sonipat)",
            "river_id": "yamuna",
            "river_name": "Yamuna River",
            "is_operational": True,
            "area_type": "REACH",
            "coverage_description": "Agricultural and industrial corridor through Panipat and Sonipat.",
            "length_km": 53.54,
            "representative_coord": [29.1900, 77.1100],
            "associated_stations": ["PANIPAT", "SONIPAT"],
        },
        {
            "id": "NCR_NORTH",
            "name": "NCR North Reach (Sonipat to Palla)",
            "river_id": "yamuna",
            "river_name": "Yamuna River",
            "is_operational": True,
            "area_type": "REACH",
            "coverage_description": "Border transit reach entering Delhi NCT at Palla station.",
            "length_km": 11.08,
            "representative_coord": [28.8969, 77.2312],
            "associated_stations": ["SONIPAT"],
        },
        {
            "id": "LOWER_REACH",
            "name": "Lower Reach (Delhi ORB to Okhla Barrage)",
            "river_id": "yamuna",
            "river_name": "Yamuna River",
            "is_operational": True,
            "area_type": "REACH",
            "coverage_description": "Southern urban corridor passing ITO, Nizamuddin, to Okhla Barrage.",
            "length_km": 17.89,
            "representative_coord": [28.5900, 77.2800],
            "associated_stations": ["DELHI_OLD_RAILWAY_BRIDGE", "OKHLA_BARRAGE"],
        },
        {
            "id": "GANGA_HARIDWAR",
            "name": "Ganga: Haridwar Reach (Upper Plain)",
            "river_id": "ganga",
            "river_name": "Ganga River",
            "is_operational": False,
            "area_type": "REACH",
            "coverage_description": "Haridwar Upper Basin from Bhimgoda Barrage to Roorkee. Live weather available; ML in development.",
            "representative_coord": [29.9457, 78.1642],
            "associated_stations": ["HARIDWAR_BHIMGODA"],
        },
        {
            "id": "GANGA_VARANASI",
            "name": "Ganga: Varanasi Reach (Middle Basin)",
            "river_id": "ganga",
            "river_name": "Ganga River",
            "is_operational": False,
            "area_type": "REACH",
            "coverage_description": "Varanasi metropolitan reach along the ghats. Live weather available; ML in development.",
            "representative_coord": [25.3176, 83.0062],
            "associated_stations": ["VARANASI_GHAT"],
        },
        {
            "id": "BRAHMAPUTRA_GUWAHATI",
            "name": "Brahmaputra: Guwahati Reach",
            "river_id": "brahmaputra",
            "river_name": "Brahmaputra River",
            "is_operational": False,
            "area_type": "REACH",
            "coverage_description": "Guwahati gorge section in Assam. Live weather available; ML in development.",
            "representative_coord": [26.1856, 91.7539],
            "associated_stations": ["GUWAHATI_PANDU"],
        },
        {
            "id": "GODAVARI_RAJAHMUNDRY",
            "name": "Godavari: Rajahmundry Reach",
            "river_id": "godavari",
            "river_name": "Godavari River",
            "is_operational": False,
            "area_type": "REACH",
            "coverage_description": "Lower Godavari delta reach and Dowleswaram Barrage. Live weather available; ML in development.",
            "representative_coord": [17.0005, 81.8040],
            "associated_stations": ["RAJAHMUNDRY_DOWLESWARAM"],
        },
    ],
    "default_river_id": "yamuna",
    "default_area_id": "DELHI_CENTRAL",
    "total_corridor_length_km": 268.94,
    "catchment_area_km2": 11365.12,
}


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()
        self.wfile.write(json.dumps(CATALOG_RESPONSE).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()
