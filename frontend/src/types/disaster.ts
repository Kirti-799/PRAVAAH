export interface CWCGaugeThresholds {
  station_name: string;
  zero_gauge_msl: number;
  warning_level_msl: number;
  danger_level_msl: number;
  highest_flood_level_msl: number;
  hfl_date: string;
  current_reference_level_msl: number;
  status: 'NORMAL' | 'ABOVE_WARNING' | 'ABOVE_DANGER';
}

export interface DischargeThresholds {
  station_name: string;
  normal_max_cumecs: number;
  low_flood_cumecs: number;
  high_flood_cumecs: number;
  extreme_surge_cumecs: number;
  current_inflow_cumecs: number;
  risk_category: 'NORMAL' | 'LOW_FLOOD' | 'HIGH_FLOOD' | 'EXTREME_SURGE';
}

export interface ReliefShelter {
  shelter_id: string;
  name: string;
  zone: string;
  latitude: number;
  longitude: number;
  capacity_persons: number;
  elevation_msl: number;
  distance_to_river_m: number;
  facilities: string[];
  contact_agency: string;
  status: string;
}

export interface EvacuationCorridor {
  corridor_id: string;
  name: string;
  origin_zone: string;
  destination_shelter_id: string;
  distance_km: number;
  transit_mode: string;
  priority_level: string;
  coordinates: [number, number][]; // [lon, lat]
}

export interface PopulationExposureSummary {
  source: string;
  methodology: string;
  low_lying_villages_count: number;
  estimated_floodplain_residents: number;
  livestock_count: number;
  high_vulnerability_clusters: string[];
  disclaimer: string;
}

export interface DisasterRiskSummaryResponse {
  timestamp_iso: string;
  overall_alert_level: 'NORMAL' | 'ALERT' | 'WARNING' | 'SEVERE';
  active_advisories: string[];
  cwc_gauge: CWCGaugeThresholds;
  discharge_status: DischargeThresholds;
  shelters_available: number;
  total_shelter_capacity: number;
  population_exposure: PopulationExposureSummary;
}

