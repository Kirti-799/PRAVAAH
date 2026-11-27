import type { HealthStatus } from '../types/api';

const LOCAL_DEV_API_URL = 'http://localhost:8000';

/**
 * Resolves the backend base URL.
 * - Highest precedence: explicitly configured VITE_API_BASE_URL environment variable (if non-empty).
 * - Local development fallback (Vite dev server): http://localhost:8000.
 * - Production browser fallback (Vercel deployment): window.location.origin (same-origin /api routing).
 * - SSR/Node fallback: http://localhost:8000.
 */
export function getApiBaseUrl(): string {
  const envUrl = import.meta.env.VITE_API_BASE_URL;
  if (typeof envUrl === 'string' && envUrl.trim().length > 0) {
    return envUrl.trim().replace(/\/+$/, '');
  }

  // Running in browser context
  if (typeof window !== 'undefined' && window.location?.origin) {
    // In local Vite development, default to local FastAPI backend on port 8000
    if (import.meta.env.DEV) {
      return LOCAL_DEV_API_URL;
    }
    // In production Vercel deployment, use same-origin domain
    return window.location.origin.replace(/\/+$/, '');
  }

  return LOCAL_DEV_API_URL;
}

export class ApiError extends Error {
  public readonly status?: number;

  constructor(message: string, status?: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

/**
 * Fetches health status from the backend API.
 * Validates the schema and handles network and HTTP errors.
 */
export async function fetchHealth(): Promise<HealthStatus> {
  const baseUrl = getApiBaseUrl();
  const endpoint = `${baseUrl}/api/health`;

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 6000);

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

    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      throw new ApiError(
        `Backend returned non-JSON response (${contentType || 'unknown'}). The request at ${endpoint} was not handled by the backend API.`,
        response.status
      );
    }

    const json = (await response.json()) as unknown;

    if (
      typeof json === 'object' &&
      json !== null &&
      'status' in json &&
      'service' in json &&
      'version' in json &&
      typeof (json as Record<string, unknown>).status === 'string' &&
      typeof (json as Record<string, unknown>).service === 'string' &&
      typeof (json as Record<string, unknown>).version === 'string'
    ) {
      return json as HealthStatus;
    }

    throw new ApiError('Received invalid data format from backend health endpoint.');
  } catch (error: unknown) {
    if (error instanceof ApiError) {
      throw error;
    }

    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiError(`Connection timed out while contacting backend at ${endpoint}.`);
    }

    if (error instanceof TypeError && error.message.toLowerCase().includes('failed to fetch')) {
      const hint = import.meta.env.DEV
        ? 'Ensure FastAPI is running on port 8000 and CORS is properly configured.'
        : 'Ensure the API service is operational and CORS is properly configured.';
      throw new ApiError(`Unable to reach backend service at ${baseUrl}. ${hint}`);
    }

    if (error instanceof Error) {
      throw new ApiError(`Network error: ${error.message}`);
    }

    throw new ApiError('An unexpected network error occurred.');
  }
}
