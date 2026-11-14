/**
 * frontend/src/services/weather.ts
 *
 * Client API service for interacting with PRAVAAH external weather and basemap endpoints.
 */

import { getApiBaseUrl, ApiError } from './api';
import type {
  NormalizedCurrentWeather,
  NormalizedWeatherForecast,
  ProviderStatus,
  WeatherLocationsResponse,
  BasemapCatalogResponse,
  WeatherRefreshResponse,
} from '../types/weather';

export async function fetchWeatherStatus(): Promise<ProviderStatus> {
  const baseUrl = getApiBaseUrl();
  const endpoint = `${baseUrl}/api/weather/status`;

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 8000);

    const response = await fetch(endpoint, {
      method: 'GET',
      headers: { Accept: 'application/json' },
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorPayload = await response.json().catch(() => ({}));
      throw new ApiError(
        errorPayload.detail || `Provider status failed (HTTP ${response.status})`,
        response.status
      );
    }
    return (await response.json()) as ProviderStatus;
  } catch (err: unknown) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(`Network error checking weather status: ${String(err)}`, 0);
  }
}

export async function fetchCorridorLocations(): Promise<WeatherLocationsResponse> {
  const baseUrl = getApiBaseUrl();
  const endpoint = `${baseUrl}/api/weather/locations`;

  try {
    const response = await fetch(endpoint, {
      method: 'GET',
      headers: { Accept: 'application/json' },
    });
    if (!response.ok) {
      throw new ApiError(`Locations query failed (HTTP ${response.status})`, response.status);
    }
    return (await response.json()) as WeatherLocationsResponse;
  } catch (err: unknown) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(`Network error fetching corridor locations: ${String(err)}`, 0);
  }
}

export async function fetchBasemapConfig(): Promise<BasemapCatalogResponse> {
  const baseUrl = getApiBaseUrl();
  const endpoint = `${baseUrl}/api/weather/basemap/config`;

  try {
    const response = await fetch(endpoint, {
      method: 'GET',
      headers: { Accept: 'application/json' },
    });
    if (!response.ok) {
      throw new ApiError(`Basemap config failed (HTTP ${response.status})`, response.status);
    }
    return (await response.json()) as BasemapCatalogResponse;
  } catch (err: unknown) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(`Network error fetching basemap config: ${String(err)}`, 0);
  }
}

export async function fetchCurrentWeather(
  lat: number = 28.66,
  lon: number = 77.25,
  forceRefresh: boolean = false
): Promise<NormalizedCurrentWeather> {
  const baseUrl = getApiBaseUrl();
  const query = new URLSearchParams({
    lat: lat.toString(),
    lon: lon.toString(),
    force_refresh: forceRefresh.toString(),
  });
  const endpoint = `${baseUrl}/api/weather/current?${query.toString()}`;

  try {
    const response = await fetch(endpoint, {
      method: 'GET',
      headers: { Accept: 'application/json' },
    });

    if (!response.ok) {
      const errorPayload = await response.json().catch(() => ({}));
      throw new ApiError(
        errorPayload.detail || `Current weather failed (HTTP ${response.status})`,
        response.status
      );
    }
    return (await response.json()) as NormalizedCurrentWeather;
  } catch (err: unknown) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(`Network error retrieving current weather: ${String(err)}`, 0);
  }
}

export async function fetchWeatherForecast(
  lat: number = 28.66,
  lon: number = 77.25,
  days: number = 3,
  forceRefresh: boolean = false
): Promise<NormalizedWeatherForecast> {
  const baseUrl = getApiBaseUrl();
  const query = new URLSearchParams({
    lat: lat.toString(),
    lon: lon.toString(),
    days: days.toString(),
    force_refresh: forceRefresh.toString(),
  });
  const endpoint = `${baseUrl}/api/weather/forecast?${query.toString()}`;

  try {
    const response = await fetch(endpoint, {
      method: 'GET',
      headers: { Accept: 'application/json' },
    });

    if (!response.ok) {
      const errorPayload = await response.json().catch(() => ({}));
      throw new ApiError(
        errorPayload.detail || `Forecast retrieval failed (HTTP ${response.status})`,
        response.status
      );
    }
    return (await response.json()) as NormalizedWeatherForecast;
  } catch (err: unknown) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(`Network error retrieving weather forecast: ${String(err)}`, 0);
  }
}

export async function refreshWeatherCache(
  lat: number,
  lon: number,
  refreshForecast: boolean = true
): Promise<WeatherRefreshResponse> {
  const baseUrl = getApiBaseUrl();
  const endpoint = `${baseUrl}/api/weather/refresh`;

  try {
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify({
        latitude: lat,
        longitude: lon,
        refresh_forecast: refreshForecast,
      }),
    });

    if (!response.ok) {
      const errorPayload = await response.json().catch(() => ({}));
      throw new ApiError(
        errorPayload.detail || `Cache refresh failed (HTTP ${response.status})`,
        response.status
      );
    }
    return (await response.json()) as WeatherRefreshResponse;
  } catch (err: unknown) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(`Network error executing cache refresh: ${String(err)}`, 0);
  }
}
