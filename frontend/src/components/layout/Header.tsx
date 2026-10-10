import React from 'react';
import { Menu, AlertTriangle, Loader2 } from 'lucide-react';
import type { HealthStatus } from '../../types/api';

interface HeaderProps {
  onMenuToggle: () => void;
  isLoading: boolean;
  healthData: HealthStatus | null;
  error: string | null;
  onRetry: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  onMenuToggle,
  isLoading,
  healthData,
  error,
  onRetry,
}) => {
  const isConnected = !isLoading && !error && healthData?.status === 'ok';

  return (
    <header className="sticky top-0 z-30 flex h-16 w-full items-center justify-between border-b border-slate-800 bg-slate-900/90 px-4 sm:px-6 backdrop-blur-md">
      <div className="flex items-center gap-3">
        <button
          onClick={onMenuToggle}
          className="rounded-lg p-2 text-slate-400 hover:bg-slate-800 hover:text-slate-200 lg:hidden focus:outline-none focus:ring-2 focus:ring-teal-500"
          aria-label="Toggle navigation menu"
        >
          <Menu className="h-5 w-5" />
        </button>

        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-lg font-semibold tracking-tight text-white sm:text-xl">
              PRAVAAH
            </h1>
            <span className="rounded bg-teal-500/10 px-2 py-0.5 text-[11px] font-medium tracking-wide text-teal-400 border border-teal-500/20">
              PHASE 0 FOUNDATION
            </span>
          </div>
          <p className="hidden text-xs text-slate-400 sm:block">
            Predictive Risk Assessment and Vulnerability Analysis for Adaptive Assistance & Humanitarian Response
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3 sm:gap-4">
        {/* Environment Badge */}
        <div className="hidden rounded-full border border-slate-700 bg-slate-800/80 px-2.5 py-1 text-xs font-medium text-slate-300 md:inline-flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-blue-400" />
          LOCAL DEVELOPMENT
        </div>

        {/* Backend Connection Status Badge */}
        <div
          className={`flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium transition-colors ${
            isLoading
              ? 'border-amber-500/30 bg-amber-500/10 text-amber-300'
              : isConnected
              ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300'
              : 'border-rose-500/30 bg-rose-500/10 text-rose-300'
          }`}
        >
          {isLoading ? (
            <>
              <Loader2 className="h-3.5 w-3.5 animate-spin text-amber-400" />
              <span>Checking API...</span>
            </>
          ) : isConnected ? (
            <>
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
              </span>
              <span className="hidden sm:inline">Backend:</span>
              <span className="font-semibold">Connected</span>
            </>
          ) : (
            <button
              onClick={onRetry}
              className="flex items-center gap-1 hover:underline focus:outline-none"
              title="Click to retry health check"
            >
              <AlertTriangle className="h-3.5 w-3.5 text-rose-400" />
              <span className="hidden sm:inline">Backend:</span>
              <span className="font-semibold">Disconnected</span>
              <span className="text-[10px] underline ml-1">(Retry)</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
