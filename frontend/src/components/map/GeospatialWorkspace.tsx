/**
 * frontend/src/components/map/GeospatialWorkspace.tsx
 *
 * Primary Unified Workspace Container for PRAVAAH in authentic Cream & Brown styling:
 * Houses the 3 core workspaces:
 * 1. Overview Dashboard (Default)
 * 2. Flood Risk Map (AI-Powered 24h Prediction & Risk Assessment)
 * 3. Disaster Response & Shelters
 */

import React, { useRef, useState, useEffect } from 'react';
import { MapToolbar, type WorkspaceViewMode } from './MapToolbar';
import { OverviewWorkspace } from '../workspaces/OverviewWorkspace';
import { FloodRiskMapWorkspace } from '../assessment/FloodRiskMapWorkspace';
import { DisasterResponseWorkspace } from '../workspaces/DisasterResponseWorkspace';
import type { HealthStatus } from '../../types/api';

interface GeospatialWorkspaceProps {
  activeNav?: string;
  onNavChange?: (nav: string) => void;
  isLoading?: boolean;
  healthData?: HealthStatus | null;
  error?: string | null;
  lastChecked?: Date | null;
  onRetry?: () => void;
}

export const GeospatialWorkspace: React.FC<GeospatialWorkspaceProps> = ({
  activeNav = 'Overview',
  onNavChange,
  isLoading = false,
  healthData = null,
  error = null,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [viewMode, setViewMode] = useState<WorkspaceViewMode>('overview');

  // Synchronize with sidebar navigation selection
  useEffect(() => {
    if (activeNav === 'Overview' || activeNav === 'Overview Dashboard') {
      setViewMode('overview');
    } else if (activeNav === 'Flood Map' || activeNav === 'Flood Risk Map') {
      setViewMode('map');
    } else if (activeNav === 'Disaster Response' || activeNav === 'Disaster Response & Shelters' || activeNav === 'Disaster Intelligence') {
      setViewMode('disaster');
    } else {
      setViewMode('overview');
    }
  }, [activeNav]);

  const handleViewChange = (newView: WorkspaceViewMode) => {
    setViewMode(newView);
    if (onNavChange) {
      if (newView === 'overview') onNavChange('Overview');
      else if (newView === 'map') onNavChange('Flood Map');
      else if (newView === 'disaster') onNavChange('Disaster Response');
    }
  };

  return (
    <div
      ref={containerRef}
      className="flex h-full w-full flex-col overflow-hidden bg-[#FBF9F5]"
    >
      {/* Top View Selector Bar */}
      <MapToolbar
        mapContainerRef={containerRef}
        activeView={viewMode}
        onViewChange={handleViewChange}
      />

      {/* Main Workspace Surface */}
      <div className="flex-1 w-full h-full overflow-hidden relative">
        {viewMode === 'overview' && (
          <OverviewWorkspace
            isLoading={isLoading}
            healthData={healthData}
            error={error}
            onNavigate={(navName) => {
              if (navName === 'Flood Map' || navName === 'Flood Risk Map') handleViewChange('map');
              else if (navName === 'Disaster Response' || navName === 'Disaster Response & Shelters') handleViewChange('disaster');
            }}
          />
        )}

        {viewMode === 'map' && (
          <FloodRiskMapWorkspace
            onNavigateToEvacuation={() => handleViewChange('disaster')}
          />
        )}

        {viewMode === 'disaster' && (
          <DisasterResponseWorkspace
            onNavigateToMap={() => handleViewChange('map')}
          />
        )}
      </div>
    </div>
  );
};
