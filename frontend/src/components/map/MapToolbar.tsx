/**
 * frontend/src/components/map/MapToolbar.tsx
 *
 * Streamlined 5-Workspace Top Bar for PRAVAAH in authentic Cream & Brown styling:
 * 1. Overview
 * 2. Flood Map
 * 3. Prediction & Simulation
 * 4. Disaster Response
 * 5. Terrain Insights
 */

import React, { useState, useEffect } from 'react';
import {
  LayoutDashboard,
  Map,
  ShieldAlert,
  Maximize2,
  Minimize2,
} from 'lucide-react';

export type WorkspaceViewMode =
  | 'overview'
  | 'map'
  | 'disaster';

interface MapToolbarProps {
  mapContainerRef?: React.RefObject<HTMLDivElement | null>;
  activeView?: WorkspaceViewMode;
  onViewChange?: (view: WorkspaceViewMode) => void;
}

export const MapToolbar: React.FC<MapToolbarProps> = ({
  mapContainerRef,
  activeView = 'overview',
  onViewChange,
}) => {
  const [isFullscreen, setIsFullscreen] = useState(false);

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => {
      document.removeEventListener('fullscreenchange', handleFullscreenChange);
    };
  }, []);

  const toggleFullscreen = async () => {
    try {
      if (!document.fullscreenElement) {
        if (mapContainerRef?.current) {
          await mapContainerRef.current.requestFullscreen();
        } else {
          await document.documentElement.requestFullscreen();
        }
      } else {
        await document.exitFullscreen();
      }
    } catch (err) {
      console.error('Fullscreen toggle failed:', err);
    }
  };

  const navItems: { mode: WorkspaceViewMode; label: string; icon: React.ElementType }[] = [
    { mode: 'overview', label: 'Overview Dashboard', icon: LayoutDashboard },
    { mode: 'map', label: 'Flood Risk Map', icon: Map },
    { mode: 'disaster', label: 'Disaster Response & Shelters', icon: ShieldAlert },
  ];

  return (
    <div className="flex h-11 w-full items-center justify-between border-b border-[#EAE3D9] bg-[#FFFDF9] px-3 sm:px-4 text-xs select-none shadow-2xs z-20">
      {/* 5 Primary Workspace Tabs */}
      <div className="flex items-center gap-1 overflow-x-auto scrollbar-none">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeView === item.mode;

          return (
            <button
              key={item.mode}
              onClick={() => onViewChange?.(item.mode)}
              className={`flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-semibold transition-all whitespace-nowrap ${
                isActive
                  ? 'border border-[#EAE3D9] bg-[#F5EFEB] text-[#2C221E] shadow-2xs'
                  : 'text-[#635347] hover:bg-[#F5EFEB]/60 hover:text-[#2C221E]'
              }`}
            >
              <Icon className={`h-3.5 w-3.5 ${isActive ? 'text-[#8B4513]' : 'text-[#8C7869]'}`} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </div>

      {/* Right: Fullscreen Action */}
      <div className="flex items-center gap-2">
        <button
          onClick={toggleFullscreen}
          className="flex items-center gap-1 rounded-md border border-[#EAE3D9] bg-[#FFFFFF] px-2 py-1 text-[11px] font-medium text-[#635347] hover:bg-[#F5EFEB] hover:text-[#2C221E] transition-colors"
          title={isFullscreen ? 'Exit Fullscreen' : 'Enter Fullscreen'}
        >
          {isFullscreen ? (
            <>
              <Minimize2 className="h-3.5 w-3.5 text-[#8B4513]" />
              <span className="hidden md:inline">Exit Fullscreen</span>
            </>
          ) : (
            <>
              <Maximize2 className="h-3.5 w-3.5 text-[#8B4513]" />
              <span className="hidden md:inline">Fullscreen</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
};
