/**
 * frontend/src/components/layout/AppLayout.tsx
 *
 * Root layout container for PRAVAAH — AI-Powered Flood Risk Assessment & Management System.
 * Connects the streamlined Sidebar, top Header, and GeospatialWorkspace.
 */

import React, { useState } from 'react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { GeospatialWorkspace } from '../map/GeospatialWorkspace';
import { ErrorBoundary } from '../common/ErrorBoundary';
import type { HealthStatus } from '../../types/api';

interface AppLayoutProps {
  isLoading: boolean;
  healthData: HealthStatus | null;
  error: string | null;
  lastChecked: Date | null;
  onRetry: () => void;
  onBackToLanding?: () => void;
}

export const AppLayout: React.FC<AppLayoutProps> = ({
  isLoading,
  healthData,
  error,
  lastChecked,
  onRetry,
  onBackToLanding,
}) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [activeNav, setActiveNav] = useState(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      const navParam = params.get('nav');
      if (navParam) {
        const lower = navParam.toLowerCase();
        if (lower === 'map' || lower === 'flood') return 'Flood Map';
        if (lower === 'simulation' || lower === 'sim') return 'Prediction & Simulation';
        if (lower === 'disaster') return 'Disaster Response';
        if (lower === 'terrain') return 'Terrain Insights';
        return navParam;
      }
    }
    return 'Overview';
  });

  const handleSelectNav = (name: string) => {
    setActiveNav(name);
  };

  return (
    <div className="flex h-screen max-h-screen w-full flex-col overflow-hidden bg-[#FBF9F5] text-[#2C221E]">
      {/* Top Header */}
      <Header
        onMenuToggle={() => setSidebarOpen(true)}
        isLoading={isLoading}
        healthData={healthData}
        error={error}
        onRetry={onRetry}
        onBackToLanding={onBackToLanding}
      />

      {/* Main Workspace Area: Sidebar + Primary Workspace */}
      <div className="flex flex-1 overflow-hidden relative">
        {/* Left Navigation Sidebar */}
        <Sidebar
          isOpen={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
          activeNav={activeNav}
          onSelectNav={handleSelectNav}
          isLoading={isLoading}
          healthData={healthData}
          error={error}
          lastChecked={lastChecked}
          onRetry={onRetry}
        />

        {/* Primary Analytical & GIS Workspace */}
        <main className="flex-1 h-full w-full overflow-hidden relative">
          <ErrorBoundary fallbackTitle="Workspace Recovered">
            <GeospatialWorkspace
              activeNav={activeNav}
              onNavChange={setActiveNav}
              isLoading={isLoading}
              healthData={healthData}
              error={error}
              lastChecked={lastChecked}
              onRetry={onRetry}
            />
          </ErrorBoundary>
        </main>
      </div>
    </div>
  );
};
