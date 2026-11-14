/**
 * frontend/src/types/weather.ts
 *
 * TypeScript type definitions for external weather and basemap data integration in PRAVAAH.
 */

export interface NormalizedCurrentWeather {
  provider: string;
  latitude: number;
  longitude: number;
  elevation_m?: number | null;
  timezone: string;
  retrieved_at: string;
  is_cached: boolean;
  cache_age_seconds: number;
  temperature_c?: number | null;
  relative_humidity_pct?: number | null;
  precipitation_mm?: number | null;
  wind_speed_kmh?: number | null;
  weather_code?: number | null;
  quality_status: 'VERIFIED' | 'PROVISIONAL' | 'ESTIMATED' | 'UNVALIDATED';
  source_reference: string;
  scientific_disclaimer: string;
}

export interface NormalizedHourlyForecastItem {
  timestamp: string;
  temperature_c?: number | null;
  precipitation_mm: number;
  precipitation_probability_pct?: number | null;
  wind_speed_kmh?: number | null;
  relative_humidity_pct?: number | null;
}

export interface NormalizedWeatherForecast {
  provider: string;
  latitude: number;
  longitude: number;
  elevation_m?: number | null;
  timezone: string;
  retrieved_at: string;
  is_cached: boolean;
  cache_age_seconds: number;
  forecast_days: number;
  hourly_series: NormalizedHourlyForecastItem[];
  source_reference: string;
  scientific_disclaimer: string;
}

export interface ProviderStatus {
  provider_name: string;
  is_available: boolean;
  status_code?: number | null;
  latency_ms?: number | null;
  last_checked: string;
  notes: string[];
}

export interface WeatherLocation {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  chainage_km?: number | null;
  station_type: string;
  warning_level_m?: number | null;
  danger_level_m?: number | null;
}

export interface WeatherLocationsResponse {
  locations: WeatherLocation[];
  corridor_bbox: {
    west: number;
    east: number;
    south: number;
    north: number;
  };
  default_location_id: string;
}

export interface BasemapOption {
  id: string;
  name: string;
  tile_url: string;
  attribution: string;
  max_zoom: number;
  min_zoom: number;
  is_default: boolean;
  terms_of_use_url: string;
  description: string;
}

export interface BasemapCatalogResponse {
  basemaps: BasemapOption[];
  default_basemap_id: string;
  corridor_extent: {
    west: number;
    east: number;
    south: number;
    north: number;
    center: [number, number];
    default_zoom: number;
  };
}

export interface WeatherRefreshResponse {
  status: string;
  message: string;
  current: NormalizedCurrentWeather;
  forecast?: NormalizedWeatherForecast | null;
}
