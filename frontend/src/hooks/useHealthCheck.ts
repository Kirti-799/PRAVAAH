import { useState, useEffect, useCallback } from 'react';
import { fetchHealth } from '../services/api';
import type { HealthStatus, ApiHealthState } from '../types/api';

export function useHealthCheck() {
  const [state, setState] = useState<ApiHealthState>({
    data: null,
    isLoading: true,
    error: null,
    lastChecked: null,
  });

  const checkHealth = useCallback(async () => {
    setState((prev) => ({
      ...prev,
      isLoading: true,
      error: null,
    }));

    try {
      const data: HealthStatus = await fetchHealth();
      setState({
        data,
        isLoading: false,
        error: null,
        lastChecked: new Date(),
      });
    } catch (err: unknown) {
      const errorMessage =
        err instanceof Error ? err.message : 'Unknown error checking health';
      setState({
        data: null,
        isLoading: false,
        error: errorMessage,
        lastChecked: new Date(),
      });
    }
  }, []);

  useEffect(() => {
    checkHealth();
  }, [checkHealth]);

  return {
    ...state,
    refetch: checkHealth,
  };
}
