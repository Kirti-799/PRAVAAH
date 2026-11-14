/**
 * frontend/src/services/hydrology.ts
 *
 * Client API service for fetching read-only non-ML hydrological intelligence.
 */

import { getApiBaseUrl, ApiError } from './api';
import type { HydrologySummaryResponse, HistoricalEventsResponse } from '../types/hydrology';

export async function fetchHydrologySummary(): Promise<HydrologySummaryResponse> {
  const baseUrl = getApiBaseUrl();
  const endpoint = `${baseUrl}/api/hydrology/summary`;

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 8000);

    const response = await fetch(endpoint, {
      method: 'GET',
      headers: {
        Accept: 'application/json',
      },
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new ApiError(
        `Backend returned HTTP status ${response.status} (${response.statusText})`,
        response.status
      );
    }

    const json = (await response.json()) as HydrologySummaryResponse;
    return json;
  } catch (error: unknown) {
    if (error instanceof ApiError) {
      throw error;
    }
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiError(`Connection timed out while contacting ${endpoint}.`);
    }
    if (error instanceof TypeError && error.message.toLowerCase().includes('failed to fetch')) {
      throw new ApiError(
        `Unable to reach backend service at ${baseUrl}. Ensure FastAPI is running on port 8000.`
      );
    }
    if (error instanceof Error) {
      throw new ApiError(`Hydrology service error: ${error.message}`);
    }
    throw new ApiError('An unexpected error occurred while fetching hydrological data.');
  }
}

export async function fetchHistoricalEvents(): Promise<HistoricalEventsResponse> {
  const baseUrl = getApiBaseUrl();
  const endpoint = `${baseUrl}/api/hydrology/events`;

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 8000);

    const response = await fetch(endpoint, {
      method: 'GET',
      headers: {
        Accept: 'application/json',
      },
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new ApiError(
        `Backend returned HTTP status ${response.status} (${response.statusText})`,
        response.status
      );
    }

    return (await response.json()) as HistoricalEventsResponse;
  } catch (error: unknown) {
    if (error instanceof ApiError) throw error;
    throw new ApiError(`Historical events service error: ${(error as Error).message}`);
  }
}
