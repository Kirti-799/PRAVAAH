import React from 'react';
import {
  Waves,
  Users,
  Compass,
  Sliders,
  ShieldCheck,
  Info,
} from 'lucide-react';
import { FeatureCard } from '../components/common/FeatureCard';
import { WorkspacePanel } from '../components/common/WorkspacePanel';
import { SystemStatusPanel } from '../components/common/SystemStatusPanel';
import type { HealthStatus } from '../types/api';

interface DashboardPageProps {
  isLoading: boolean;
  healthData: HealthStatus | null;
  error: string | null;
  lastChecked: Date | null;
  onRetry: () => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({
  isLoading,
  healthData,
  error,
  lastChecked,
  onRetry,
}) => {
  return (
    <div className="space-y-8 pb-12">
      {/* Overview / Welcome Banner */}
      <section className="relative overflow-hidden rounded-2xl border border-slate-800 bg-gradient-to-r from-slate-900 via-slate-900 to-slate-950 p-6 sm:p-8">
        <div className="relative z-10 max-w-3xl">
          <div className="inline-flex items-center gap-2 rounded-full border border-teal-500/30 bg-teal-500/10 px-3 py-1 text-xs font-medium text-teal-300">
            <ShieldCheck className="h-3.5 w-3.5" />
            <span>Phase 0 — Project Foundation Initialized</span>
          </div>

          <h2 className="mt-4 text-2xl font-bold tracking-tight text-white sm:text-3xl">
            PRAVAAH Disaster Intelligence Platform
          </h2>

          <p className="mt-2 text-sm leading-relaxed text-slate-300">
            Predictive Risk Assessment and Vulnerability Analysis for Adaptive Assistance & Humanitarian Response. 
            Phase 0 establishes the software foundation, API communication layer, and modular architecture.
          </p>

          <div className="mt-5 flex flex-wrap items-center gap-4 text-xs text-slate-400">
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-teal-400" />
              FastAPI Core Running
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-blue-400" />
              React + TypeScript Interface
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-purple-400" />
              Strict No-Fabrication Protocol
            </span>
          </div>
        </div>
      </section>

      {/* Real-time System Status Section */}
      <section>
        <SystemStatusPanel
          isLoading={isLoading}
          healthData={healthData}
          error={error}
          lastChecked={lastChecked}
          onRetry={onRetry}
        />
      </section>

      {/* Planned Feature Cards Grid */}
      <section>
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold text-white">
              Core Platform Capabilities
            </h2>
            <p className="text-xs text-slate-400">
              Four planned modules scheduled for sequential implementation in subsequent phases.
            </p>
          </div>
          <div className="hidden sm:flex items-center gap-1.5 text-xs text-slate-400">
            <Info className="h-3.5 w-3.5 text-teal-400" />
            <span>No fabricated risk statistics displayed</span>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          <FeatureCard
            title="Flood Risk Prediction"
            description="Geospatial flood hazard classification integrating precipitation, hydrological gauges, and topographical elevation models."
            icon={Waves}
            targetPhase="Phase 1 Module"
            statusLabel="Planned"
            capabilities={[
              'Hydrological elevation modeling',
              'Rainfall threshold indexing',
              'Multi-zone vulnerability classification',
            ]}
          />

          <FeatureCard
            title="Population Impact"
            description="Spatial demographic exposure analysis intersecting administrative census boundaries with inundation danger zones."
            icon={Users}
            targetPhase="Phase 2 Module"
            statusLabel="Planned"
            capabilities={[
              'Demographic exposure estimation',
              'Vulnerable group identification',
              'Resource requirement projections',
            ]}
          />

          <FeatureCard
            title="Shelters & Routes"
            description="Graph-based evacuation routing identifying candidate humanitarian shelters and unobstructed road networks."
            icon={Compass}
            targetPhase="Phase 3 Module"
            statusLabel="Planned"
            capabilities={[
              'Safe shelter capacity tracking',
              'NetworkX shortest-safe routing',
              'Hazard avoidance pathfinding',
            ]}
          />

          <FeatureCard
            title="What-If Simulation"
            description="Scenario-based comparative simulation engine modeling extreme weather variations and infrastructure disruption."
            icon={Sliders}
            targetPhase="Phase 4 Module"
            statusLabel="Planned"
            capabilities={[
              'Precipitation surge modeling',
              'Embankment breach scenarios',
              'Baseline vs stress test comparison',
            ]}
          />
        </div>
      </section>

      {/* Main Workspace Panel */}
      <section>
        <WorkspacePanel />
      </section>
    </div>
  );
};
