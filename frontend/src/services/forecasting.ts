/**
 * frontend/src/services/forecasting.ts
 *
 * Client API service for fetching upstream forecasting readiness,
 * Phase 2B model status, and experimental demonstration discharge forecasts.
 */

import { getApiBaseUrl, ApiError } from './api';
import type {
  ForecastingReadinessResponse,
  DischargeModelStatusResponse,
  ExperimentalDischargeForecastResponse,
} from '../types/forecasting';

export async function fetchForecastingReadiness(): Promise<ForecastingReadinessResponse> {
  const baseUrl = getApiBaseUrl();
  const endpoint = `${baseUrl}/api/forecasting/readiness`;

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

    return (await response.json()) as ForecastingReadinessResponse;
  } catch (error: unknown) {
    if (error instanceof ApiError) throw error;
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiError(`Connection timed out while contacting ${endpoint}.`);
    }
    if (error instanceof Error) {
      throw new ApiError(`Forecasting readiness service error: ${error.message}`);
    }
    throw new ApiError('An unexpected error occurred while fetching forecasting readiness.');
  }
}

export async function fetchDischargeModelStatus(): Promise<DischargeModelStatusResponse> {
  const baseUrl = getApiBaseUrl();
  const endpoint = `${baseUrl}/api/forecasting/model-status`;

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

    return (await response.json()) as DischargeModelStatusResponse;
  } catch (error: unknown) {
    if (error instanceof ApiError) throw error;
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiError(`Connection timed out while contacting ${endpoint}.`);
    }
    if (error instanceof Error) {
      throw new ApiError(`Model status service error: ${error.message}`);
    }
    throw new ApiError('An unexpected error occurred while fetching discharge model status.');
  }
}

export async function fetchSampleHistoricalForecast(): Promise<ExperimentalDischargeForecastResponse> {
  const baseUrl = getApiBaseUrl();
  const endpoint = `${baseUrl}/api/forecasting/sample-forecast`;

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

    return (await response.json()) as ExperimentalDischargeForecastResponse;
  } catch (error: unknown) {
    if (error instanceof ApiError) throw error;
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiError(`Connection timed out while contacting ${endpoint}.`);
    }
    if (error instanceof Error) {
      throw new ApiError(`Sample forecast service error: ${error.message}`);
    }
    throw new ApiError('An unexpected error occurred while fetching sample forecast.');
  }
}
