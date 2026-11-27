/**
 * frontend/src/components/layout/Sidebar.tsx
 *
 * Unified 5-Workspace Primary Navigation for PRAVAAH in authentic Cream & Brown styling:
 * 1. Overview
 * 2. Flood Map
 * 3. Prediction & Simulation
 * 4. Disaster Response
 * 5. Terrain Insights
 */

import React from 'react';
import {
  LayoutDashboard,
  Map,
  ShieldAlert,
  X,
  RefreshCw,
  CheckCircle2,
  XCircle,
  Compass,
} from 'lucide-react';
import type { HealthStatus } from '../../types/api';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  activeNav: string;
  onSelectNav: (name: string) => void;
  isLoading: boolean;
  healthData: HealthStatus | null;
  error: string | null;
  lastChecked: Date | null;
  onRetry: () => void;
}

interface NavItem {
  name: string;
  label: string;
  icon: React.ElementType;
  description: string;
}

const PRIMARY_NAV_ITEMS: NavItem[] = [
  {
    name: 'Overview',
    label: 'Overview',
    icon: LayoutDashboard,
    description: 'Corridor summary, CWC gauge & 24h discharge indicators',
  },
  {
    name: 'Flood Risk Map',
    label: 'Flood Risk Map',
    icon: Map,
    description: 'Interactive 24-hour flood risk map & geographical assessment',
  },
  {
    name: 'Disaster Response',
    label: 'Disaster Response',
    icon: ShieldAlert,
    description: 'CWC gauge thresholds, candidate shelters & evacuation corridors',
  },
];

export const Sidebar: React.FC<SidebarProps> = ({
  isOpen,
  onClose,
  activeNav,
  onSelectNav,
  isLoading,
  healthData,
  error,
  lastChecked,
  onRetry,
}) => {
  const isConnected = !isLoading && !error && healthData?.status === 'ok';

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-[#2C221E]/60 backdrop-blur-xs lg:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 flex w-72 flex-col border-r border-[#EAE3D9] bg-[#FFFDF9] transition-transform duration-200 ease-in-out lg:static lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Mobile Header */}
        <div className="flex h-14 items-center justify-between border-b border-[#EAE3D9] px-4 lg:hidden bg-[#FBF9F5]">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded bg-[#8B4513] text-white">
              <Compass className="h-4 w-4" />
            </div>
            <span className="font-bold text-[#2C221E]">PRAVAAH</span>
          </div>
          <button
            onClick={onClose}
            className="rounded p-1 text-[#635347] hover:bg-[#F5EFEB] hover:text-[#2C221E]"
            aria-label="Close navigation sidebar"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Navigation Workspaces List */}
        <div className="flex-1 overflow-y-auto px-3 py-4">
          <div className="mb-2 px-3 text-[10px] font-bold uppercase tracking-wider text-[#8C7869]">
            Primary Workspaces
          </div>

          <nav className="space-y-1" aria-label="Workspaces">
            {PRIMARY_NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              const isActive =
                activeNav === item.name ||
                (item.name === 'Flood Risk Map' && (activeNav === 'Flood Map' || activeNav === 'Flood Risk Map'));

              return (
                <button
                  key={item.name}
                  onClick={() => {
                    onSelectNav(item.name);
                    onClose();
                  }}
                  className={`group flex w-full flex-col rounded-lg px-3 py-2.5 text-left transition-all ${
                    isActive
                      ? 'border-l-4 border-[#8B4513] bg-[#F5EFEB] text-[#2C221E] shadow-2xs font-semibold'
                      : 'border-l-4 border-transparent text-[#635347] hover:bg-[#F5EFEB]/60 hover:text-[#2C221E]'
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <Icon
                      className={`h-4 w-4 transition-colors ${
                        isActive ? 'text-[#8B4513]' : 'text-[#8C7869] group-hover:text-[#635347]'
                      }`}
                    />
                    <span className="text-sm font-semibold">{item.label}</span>
                  </div>
                  <span
                    className={`mt-1 pl-6.5 text-[11px] leading-tight ${
                      isActive ? 'text-[#635347]' : 'text-[#8C7869]'
                    }`}
                  >
                    {item.description}
                  </span>
                </button>
              );
            })}
          </nav>

          {/* Study Corridor Reference Card */}
          <div className="mt-6 rounded-xl border border-[#EAE3D9] bg-[#FBF9F5] p-3 text-xs text-[#635347]">
            <div className="flex items-center gap-1.5 font-bold text-[#2C221E]">
              <Compass className="h-3.5 w-3.5 text-[#8B4513]" />
              <span>Operational Corridor</span>
            </div>
            <div className="mt-2 space-y-1 text-[11px] leading-relaxed">
              <div className="flex justify-between">
                <span className="text-[#8C7869]">Origin Barrage:</span>
                <span className="font-semibold text-[#2C221E]">Hathnikund (0.0 km)</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#8C7869]">Target Gauge:</span>
                <span className="font-semibold text-[#2C221E]">Delhi ORB (251.05 km)</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#8C7869]">Catchment Area:</span>
                <span className="font-semibold text-[#2C221E]">11,365 km² (D8 DEM)</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#8C7869]">CWC Survey Ref:</span>
                <span className="font-semibold text-[#2C221E]">11,112 km² (Lit)</span>
              </div>
            </div>
          </div>
        </div>

        {/* Footer: System Health & Provenance */}
        <div className="border-t border-[#EAE3D9] bg-[#FBF9F5] p-3">
          <div className="flex items-center justify-between text-xs">
            <span className="font-bold text-[#2C221E]">System Status</span>
            <span
              className={`flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-bold ${
                isLoading
                  ? 'bg-amber-100 text-amber-800'
                  : isConnected
                  ? 'bg-emerald-100 text-emerald-800'
                  : 'bg-red-100 text-red-800'
              }`}
            >
              {isLoading ? (
                <RefreshCw className="h-2.5 w-2.5 animate-spin" />
              ) : isConnected ? (
                <CheckCircle2 className="h-2.5 w-2.5" />
              ) : (
                <XCircle className="h-2.5 w-2.5" />
              )}
              {isLoading ? 'Checking' : isConnected ? 'Operational' : 'Offline'}
            </span>
          </div>

          {!isConnected && !isLoading && (
            <div className="mt-1">
              <button
                onClick={onRetry}
                className="flex items-center gap-1 text-[10px] text-[#8B4513] hover:underline"
              >
                <RefreshCw className="h-2.5 w-2.5" /> Reconnect backend
              </button>
            </div>
          )}

          <div className="mt-1.5 text-[10px] text-[#8C7869] leading-tight">
            {lastChecked ? (
              <span>Verified: {lastChecked.toLocaleTimeString()}</span>
            ) : (
              <span>Not verified</span>
            )}
          </div>

          <div className="mt-2 flex items-center justify-between text-[10px] text-[#8C7869] border-t border-[#EAE3D9]/60 pt-2">
            <span>PRAVAAH Engine</span>
            <span className="font-mono text-[#635347]">v0.1.0</span>
          </div>
        </div>
      </aside>
    </>
  );
};
