import React from 'react';
import { X, Clock, ShieldCheck, Compass, Users, Sliders, ShieldAlert } from 'lucide-react';

export interface PlannedModuleInfo {
  title: string;
  phase: string;
  description: string;
  capabilities: string[];
}

const MODULE_DETAILS: Record<string, PlannedModuleInfo> = {
  'Risk Analysis': {
    title: 'Risk Analysis',
    phase: 'Phase 1',
    description:
      'Geospatial flood hazard classification integrating precipitation indices, hydrological gauges, and topographical elevation models.',
    capabilities: [
      'Digital Elevation Model (DEM) terrain processing',
      'Hydrological rainfall-runoff threshold modeling',
      'Multi-tier vulnerability zoning and classification',
    ],
  },
  'Impact Assessment': {
    title: 'Impact Assessment',
    phase: 'Phase 2',
    description:
      'Spatial demographic exposure analysis intersecting administrative census boundaries with modeled inundation danger zones.',
    capabilities: [
      'Demographic exposure and population density indexing',
      'Vulnerable demographic identification (elderly, children)',
      'Humanitarian resource requirement estimations',
    ],
  },
  'Shelters & Routes': {
    title: 'Shelters & Routes',
    phase: 'Phase 3',
    description:
      'Graph-based evacuation routing identifying candidate humanitarian shelters and unobstructed road networks.',
    capabilities: [
      'Safe shelter capacity tracking and availability',
      'NetworkX shortest-safe pathfinding algorithm',
      'Dynamic hazard avoidance road network weighting',
    ],
  },
  'Scenario Analysis': {
    title: 'Scenario Analysis',
    phase: 'Phase 4',
    description:
      'Scenario-based comparative simulation engine modeling extreme weather variations and infrastructure disruption.',
    capabilities: [
      'Precipitation surge and storm scenario modeling',
      'Embankment breach and floodwall failure simulations',
      'Baseline vs. stressed infrastructure comparison',
    ],
  },
};

const MODULE_ICONS: Record<string, React.ElementType> = {
  'Risk Analysis': ShieldAlert,
  'Impact Assessment': Users,
  'Shelters & Routes': Compass,
  'Scenario Analysis': Sliders,
};

interface PlannedModuleModalProps {
  moduleName: string | null;
  onClose: () => void;
}

export const PlannedModuleModal: React.FC<PlannedModuleModalProps> = ({
  moduleName,
  onClose,
}) => {
  if (!moduleName) return null;

  const info = MODULE_DETAILS[moduleName] || {
    title: moduleName,
    phase: 'Future Phase',
    description: 'This operational module is scheduled for future release.',
    capabilities: ['Architecture foundation established in Phase 0'],
  };

  const IconComponent = MODULE_ICONS[moduleName] || Clock;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-[#182746]/60 backdrop-blur-xs p-4"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      <div
        className="w-full max-w-md rounded-xl border border-[#D8ECEC] bg-[#FFFFFF] p-5 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between border-b border-[#D8ECEC] pb-3">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg border border-[#C8E5E5] bg-[#E6F5F5] text-[#119E9A]">
              <IconComponent className="h-4 w-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 id="modal-title" className="text-sm font-semibold text-[#182746]">
                  {info.title}
                </h3>
                <span className="rounded-full border border-[#C8E5E5] bg-[#E6F5F5] px-2 py-0.5 text-[10px] font-medium text-[#182746]">
                  {info.phase}
                </span>
              </div>
              <span className="text-[11px] text-[#5A6A7E]">Planned Module</span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1 text-[#5A6A7E] hover:bg-[#E6F5F5] hover:text-[#182746] transition-colors"
            aria-label="Close modal"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="mt-3.5 space-y-3">
          <p className="text-xs leading-relaxed text-[#2B3A4A]">
            {info.description}
          </p>

          <div className="rounded-lg border border-[#D8ECEC] bg-[#F5F9F9] p-3">
            <h4 className="text-[11px] font-semibold uppercase tracking-wider text-[#5A6A7E]">
              Planned Capabilities
            </h4>
            <ul className="mt-1.5 space-y-1">
              {info.capabilities.map((cap, idx) => (
                <li key={idx} className="flex items-start gap-1.5 text-xs text-[#2B3A4A]">
                  <span className="mt-1 h-1.5 w-1.5 rounded-full bg-[#119E9A] shrink-0" />
                  <span>{cap}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="flex items-center gap-2 rounded-lg border border-[#C8E5E5] bg-[#E6F5F5] p-2.5 text-[11px] text-[#182746]">
            <ShieldCheck className="h-4 w-4 text-[#119E9A] shrink-0" />
            <span>
              Zero-Fabrication Policy: This module is intentionally disabled until real datasets and models are validated.
            </span>
          </div>
        </div>

        <div className="mt-4 flex justify-end">
          <button
            onClick={onClose}
            className="rounded-lg border border-[#D8ECEC] bg-[#E6F5F5] px-3.5 py-1.5 text-xs font-medium text-[#182746] hover:bg-[#D8ECEC] transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
