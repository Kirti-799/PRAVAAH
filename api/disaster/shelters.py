"""
api/disaster/shelters.py - Vercel Serverless Function for Designated Relief Shelters
Mapped directly to /api/disaster/shelters
"""

import json
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


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()
        self.wfile.write(json.dumps(SHELTERS_GEOJSON).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()
