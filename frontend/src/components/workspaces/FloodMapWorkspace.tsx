/**
 * frontend/src/components/workspaces/FloodMapWorkspace.tsx
 *
 * Primary GIS Flood Map Workspace for PRAVAAH in authentic Cream & Brown styling:
 * - Occupies ~90-100% of the active workspace with map as primary visual element.
 * - Collapsible layer drawer and cartographic legend.
 * - Compact flood wave progression controller at bottom.
 * - Frames the Hathnikund (0 km) to Delhi ORB (251.05 km) Yamuna corridor.
 */

import React from 'react';
import { InteractiveGISMap } from '../map/InteractiveGISMap';

interface FloodMapWorkspaceProps {
  onNavigateToSimulation?: () => void;
  onNavigateToDisaster?: () => void;
}

export const FloodMapWorkspace: React.FC<FloodMapWorkspaceProps> = () => {
  return (
    <div className="h-full w-full overflow-hidden relative bg-[#FBF9F5]">
      <InteractiveGISMap />
    </div>
  );
};

