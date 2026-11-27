/**
 * frontend/src/services/riskAssessment.ts
 *
 * API client service for simplified flood risk assessment.
 */

import { getApiBaseUrl, ApiError } from './api';
import type {
  SupportedAreasResponse,
  AssessmentRequest,
  AssessmentResponse,
} from '../types/riskAssessment';

export const riskAssessmentApi = {
  /**
   * Fetch list of supported authentic geographical entities along the Yamuna corridor.
   */
  async getSupportedAreas(): Promise<SupportedAreasResponse> {
    const baseUrl = getApiBaseUrl();
    const endpoint = `${baseUrl}/api/assessment/areas`;

    try {
      const response = await fetch(endpoint, {
        method: 'GET',
        headers: { Accept: 'application/json' },
      });

      if (!response.ok) {
        throw new ApiError(
          `Failed to load supported areas: ${response.statusText}`,
          response.status
        );
      }
      return await response.json();
    } catch (error) {
      if (error instanceof ApiError) throw error;
      throw new ApiError(`Supported areas service unavailable: ${(error as Error).message}`);
    }
  },

  /**
   * Execute simplified, AI-powered flood risk assessment for a selected area and forecast horizon.
   */
  async assessRisk(request: AssessmentRequest): Promise<AssessmentResponse> {
    const baseUrl = getApiBaseUrl();
    const endpoint = `${baseUrl}/api/assessment/assess`;

    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
        },
        body: JSON.stringify({
          area_id: request.area_id,
          forecast_days: request.forecast_days || 1,
          horizon_hours: 24,
        }),
      });

      if (!response.ok) {
        throw new ApiError(
          `Risk assessment failed: ${response.statusText}`,
          response.status
        );
      }
      return await response.json();
    } catch (error) {
      if (error instanceof ApiError) throw error;
      throw new ApiError(`Risk assessment engine unavailable: ${(error as Error).message}`);
    }
  },
};
