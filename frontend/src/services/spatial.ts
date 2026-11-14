/**
 * frontend/src/services/spatial.ts
 *
 * Client API service for fetching spatial data inventories, study area contracts,
 * DEM status, and terrain elevation/slope summaries.
 */

import { getApiBaseUrl, ApiError } from './api';
import type {
  SpatialInventoryResponse,
  StudyAreaMetadataResponse,
  DEMStatusResponse,
  TerrainSummaryResponse,
  RiverNetworkStatusResponse,
  RiverGeoJSONResponse,
  HydrographyStatusResponse,
  HydrographyLayersResponse,
  HydrographySummaryResponse,
  RiverNetworkGraphResponse,
  RiverChainageResponse,
} from '../types/spatial';

export async function fetchSpatialInventory(): Promise<SpatialInventoryResponse> {
  const baseUrl = getApiBaseUrl();
  const endpoint = `${baseUrl}/api/spatial/inventory`;

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
        `Backend returned HTTP ${response.status} (${response.statusText})`,
        response.status
      );
    }

    return (await response.json()) as SpatialInventoryResponse;
  } catch (error: unknown) {
    if (error instanceof ApiError) throw error;
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiError(`Connection timed out while contacting ${endpoint}.`);
    }
    if (error instanceof Error) {
      throw new ApiError(`Spatial inventory service error: ${error.message}`);
    }
    throw new ApiError('An unexpected error occurred while fetching spatial inventory.');
  }
}

export async function fetchStudyAreaMetadata(): Promise<StudyAreaMetadataResponse> {
  const baseUrl = getApiBaseUrl();
  const endpoint = `${baseUrl}/api/spatial/study-area`;

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
        `Backend returned HTTP ${response.status} (${response.statusText})`,
        response.status
      );
    }

    return (await response.json()) as StudyAreaMetadataResponse;
  } catch (error: unknown) {
    if (error instanceof ApiError) throw error;
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiError(`Connection timed out while contacting ${endpoint}.`);
    }
    if (error instanceof Error) {
      throw new ApiError(`Study area service error: ${error.message}`);
    }
    throw new ApiError('An unexpected error occurred while fetching study area metadata.');
  }
}

export async function fetchDEMStatus(): Promise<DEMStatusResponse> {
  const baseUrl = getApiBaseUrl();
  const endpoint = `${baseUrl}/api/spatial/dem/status`;

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
        `Backend returned HTTP ${response.status} (${response.statusText})`,
        response.status
      );
    }

    return (await response.json()) as DEMStatusResponse;
  } catch (error: unknown) {
    if (error instanceof ApiError) throw error;
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiError(`Connection timed out while contacting ${endpoint}.`);
    }
    if (error instanceof Error) {
      throw new ApiError(`DEM status service error: ${error.message}`);
    }
    throw new ApiError('An unexpected error occurred while checking DEM status.');
  }
}

export async function fetchTerrainSummary(): Promise<TerrainSummaryResponse> {
  const baseUrl = getApiBaseUrl();
  const endpoint = `${baseUrl}/api/spatial/terrain/summary`;

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
        `Backend returned HTTP ${response.status} (${response.statusText})`,
        response.status
      );
    }

    return (await response.json()) as TerrainSummaryResponse;
  } catch (error: unknown) {
    if (error instanceof ApiError) throw error;
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiError(`Connection timed out while contacting ${endpoint}.`);
    }
    if (error instanceof Error) {
      throw new ApiError(`Terrain summary service error: ${error.message}`);
    }
    throw new ApiError('An unexpected error occurred while fetching terrain summary.');
  }
}

export async function fetchRiverStatus(): Promise<RiverNetworkStatusResponse> {
  const baseUrl = getApiBaseUrl();
  const endpoint = `${baseUrl}/api/spatial/river/status`;

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
        `Backend returned HTTP ${response.status} (${response.statusText})`,
        response.status
      );
    }

    return (await response.json()) as RiverNetworkStatusResponse;
  } catch (error: unknown) {
    if (error instanceof ApiError) throw error;
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiError(`Connection timed out while contacting ${endpoint}.`);
    }
    if (error instanceof Error) {
      throw new ApiError(`River status service error: ${error.message}`);
    }
    throw new ApiError('An unexpected error occurred while fetching river status.');
  }
}

