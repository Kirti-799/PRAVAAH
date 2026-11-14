/**
 * frontend/src/services/routing.ts
 *
 * Client API service for fetching hydrological routing readiness and simulation prototypes.
 */

import { getApiBaseUrl, ApiError } from './api';
import type {
  RoutingReadinessResponse,
  RoutingSimulationResponse,
  SpatialRoutingSimulationResponse,
} from '../types/routing';

export async function fetchRoutingReadiness(): Promise<RoutingReadinessResponse> {
  const baseUrl = getApiBaseUrl();
  const endpoint = `${baseUrl}/api/hydrology/routing-readiness`;

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
      throw new ApiError(
        `Backend returned HTTP status ${response.status} (${response.statusText})`,
        response.status
      );
    }

    return (await response.json()) as RoutingReadinessResponse;
  } catch (error: unknown) {
    if (error instanceof ApiError) throw error;
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiError(`Connection timed out while contacting ${endpoint}.`);
    }
    if (error instanceof Error) {
      throw new ApiError(`Routing readiness service error: ${error.message}`);
    }
    throw new ApiError('An unexpected error occurred while fetching routing readiness.');
  }
}

export async function fetchRoutingSimulation(
  episodeId: string = 'EPISODE_2023_08',
  K_hours: number = 36.0,
  x: number = 0.20
): Promise<RoutingSimulationResponse> {
  const baseUrl = getApiBaseUrl();
  const url = new URL(`${baseUrl}/api/hydrology/routing-simulation`);
  url.searchParams.append('episode_id', episodeId);
  url.searchParams.append('K_hours', K_hours.toString());
  url.searchParams.append('x', x.toString());

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 8000);

    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: { Accept: 'application/json' },
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorJson = await response.json().catch(() => null);
      const detail = errorJson?.detail || response.statusText;
      throw new ApiError(
        `Backend returned HTTP ${response.status}: ${detail}`,
        response.status
      );
    }

    return (await response.json()) as RoutingSimulationResponse;
  } catch (error: unknown) {
    if (error instanceof ApiError) throw error;
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiError(`Connection timed out while contacting simulation endpoint.`);
    }
    if (error instanceof Error) {
      throw new ApiError(`Routing simulation error: ${error.message}`);
    }
    throw new ApiError('An unexpected error occurred while running routing simulation.');
  }
}

export async function fetchSpatialRoutingSimulation(
  episodeId: string = 'EPISODE_2023_08',
  K_hours: number = 36.0,
  x: number = 0.20,
  intervalKm: number = 5.0
): Promise<SpatialRoutingSimulationResponse> {
  const baseUrl = getApiBaseUrl();
  const url = new URL(`${baseUrl}/api/hydrology/routing-simulation-spatial`);
  url.searchParams.append('episode_id', episodeId);
  url.searchParams.append('K_hours', K_hours.toString());
  url.searchParams.append('x', x.toString());
  url.searchParams.append('interval_km', intervalKm.toString());

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);

    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: { Accept: 'application/json' },
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorJson = await response.json().catch(() => null);
      const detail = errorJson?.detail || response.statusText;
      throw new ApiError(
        `Backend returned HTTP ${response.status}: ${detail}`,
        response.status
      );
    }

    return (await response.json()) as SpatialRoutingSimulationResponse;
  } catch (error: unknown) {
    if (error instanceof ApiError) throw error;
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiError(`Connection timed out while contacting spatial routing endpoint.`);
    }
    if (error instanceof Error) {
      throw new ApiError(`Spatial routing simulation error: ${error.message}`);
    }
    throw new ApiError('An unexpected error occurred while running spatial routing simulation.');
  }
}


export async function fetchTabletopPresets(): Promise<import('../types/routing').TabletopPresetsResponse> {
  const baseUrl = getApiBaseUrl();
  const endpoint = `${baseUrl}/api/hydrology/tabletop-presets`;

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
      throw new ApiError(
        `Backend returned HTTP status ${response.status} (${response.statusText})`,
        response.status
      );
    }

    return (await response.json()) as import('../types/routing').TabletopPresetsResponse;
  } catch (error: unknown) {
    if (error instanceof ApiError) throw error;
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiError(`Connection timed out while contacting ${endpoint}.`);
    }
    if (error instanceof Error) {
      throw new ApiError(`Tabletop presets service error: ${error.message}`);
    }
    throw new ApiError('An unexpected error occurred while fetching tabletop presets.');
  }
}

export async function runTabletopScenario(
  payload: import('../types/routing').TabletopScenarioRequest
): Promise<import('../types/routing').TabletopScenarioResponse> {
  const baseUrl = getApiBaseUrl();
  const endpoint = `${baseUrl}/api/hydrology/tabletop-scenario`;

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 8000);

    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorJson = await response.json().catch(() => null);
      const detail = errorJson?.detail || response.statusText;
      throw new ApiError(
        `Backend returned HTTP ${response.status}: ${detail}`,
        response.status
      );
    }

    return (await response.json()) as import('../types/routing').TabletopScenarioResponse;
  } catch (error: unknown) {
    if (error instanceof ApiError) throw error;
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiError(`Connection timed out while contacting tabletop simulation endpoint.`);
    }
    if (error instanceof Error) {
      throw new ApiError(`Tabletop scenario error: ${error.message}`);
    }
    throw new ApiError('An unexpected error occurred while running tabletop scenario simulation.');
  }
}

