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
    let isMounted = true;
    checkHealth();

    // In serverless environments, an initial cold start can cause a transient delay.
    // Automatically perform a follow-up verification check after 3 seconds.
    const timer = setTimeout(() => {
      if (isMounted) {
        checkHealth();
      }
    }, 3000);

    return () => {
      isMounted = false;
      clearTimeout(timer);
    };
  }, [checkHealth]);

  return {
    ...state,
    refetch: checkHealth,
  };
}