export async function fetchRiverFeatures(clipToCorridor: boolean = true): Promise<RiverGeoJSONResponse> {
  const baseUrl = getApiBaseUrl();
  const endpoint = `${baseUrl}/api/spatial/river/features?clip_to_corridor=${clipToCorridor}`;

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);

    const response = await fetch(endpoint, {
      method: 'GET',
      headers: { Accept: 'application/json' },
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new ApiError(
        `Backend returned HTTP ${response.status} (${response.statusText})`,
        response.status
      );
    }

    return (await response.json()) as RiverGeoJSONResponse;
  } catch (error: unknown) {
    if (error instanceof ApiError) throw error;
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiError(`Connection timed out while contacting ${endpoint}.`);
    }
    if (error instanceof Error) {
      throw new ApiError(`River features service error: ${error.message}`);
    }
    throw new ApiError('An unexpected error occurred while fetching river features.');
  }
}

// ==============================================================================
// Phase 3B: Advanced Hydrography API Clients
// ==============================================================================

export async function fetchHydrographyStatus(): Promise<HydrographyStatusResponse> {
  const baseUrl = getApiBaseUrl();
  const endpoint = `${baseUrl}/api/spatial/hydrography/status`;

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
        `Backend returned HTTP ${response.status} (${response.statusText})`,
        response.status
      );
    }

    return (await response.json()) as HydrographyStatusResponse;
  } catch (error: unknown) {
    if (error instanceof ApiError) throw error;
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiError(`Connection timed out while contacting ${endpoint}.`);
    }
    if (error instanceof Error) {
      throw new ApiError(`Hydrography status service error: ${error.message}`);
    }
    throw new ApiError('An unexpected error occurred while fetching hydrography status.');
  }
}

export async function fetchHydrographyLayers(clipToCorridor: boolean = true): Promise<HydrographyLayersResponse> {
  const baseUrl = getApiBaseUrl();
  const endpoint = `${baseUrl}/api/spatial/hydrography/layers?clip_to_corridor=${clipToCorridor}`;

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);

    const response = await fetch(endpoint, {
      method: 'GET',
      headers: { Accept: 'application/json' },
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new ApiError(
        `Backend returned HTTP ${response.status} (${response.statusText})`,
        response.status
      );
    }

    return (await response.json()) as HydrographyLayersResponse;
  } catch (error: unknown) {
    if (error instanceof ApiError) throw error;
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiError(`Connection timed out while contacting ${endpoint}.`);
    }
    if (error instanceof Error) {
      throw new ApiError(`Hydrography layers service error: ${error.message}`);
    }
    throw new ApiError('An unexpected error occurred while fetching hydrography layers.');
  }
}

export async function fetchHydrographySummary(): Promise<HydrographySummaryResponse> {
  const baseUrl = getApiBaseUrl();
  const endpoint = `${baseUrl}/api/spatial/hydrography/summary`;

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
        `Backend returned HTTP ${response.status} (${response.statusText})`,
        response.status
      );
    }

    return (await response.json()) as HydrographySummaryResponse;
  } catch (error: unknown) {
    if (error instanceof ApiError) throw error;
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiError(`Connection timed out while contacting ${endpoint}.`);
    }
    if (error instanceof Error) {
      throw new ApiError(`Hydrography summary service error: ${error.message}`);
    }
    throw new ApiError('An unexpected error occurred while fetching hydrography summary.');
  }
}

export async function fetchHydrographyNetwork(): Promise<RiverNetworkGraphResponse> {
  const baseUrl = getApiBaseUrl();
  const endpoint = `${baseUrl}/api/spatial/hydrography/network`;

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
        `Backend returned HTTP ${response.status} (${response.statusText})`,
        response.status
      );
    }

    return (await response.json()) as RiverNetworkGraphResponse;
  } catch (error: unknown) {
    if (error instanceof ApiError) throw error;
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiError(`Connection timed out while contacting ${endpoint}.`);
    }
    if (error instanceof Error) {
      throw new ApiError(`River network graph service error: ${error.message}`);
    }
    throw new ApiError('An unexpected error occurred while fetching river network graph.');
  }
}

export async function fetchHydrographyChainage(intervalKm: number = 5.0): Promise<RiverChainageResponse> {
  const baseUrl = getApiBaseUrl();
  const endpoint = `${baseUrl}/api/spatial/hydrography/chainage?interval_km=${intervalKm}`;

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
        `Backend returned HTTP ${response.status} (${response.statusText})`,
        response.status
      );
    }

    return (await response.json()) as RiverChainageResponse;
  } catch (error: unknown) {
    if (error instanceof ApiError) throw error;
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiError(`Connection timed out while contacting ${endpoint}.`);
    }
    if (error instanceof Error) {
      throw new ApiError(`River chainage service error: ${error.message}`);
    }
    throw new ApiError('An unexpected error occurred while fetching river chainage.');
  }
}

// --- Phase 3D: Upstream Catchment & Rainfall Service Functions ---

