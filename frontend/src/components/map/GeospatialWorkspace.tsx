/**
 * frontend/src/components/map/GeospatialWorkspace.tsx
 *
 * Primary Unified Workspace Container for PRAVAAH in authentic Cream & Brown styling:
 * Houses the 5 unified workspaces:
 * 1. Overview (Default)
 * 2. Flood Map
 * 3. Prediction & Simulation
 * 4. Disaster Response
 * 5. Terrain Insights
 */

import React, { useRef, useState, useEffect } from 'react';
import { MapToolbar, type WorkspaceViewMode } from './MapToolbar';
import { OverviewWorkspace } from '../workspaces/OverviewWorkspace';
import { FloodMapWorkspace } from '../workspaces/FloodMapWorkspace';
import { SimulationWorkspace } from '../workspaces/SimulationWorkspace';
import { DisasterResponseWorkspace } from '../workspaces/DisasterResponseWorkspace';
import { TerrainInsightsWorkspace } from '../workspaces/TerrainInsightsWorkspace';
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
    if (activeNav === 'Overview') {
      setViewMode('overview');
    } else if (activeNav === 'Flood Map' || activeNav === 'Flood Risk Map') {
      setViewMode('map');
    } else if (activeNav === 'Prediction & Simulation' || activeNav === 'Tabletop Scenario') {
      setViewMode('simulation');
    } else if (activeNav === 'Disaster Response' || activeNav === 'Disaster Intelligence') {
      setViewMode('disaster');
    } else if (activeNav === 'Terrain Insights' || activeNav === 'Spatial Infrastructure') {
      setViewMode('terrain');
    }
  }, [activeNav]);

  const handleViewChange = (newView: WorkspaceViewMode) => {
    setViewMode(newView);
    if (onNavChange) {
      if (newView === 'overview') onNavChange('Overview');
      else if (newView === 'map') onNavChange('Flood Map');
      else if (newView === 'simulation') onNavChange('Prediction & Simulation');
      else if (newView === 'disaster') onNavChange('Disaster Response');
      else if (newView === 'terrain') onNavChange('Terrain Insights');
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
              if (navName === 'Flood Map') handleViewChange('map');
              else if (navName === 'Prediction & Simulation') handleViewChange('simulation');
              else if (navName === 'Disaster Response') handleViewChange('disaster');
              else if (navName === 'Terrain Insights') handleViewChange('terrain');
            }}
          />
        )}

        {viewMode === 'map' && (
          <FloodMapWorkspace
            onNavigateToSimulation={() => handleViewChange('simulation')}
            onNavigateToDisaster={() => handleViewChange('disaster')}
          />
        )}

        {viewMode === 'simulation' && (
          <SimulationWorkspace
            onNavigateToMap={() => handleViewChange('map')}
          />
        )}

        {viewMode === 'disaster' && (
          <DisasterResponseWorkspace
            onNavigateToMap={() => handleViewChange('map')}
          />
        )}

        {viewMode === 'terrain' && (
          <TerrainInsightsWorkspace
            onNavigateToMap={() => handleViewChange('map')}
          />
        )}
      </div>
    </div>
  );
};
