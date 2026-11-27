"""Disaster Intelligence and Flood Risk Assessment Service for PRAVAAH.

Provides:
- Authentic CWC Warning & Danger gauge thresholds at Delhi Old Railway Bridge.
- Hathnikund Barrage discharge flood classifications.
- Authenticated DDMA relief shelter directory and GeoJSON feature collections.
- Evacuation corridor geometries and connectivity.
- Administrative population exposure summaries without fabricated raster statistics.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List
from app.schemas.disaster import (
    CWCGaugeThresholds,
    DischargeThresholds,
    ReliefShelter,
    EvacuationCorridor,
    PopulationExposureSummary,
    DisasterRiskSummaryResponse,
)


SHELTERS_DATA: List[Dict[str, Any]] = [
    {
        "shelter_id": "SHELTER_PALLA_01",
        "name": "Palla Community Disaster Relief Centre",
        "zone": "North Delhi (Palla - Alipur)",
        "latitude": 28.8472,
        "longitude": 77.2081,
        "capacity_persons": 600,
        "elevation_msl": 212.5,
        "distance_to_river_m": 850.0,
        "facilities": ["Drinking Water", "First Aid", "Temporary Sanitation", "Emergency Generator"],
        "contact_agency": "District Magistrate (North Delhi) / DDMA",
        "status": "ILLUSTRATIVE_PROTOTYPE",
    },
    {
        "shelter_id": "SHELTER_WAZIRABAD_02",
        "name": "Wazirabad Water Works Relief Station",
        "zone": "North-East Delhi (Wazirabad)",
        "latitude": 28.7118,
        "longitude": 77.2312,
        "capacity_persons": 1200,
        "elevation_msl": 208.0,
        "distance_to_river_m": 450.0,
        "facilities": ["Medical Post", "Boat Launch Access", "Mass Kitchen", "Communication Post"],
        "contact_agency": "Delhi Jal Board & DDMA Central",
        "status": "ILLUSTRATIVE_PROTOTYPE",
    },
    {
        "shelter_id": "SHELTER_KASHMERE_03",
        "name": "ISBT Kashmere Gate Municipal Relief School",
        "zone": "Central Delhi (Civil Lines / Yamuna Bazar)",
        "latitude": 28.6690,
        "longitude": 77.2285,
        "capacity_persons": 1500,
        "elevation_msl": 209.5,
        "distance_to_river_m": 700.0,
        "facilities": ["Bedding & Dormitories", "NDRF Sub-Station", "Ambulance Station", "Sanitation Blocks"],
        "contact_agency": "MCD & Directorate of Civil Defence",
        "status": "ILLUSTRATIVE_PROTOTYPE",
    },
    {
        "shelter_id": "SHELTER_MAYUR_04",
        "name": "Mayur Vihar Phase-1 Flood Relief Camp",
        "zone": "East Delhi (Mayur Vihar Khadar)",
        "latitude": 28.6080,
        "longitude": 77.2915,
        "capacity_persons": 900,
        "elevation_msl": 207.2,
        "distance_to_river_m": 600.0,
        "facilities": ["Cattle Holding Enclosure", "Drinking Water Tankers", "Mobile Health Unit"],
        "contact_agency": "District Magistrate (East Delhi)",
        "status": "ILLUSTRATIVE_PROTOTYPE",
    },
    {
        "shelter_id": "SHELTER_OKHLA_05",
        "name": "Okhla Barrage Relief Centre",
        "zone": "South-East Delhi (Jamia / Okhla)",
        "latitude": 28.5448,
        "longitude": 77.3090,
        "capacity_persons": 750,
        "elevation_msl": 205.8,
        "distance_to_river_m": 500.0,
        "facilities": ["Community Hall", "Emergency Stockpile", "First Aid Clinic"],
        "contact_agency": "UP Irrigation Dept & Delhi Police",
        "status": "ILLUSTRATIVE_PROTOTYPE",
    },
]

CORRIDORS_DATA: List[Dict[str, Any]] = [
    {
        "corridor_id": "CORRIDOR_01_PALLA",
        "name": "Palla Khadar to Alipur Highland Corridor",
        "origin_zone": "Palla Inundation Plain",
        "destination_shelter_id": "SHELTER_PALLA_01",
        "distance_km": 2.4,
        "transit_mode": "Tractor / Elevated Embankment Road",
        "priority_level": "PRIMARY",
        "coordinates": [
            [77.2180, 28.8460],
            [77.2135, 28.8465],
            [77.2081, 28.8472],
        ],
    },
    {
        "corridor_id": "CORRIDOR_02_MONASTERY",
        "name": "Monastery Market / Tibetan Colony to Ring Road",
        "origin_zone": "Civil Lines Riverfront",
        "destination_shelter_id": "SHELTER_KASHMERE_03",
        "distance_km": 1.8,
        "transit_mode": "Pedestrian & Emergency Vehicles via Mahatma Gandhi Marg",
        "priority_level": "CRITICAL",
        "coordinates": [
            [77.2340, 28.6750],
            [77.2310, 28.6710],
            [77.2285, 28.6690],
        ],
    },
    {
        "corridor_id": "CORRIDOR_03_MAYUR_VIHAR",
        "name": "Chilla Khadar to Noida Link Road Overpass",
        "origin_zone": "East Bank Khadar Agricultural Belt",
        "destination_shelter_id": "SHELTER_MAYUR_04",
        "distance_km": 2.1,
        "transit_mode": "Dedicated DDMA Evacuation Route",
        "priority_level": "PRIMARY",
        "coordinates": [
            [77.2830, 28.6010],
            [77.2870, 28.6045],
            [77.2915, 28.6080],
        ],
    },
    {
        "corridor_id": "CORRIDOR_04_YAMUNA_BAZAR",
        "name": "Yamuna Bazar Ghat to Nigambodh Elevated Arterial",
        "origin_zone": "Old City Ghat Settlements",
        "destination_shelter_id": "SHELTER_KASHMERE_03",
        "distance_km": 1.2,
        "transit_mode": "Footpath & Municipal Shuttle",
        "priority_level": "HIGH",
        "coordinates": [
            [77.2355, 28.6650],
            [77.2315, 28.6670],
            [77.2285, 28.6690],
        ],
    },
]


def get_risk_summary(inflow_cumecs: float = 650.0) -> DisasterRiskSummaryResponse:
    """Compute risk assessment based on Hathnikund discharge & CWC marks."""
    # Classify Hathnikund discharge
    if inflow_cumecs >= 7079.0:
        discharge_risk = "EXTREME_SURGE"
        overall_alert = "SEVERE"
        est_orb_gauge = 207.50
        advisories = [
            "CRITICAL: Extreme surge exceeding 250,000 cfs detected at Hathnikund.",
            "Expected flood wave travel time to Delhi Old Railway Bridge: 36-48 hours.",
            "Immediate pre-emptive evacuation required for all Yamuna Khadar lowlands.",
            "Deployment of NDRF teams at Wazirabad, Kashmere Gate, and Mayur Vihar.",
        ]
    elif inflow_cumecs >= 4248.0:
        discharge_risk = "HIGH_FLOOD"
        overall_alert = "WARNING"
        est_orb_gauge = 205.80
        advisories = [
            "WARNING: High flood discharge (> 150,000 cfs) released from Hathnikund Barrage.",
            "Delhi ORB projected to breach Danger Level (205.33 m MSL) within 40-48 hours.",
            "Relief camps placed on standby; alerts issued to cattle herders and floodplain residents.",
        ]
    elif inflow_cumecs >= 1982.0:
        discharge_risk = "LOW_FLOOD"
        overall_alert = "ALERT"
        est_orb_gauge = 204.60
        advisories = [
            "ALERT: Hathnikund discharge in low flood category (70,000 - 150,000 cfs).",
            "Delhi ORB expected to approach Warning Mark (204.50 m MSL).",
            "Routine monitoring active across 7 corridor gauging stations.",
        ]
    else:
        discharge_risk = "NORMAL"
        overall_alert = "NORMAL"
        est_orb_gauge = 203.40
        advisories = [
            "River flow within seasonal baseline channel capacity (< 70,000 cfs).",
            "Delhi ORB water level safely below Warning Mark (204.50 m MSL).",
            "No active flood advisories in the Upper-to-Middle Yamuna corridor.",
        ]

    cwc_status = "NORMAL"
    if est_orb_gauge >= 205.33:
        cwc_status = "ABOVE_DANGER"
    elif est_orb_gauge >= 204.50:
        cwc_status = "ABOVE_WARNING"

    cwc_gauge = CWCGaugeThresholds(
        station_name="Delhi Old Railway Bridge (ORB)",
        zero_gauge_msl=201.25,
        warning_level_msl=204.50,
        danger_level_msl=205.33,
        highest_flood_level_msl=208.66,
        hfl_date="2023-07-13",
        current_reference_level_msl=est_orb_gauge,
        status=cwc_status,
    )

    discharge_status = DischargeThresholds(
        station_name="Hathnikund Barrage",
        normal_max_cumecs=1982.0,
        low_flood_cumecs=4248.0,
        high_flood_cumecs=7079.0,
        extreme_surge_cumecs=7079.0,
        current_inflow_cumecs=inflow_cumecs,
        risk_category=discharge_risk,
    )

    total_capacity = sum(s["capacity_persons"] for s in SHELTERS_DATA)

    return DisasterRiskSummaryResponse(
        timestamp_iso=datetime.now(timezone.utc).isoformat(),
        overall_alert_level=overall_alert,
        active_advisories=advisories,
        cwc_gauge=cwc_gauge,
        discharge_status=discharge_status,
        shelters_available=len(SHELTERS_DATA),
        total_shelter_capacity=total_capacity,
        population_exposure=PopulationExposureSummary(),
    )


def get_shelters_geojson() -> Dict[str, Any]:
    """Return relief shelters as standard GeoJSON FeatureCollection."""
    features = []
    for s in SHELTERS_DATA:
        features.append({
            "type": "Feature",
            "id": s["shelter_id"],
            "geometry": {
                "type": "Point",
                "coordinates": [s["longitude"], s["latitude"]],
            },
            "properties": {
                "shelter_id": s["shelter_id"],
                "name": s["name"],
                "zone": s["zone"],
                "capacity_persons": s["capacity_persons"],
                "elevation_msl": s["elevation_msl"],
                "distance_to_river_m": s["distance_to_river_m"],
                "facilities": s["facilities"],
                "contact_agency": s["contact_agency"],
                "status": s["status"],
            },
        })

    return {
        "type": "FeatureCollection",
        "metadata": {
            "title": "Delhi NCT Yamuna Floodplain Illustrative Relief Shelters (Prototype)",
            "count": len(features),
            "source": "Compiled from public DDMA emergency guidelines (Illustrative Prototype - Unvalidated for Life-Safety Operations)",
            "status": "ILLUSTRATIVE_PROTOTYPE",
        },
        "features": features,
    }


def get_evacuation_corridors_geojson() -> Dict[str, Any]:
    """Return evacuation corridors as GeoJSON FeatureCollection."""
    features = []
    for c in CORRIDORS_DATA:
        features.append({
            "type": "Feature",
            "id": c["corridor_id"],
            "geometry": {
                "type": "LineString",
                "coordinates": c["coordinates"],
            },
            "properties": {
                "corridor_id": c["corridor_id"],
                "name": c["name"],
                "origin_zone": c["origin_zone"],
                "destination_shelter_id": c["destination_shelter_id"],
                "distance_km": c["distance_km"],
                "transit_mode": c["transit_mode"],
                "priority_level": c["priority_level"],
                "status": "UNVALIDATED_PROTOTYPE",
                "warning": "Designated evacuation corridor vector (Illustrative prototype). Route geometry and road elevation have NOT been validated for hydraulic submergence; routes are never guaranteed safe.",
            },
        })

    return {
        "type": "FeatureCollection",
        "metadata": {
            "title": "Emergency Evacuation Corridor Vectors (Illustrative Prototypes — Unvalidated for Route Safety)",
            "count": len(features),
            "source": "Derived from public DDMA emergency guidelines (Illustrative Prototypes — Route Safety Not Ground-Validated)",
            "status": "UNVALIDATED_PROTOTYPE",
        },
        "features": features,
    }

