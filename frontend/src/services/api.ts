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
 * Probes primary (/api/health) and fallback endpoints (/health, /api) to ensure
 * reliable connection status across diverse serverless routing configurations.
 */
export async function fetchHealth(): Promise<HealthStatus> {
  const baseUrl = getApiBaseUrl();
  const candidates = [
    `${baseUrl}/api/health`,
    `${baseUrl}/health`,
    `${baseUrl}/api`,
  ];

  let lastError: Error | null = null;

  for (const endpoint of candidates) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 12000);

      const response = await fetch(endpoint, {
        method: 'GET',
        headers: {
          Accept: 'application/json',
        },
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        lastError = new ApiError(
          `Backend returned HTTP status ${response.status} (${response.statusText}) at ${endpoint}`,
          response.status
        );
        continue;
      }

      const contentType = response.headers.get('content-type') || '';
      if (!contentType.includes('application/json')) {
        lastError = new ApiError(
          `Backend returned non-JSON response (${contentType || 'unknown'}) at ${endpoint}.`,
          response.status
        );
        continue;
      }

      const json = (await response.json()) as unknown;

      if (
        typeof json === 'object' &&
        json !== null &&
        'status' in json &&
        typeof (json as Record<string, unknown>).status === 'string'
      ) {
        const record = json as Record<string, unknown>;
        return {
          status: String(record.status),
          service: typeof record.service === 'string' ? record.service : 'PRAVAAH API',
          version: typeof record.version === 'string' ? record.version : '0.1.0',
        };
      }

      lastError = new ApiError(`Invalid health schema returned from ${endpoint}`);
    } catch (err: unknown) {
      if (err instanceof DOMException && err.name === 'AbortError') {
        lastError = new ApiError(`Connection timed out while contacting backend at ${endpoint}.`);
      } else if (err instanceof TypeError && err.message.toLowerCase().includes('failed to fetch')) {
        lastError = new ApiError(`Unable to reach backend service at ${endpoint}.`);
      } else if (err instanceof Error) {
        lastError = err;
      } else {
        lastError = new ApiError(String(err));
      }
    }
  }

  throw lastError || new ApiError('Unable to connect to backend API endpoints.');
}
