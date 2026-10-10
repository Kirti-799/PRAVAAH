export interface HealthStatus {
  status: string;
  service: string;
  version: string;
}

export interface ApiHealthState {
  data: HealthStatus | null;
  isLoading: boolean;
  error: string | null;
  lastChecked: Date | null;
}
