/**
 * frontend/src/services/disaster.ts
 *
 * Client API service for Disaster Intelligence, Risk Assessment, and Shelters.
 */

import { getApiBaseUrl, ApiError } from './api';
import type { DisasterRiskSummaryResponse } from '../types/disaster';
import type { FeatureCollection } from 'geojson';

export async function fetchDisasterRiskSummary(
  inflowCumecs?: number
): Promise<DisasterRiskSummaryResponse> {
  const baseUrl = getApiBaseUrl();
  const query = inflowCumecs !== undefined ? `?inflow_cumecs=${inflowCumecs}` : '';
  const endpoint = `${baseUrl}/api/disaster/risk-summary${query}`;

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
        `Failed to fetch disaster risk summary: ${response.statusText}`,
        response.status
      );
    }

    return await response.json();
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError(
      `Disaster Risk Service unavailable: ${(error as Error).message}`
    );
  }
}

export async function fetchSheltersGeoJSON(): Promise<FeatureCollection> {
  const baseUrl = getApiBaseUrl();
  const endpoint = `${baseUrl}/api/disaster/shelters`;

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
        `Failed to fetch shelters GeoJSON: ${response.statusText}`,
        response.status
      );
    }

    return await response.json();
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError(
      `Shelters GeoJSON unavailable: ${(error as Error).message}`
    );
  }
}

export async function fetchEvacuationCorridorsGeoJSON(): Promise<FeatureCollection> {
  const baseUrl = getApiBaseUrl();
  const endpoint = `${baseUrl}/api/disaster/evacuation-corridors`;

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
        `Failed to fetch evacuation corridors GeoJSON: ${response.statusText}`,
        response.status
      );
    }

    return await response.json();
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError(
      `Evacuation Corridors GeoJSON unavailable: ${(error as Error).message}`
    );
  }
}

