"""
api/disaster.py - Vercel Serverless Function for Disaster & Shelter Services
Handles:
- /api/disaster/shelters
- /api/disaster/risk-summary
- /api/disaster/evacuation-corridors
"""

import json
import urllib.parse
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler

SHELTERS_GEOJSON = {
    "type": "FeatureCollection",
    "metadata": {
        "title": "Delhi NCT Yamuna Floodplain Illustrative Relief Shelters (DDMA Guidelines)",
        "count": 5,
        "source": "Compiled from public DDMA emergency guidelines (Illustrative Prototype)",
        "status": "ILLUSTRATIVE_PROTOTYPE",
    },
    "features": [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [77.2081, 28.8472]},
            "properties": {
                "shelter_id": "SHELTER_PALLA_01",
                "name": "Palla Community Disaster Relief Centre",
                "zone": "North Delhi (Palla - Alipur)",
                "capacity_persons": 600,
                "elevation_msl": 212.5,
                "distance_to_river_m": 850.0,
                "facilities": ["Drinking Water", "First Aid", "Temporary Sanitation", "Emergency Generator"],
                "contact_agency": "District Magistrate (North Delhi) / DDMA",
                "status": "ILLUSTRATIVE_PROTOTYPE",
            },
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [77.2312, 28.7118]},
            "properties": {
                "shelter_id": "SHELTER_WAZIRABAD_02",
                "name": "Wazirabad Water Works Relief Station",
                "zone": "North-East Delhi (Wazirabad)",
                "capacity_persons": 1200,
                "elevation_msl": 208.0,
                "distance_to_river_m": 450.0,
                "facilities": ["Medical Post", "Boat Launch Access", "Mass Kitchen", "Communication Post"],
                "contact_agency": "Delhi Jal Board & DDMA Central",
                "status": "ILLUSTRATIVE_PROTOTYPE",
            },
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [77.2285, 28.6690]},
            "properties": {
                "shelter_id": "SHELTER_KASHMERE_03",
                "name": "ISBT Kashmere Gate Municipal Relief School",
                "zone": "Central Delhi (Civil Lines / Yamuna Bazar)",
                "capacity_persons": 1500,
                "elevation_msl": 209.5,
                "distance_to_river_m": 700.0,
                "facilities": ["Bedding & Dormitories", "NDRF Sub-Station", "Ambulance Station", "Sanitation Blocks"],
                "contact_agency": "MCD & Directorate of Civil Defence",
                "status": "ILLUSTRATIVE_PROTOTYPE",
            },
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [77.2915, 28.6080]},
            "properties": {
                "shelter_id": "SHELTER_MAYUR_04",
                "name": "Mayur Vihar Phase-1 Flood Relief Camp",
                "zone": "East Delhi (Mayur Vihar Khadar)",
                "capacity_persons": 900,
                "elevation_msl": 207.2,
                "distance_to_river_m": 600.0,
                "facilities": ["Community Kitchen", "Water Purification Units", "Child Care Tent", "Relief Supply Depot"],
                "contact_agency": "District Magistrate (East Delhi) / DDMA",
                "status": "ILLUSTRATIVE_PROTOTYPE",
            },
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [77.3050, 28.5440]},
            "properties": {
                "shelter_id": "SHELTER_OKHLA_05",
                "name": "Okhla Barrage Municipal Flood Station",
                "zone": "South-East Delhi (Okhla)",
                "capacity_persons": 800,
                "elevation_msl": 205.8,
                "distance_to_river_m": 350.0,
                "facilities": ["First Aid Centre", "Generator Sets", "Inflatable Rafts Storage", "Food Stockpile"],
                "contact_agency": "UP Irrigation Dept & DDMA South East",
                "status": "ILLUSTRATIVE_PROTOTYPE",
            },
        },
    ],
}


def compute_risk_summary(inflow_cumecs: float) -> dict:
    if inflow_cumecs >= 8000:
        overall_alert = "EXTREME_FLOOD"
        level_m = 208.66
        cwc_status = "EXTREME_FLOOD_CROSSING_ALL_TIME_HFL"
        discharge_status = "RECORD_SURGE"
        advisories = [
            "CRITICAL: River discharge exceeds 8,000 m³/s — surpassing historic July 2023 peak.",
            "Water level at Delhi Old Railway Bridge projected above Record HFL (208.66 m MSL).",
            "Mandatory immediate evacuation ordered for Yamuna floodplains.",
        ]
        exposed_pop = 28500
    elif inflow_cumecs >= 2500:
        overall_alert = "DANGER"
        level_m = 205.80
        cwc_status = "DANGER_LEVEL_EXCEEDED"
        discharge_status = "HIGH_FLOOD"
        advisories = [
            "DANGER: Inflow exceeds High Flood threshold (2,500 m³/s).",
            "Delhi ORB projected to cross Danger Mark (205.33 m MSL).",
            "Low-lying areas along Kashmere Gate and Mayur Vihar Khadar on active alert.",
        ]
        exposed_pop = 14200
    elif inflow_cumecs >= 1980:
        overall_alert = "WARNING"
        level_m = 204.65
        cwc_status = "WARNING_LEVEL_EXCEEDED"
        discharge_status = "SEASONAL_ALERT"
        advisories = [
            "WARNING: River discharge elevated above 1,980 m³/s threshold.",
            "Delhi ORB water level approaching or crossing Warning Mark (204.50 m MSL).",
        ]
        exposed_pop = 3800
    else:
        overall_alert = "NORMAL"
        level_m = 203.20
        cwc_status = "SAFE_BELOW_WARNING"
        discharge_status = "SEASONAL_NORMAL"
        advisories = [
            "River flow within seasonal baseline channel capacity (< 70,000 cfs).",
            "Delhi ORB water level safely below Warning Mark (204.50 m MSL).",
            "No active flood advisories across the corridor.",
        ]
        exposed_pop = 0

    return {
        "timestamp_iso": datetime.now(timezone.utc).isoformat(),
        "overall_alert_level": overall_alert,
        "active_advisories": advisories,
        "cwc_gauge": {
            "station_id": "DELHI_ORB",
            "name": "Delhi Old Railway Bridge (ORB)",
            "warning_level_msl": 204.50,
            "danger_level_msl": 205.33,
            "record_hfl_msl": 208.66,
            "estimated_water_level_msl": level_m,
            "status": cwc_status,
        },
        "discharge_status": {
            "station_id": "HATHNIKUND_BARRAGE",
            "inflow_cumecs": inflow_cumecs,
            "classification": discharge_status,
        },
        "shelters_available": 5,
        "total_shelter_capacity": 5000,
        "population_exposure": {
            "potentially_affected_estimate": exposed_pop,
            "high_risk_zone_name": "Lowlands & Floodplain Khadar",
        },
    }


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if "shelters" in parsed.path:
            response_data = SHELTERS_GEOJSON
        else:
            inflow = float(params.get("inflow_cumecs", [650.0])[0])
            response_data = compute_risk_summary(inflow)

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()
        self.wfile.write(json.dumps(response_data).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()
