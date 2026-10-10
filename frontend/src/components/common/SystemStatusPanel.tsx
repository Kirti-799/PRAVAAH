import React from 'react';
import {
  Server,
  Globe,
  RefreshCw,
  CheckCircle2,
  XCircle,
  Clock,
  ExternalLink,
  Code2,
} from 'lucide-react';
import type { HealthStatus } from '../../types/api';
import { getApiBaseUrl } from '../../services/api';

interface SystemStatusPanelProps {
  isLoading: boolean;
  healthData: HealthStatus | null;
  error: string | null;
  lastChecked: Date | null;
  onRetry: () => void;
}

export const SystemStatusPanel: React.FC<SystemStatusPanelProps> = ({
  isLoading,
  healthData,
  error,
  lastChecked,
  onRetry,
}) => {
  const isConnected = !isLoading && !error && healthData?.status === 'ok';
  const baseUrl = getApiBaseUrl();

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-5">
        <div>
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <Server className="h-5 w-5 text-teal-400" />
            System Architecture & Connection Status
          </h2>
          <p className="mt-1 text-xs text-slate-400">
            Real-time status of frontend and backend services in this environment.
          </p>
        </div>

        <button
          onClick={onRetry}
          disabled={isLoading}
          className="inline-flex items-center gap-2 rounded-lg bg-slate-800 px-3.5 py-2 text-xs font-medium text-slate-200 transition-colors hover:bg-slate-700 disabled:opacity-50 border border-slate-700 focus:outline-none focus:ring-2 focus:ring-teal-500"
          aria-label="Retry backend connection check"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? 'animate-spin text-teal-400' : ''}`} />
          <span>{isLoading ? 'Checking API...' : 'Retry Health Check'}</span>
        </button>
      </div>

      {/* Disconnected error alert */}
      {error && !isLoading && (
        <div className="mt-5 rounded-lg border border-rose-500/30 bg-rose-500/10 p-4">
          <div className="flex items-start gap-3">
            <XCircle className="h-5 w-5 text-rose-400 shrink-0 mt-0.5" />
            <div className="flex-1">
              <h4 className="text-xs font-semibold text-rose-300">
                Backend Connection Unavailable
              </h4>
              <p className="mt-1 text-xs text-rose-200/90 leading-relaxed">
                {error}
              </p>
              <div className="mt-3 flex flex-wrap items-center gap-2">
                <span className="text-[11px] text-slate-400">Target Endpoint:</span>
                <code className="rounded bg-slate-900 px-2 py-0.5 text-[11px] font-mono text-rose-300 border border-rose-900/50">
                  {baseUrl}/api/health
                </code>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Status Details Grid */}
      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* Frontend Status */}
        <div className="rounded-lg border border-slate-800 bg-slate-900/80 p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 flex items-center gap-1.5">
              <Globe className="h-4 w-4 text-teal-400" />
              Frontend
            </span>
            <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2 py-0.5 text-[11px] font-medium text-emerald-400 border border-emerald-500/20">
              <CheckCircle2 className="h-3 w-3" />
              Operational
            </span>
          </div>
          <div className="mt-3">
            <span className="text-xs text-slate-400">Framework</span>
            <p className="text-sm font-semibold text-white">React + TypeScript</p>
          </div>
          <div className="mt-2 text-[11px] font-mono text-slate-400">
            Vite Dev Server (Port 5173)
          </div>
        </div>

        {/* Backend Connectivity */}
        <div className="rounded-lg border border-slate-800 bg-slate-900/80 p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 flex items-center gap-1.5">
              <Server className="h-4 w-4 text-teal-400" />
              FastAPI Backend
            </span>
            {isLoading ? (
              <span className="inline-flex items-center gap-1 rounded-full bg-amber-500/10 px-2 py-0.5 text-[11px] font-medium text-amber-400 border border-amber-500/20">
                Checking...
              </span>
            ) : isConnected ? (
              <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2 py-0.5 text-[11px] font-medium text-emerald-400 border border-emerald-500/20">
                <CheckCircle2 className="h-3 w-3" />
                Connected
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 rounded-full bg-rose-500/10 px-2 py-0.5 text-[11px] font-medium text-rose-400 border border-rose-500/20">
                <XCircle className="h-3 w-3" />
                Disconnected
              </span>
            )}
          </div>
          <div className="mt-3">
            <span className="text-xs text-slate-400">Service Name</span>
            <p className="text-sm font-semibold text-white">
              {healthData?.service || (isLoading ? 'Detecting...' : 'Unavailable')}
            </p>
          </div>
          <div className="mt-2 text-[11px] font-mono text-slate-400 truncate" title={baseUrl}>
            {baseUrl}
          </div>
        </div>

        {/* Backend Version */}
        <div className="rounded-lg border border-slate-800 bg-slate-900/80 p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 flex items-center gap-1.5">
              <Code2 className="h-4 w-4 text-teal-400" />
              API Version
            </span>
            <span className="text-[11px] font-mono text-slate-400">Semantic</span>
          </div>
          <div className="mt-3">
            <span className="text-xs text-slate-400">Deployed Version</span>
            <p className="text-sm font-semibold text-white">
              {healthData?.version ? `v${healthData.version}` : isConnected ? 'v0.1.0' : 'Unknown'}
            </p>
          </div>
          <div className="mt-2 text-[11px] text-slate-400">
            FastAPI + Pydantic v2
          </div>
        </div>

        {/* Last Health Ping */}
        <div className="rounded-lg border border-slate-800 bg-slate-900/80 p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 flex items-center gap-1.5">
              <Clock className="h-4 w-4 text-teal-400" />
              Last Monitored
            </span>
            <span className="text-[11px] font-mono text-slate-400">GET /api/health</span>
          </div>
          <div className="mt-3">
            <span className="text-xs text-slate-400">Timestamp</span>
            <p className="text-sm font-semibold text-white">
              {lastChecked ? lastChecked.toLocaleTimeString() : 'Pending'}
            </p>
          </div>
          <div className="mt-2 text-[11px] text-slate-400">
            {isConnected ? (
              <a
                href={`${baseUrl}/api/docs`}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1 text-teal-400 hover:underline"
              >
                <span>View OpenAPI Docs</span>
                <ExternalLink className="h-3 w-3" />
              </a>
            ) : (
              <span>Docs available when online</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