export async function fetchCatchmentStatus(): Promise<import('../types/spatial').CatchmentStatusResponse> {
  const baseUrl = getApiBaseUrl();
  const endpoint = `${baseUrl}/api/spatial/catchment/status`;
  try {
    const response = await fetch(endpoint, {
      method: 'GET',
      headers: { Accept: 'application/json' },
    });
    if (!response.ok) {
      throw new ApiError(`Backend returned HTTP ${response.status}`, response.status);
    }
    return (await response.json()) as import('../types/spatial').CatchmentStatusResponse;
  } catch (error: unknown) {
    if (error instanceof ApiError) throw error;
    if (error instanceof Error) {
      throw new ApiError(`Catchment status error: ${error.message}`);
    }
    throw new ApiError('An unexpected error occurred while fetching catchment status.');
  }
}

export async function fetchCatchmentSummary(): Promise<import('../types/spatial').CatchmentSummaryResponse> {
  const baseUrl = getApiBaseUrl();
  const endpoint = `${baseUrl}/api/spatial/catchment/summary`;
  try {
    const response = await fetch(endpoint, {
      method: 'GET',
      headers: { Accept: 'application/json' },
    });
    if (!response.ok) {
      throw new ApiError(`Backend returned HTTP ${response.status}`, response.status);
    }
    return (await response.json()) as import('../types/spatial').CatchmentSummaryResponse;
  } catch (error: unknown) {
    if (error instanceof ApiError) throw error;
    if (error instanceof Error) {
      throw new ApiError(`Catchment summary error: ${error.message}`);
    }
    throw new ApiError('An unexpected error occurred while fetching catchment summary.');
  }
}

export async function fetchCatchmentGeometry(): Promise<any> {
  const baseUrl = getApiBaseUrl();
  const endpoint = `${baseUrl}/api/spatial/catchment/geometry`;
  try {
    const response = await fetch(endpoint, {
      method: 'GET',
      headers: { Accept: 'application/json' },
    });
    if (!response.ok) {
      throw new ApiError(`Backend returned HTTP ${response.status}`, response.status);
    }
    return await response.json();
  } catch (error: unknown) {
    if (error instanceof ApiError) throw error;
    if (error instanceof Error) {
      throw new ApiError(`Catchment geometry error: ${error.message}`);
    }
    throw new ApiError('An unexpected error occurred while fetching catchment geometry.');
  }
}

export async function fetchCatchmentDrainage(): Promise<any> {
  const baseUrl = getApiBaseUrl();
  const endpoint = `${baseUrl}/api/spatial/catchment/drainage`;
  try {
    const response = await fetch(endpoint, {
      method: 'GET',
      headers: { Accept: 'application/json' },
    });
    if (!response.ok) {
      throw new ApiError(`Backend returned HTTP ${response.status}`, response.status);
    }
    return await response.json();
  } catch (error: unknown) {
    if (error instanceof ApiError) throw error;
    if (error instanceof Error) {
      throw new ApiError(`Catchment drainage error: ${error.message}`);
    }
    throw new ApiError('An unexpected error occurred while fetching catchment drainage.');
  }
}

export async function fetchRainfallCatchmentSummary(forceRefresh: boolean = false): Promise<import('../types/spatial').CatchmentRainfallSummaryResponse> {
  const baseUrl = getApiBaseUrl();
  const endpoint = `${baseUrl}/api/rainfall/catchment/summary${forceRefresh ? '?force_refresh=true' : ''}`;
  try {
    const response = await fetch(endpoint, {
      method: 'GET',
      headers: { Accept: 'application/json' },
    });
    if (!response.ok) {
      throw new ApiError(`Backend returned HTTP ${response.status}`, response.status);
    }
    return (await response.json()) as import('../types/spatial').CatchmentRainfallSummaryResponse;
  } catch (error: unknown) {
    if (error instanceof ApiError) throw error;
    if (error instanceof Error) {
      throw new ApiError(`Rainfall catchment summary error: ${error.message}`);
    }
    throw new ApiError('An unexpected error occurred while fetching rainfall catchment summary.');
  }
}

export async function fetchRainfallStatus(): Promise<import('../types/spatial').RainfallStatusResponse> {
  const baseUrl = getApiBaseUrl();
  const endpoint = `${baseUrl}/api/rainfall/status`;
  try {
    const response = await fetch(endpoint, {
      method: 'GET',
      headers: { Accept: 'application/json' },
    });
    if (!response.ok) {
      throw new ApiError(`Backend returned HTTP ${response.status}`, response.status);
    }
    return (await response.json()) as import('../types/spatial').RainfallStatusResponse;
  } catch (error: unknown) {
    if (error instanceof ApiError) throw error;
    if (error instanceof Error) {
      throw new ApiError(`Rainfall status error: ${error.message}`);
    }
    throw new ApiError('An unexpected error occurred while fetching rainfall status.');
  }
}


