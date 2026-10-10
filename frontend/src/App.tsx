import React from 'react';
import { AppLayout } from './components/layout/AppLayout';
import { DashboardPage } from './pages/DashboardPage';
import { useHealthCheck } from './hooks/useHealthCheck';

export const App: React.FC = () => {
  const { data, isLoading, error, lastChecked, refetch } = useHealthCheck();

  return (
    <AppLayout
      isLoading={isLoading}
      healthData={data}
      error={error}
      onRetry={refetch}
    >
      <DashboardPage
        isLoading={isLoading}
        healthData={data}
        error={error}
        lastChecked={lastChecked}
        onRetry={refetch}
      />
    </AppLayout>
  );
};

export default App;
