/**
 * frontend/src/App.tsx
 *
 * Root Application Router for PRAVAAH.
 * Renders the new visual LandingPage by default.
 * Transitions smoothly to the interactive AppLayout workspace when the user clicks "Get Started".
 */

import React, { useState } from 'react';
import { LandingPage } from './pages/LandingPage';
import { AppLayout } from './components/layout/AppLayout';
import { useHealthCheck } from './hooks/useHealthCheck';

export const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<'landing' | 'app'>('landing');
  const { data, isLoading, error, lastChecked, refetch } = useHealthCheck();

  if (currentView === 'landing') {
    return <LandingPage onGetStarted={() => setCurrentView('app')} />;
  }

  return (
    <AppLayout
      isLoading={isLoading}
      healthData={data}
      error={error}
      lastChecked={lastChecked}
      onRetry={refetch}
      onBackToLanding={() => setCurrentView('landing')}
    />
  );
};

export default App;
