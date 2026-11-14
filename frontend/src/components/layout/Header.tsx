/**
 * frontend/src/components/layout/Header.tsx
 *
 * Unified Application Header for PRAVAAH in authentic Cream & Brown styling:
 * - Deep Espresso (#2C221E) background with subtle Dark Brown (#3E3026) border.
 * - Warm Saddle Brown (#8B4513) icon accents.
 * - Warm Cream (#FFFDF9) typography.
 * - Unified Project Identity: PRAVAAH — Yamuna Flood Intelligence & Decision Support.
 * - Study Region: Hathnikund Barrage to Delhi Old Railway Bridge.
 */

import React from 'react';
import { Menu, RefreshCw, CheckCircle2, XCircle, Waves, ArrowLeft } from 'lucide-react';
import type { HealthStatus } from '../../types/api';

interface HeaderProps {
  onMenuToggle: () => void;
  isLoading: boolean;
  healthData: HealthStatus | null;
  error: string | null;
  onRetry: () => void;
  onBackToLanding?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  onMenuToggle,
  isLoading,
  healthData,
  error,
  onRetry,
  onBackToLanding,
}) => {
  const isConnected = !isLoading && !error && healthData?.status === 'ok';

  return (
    <header className="flex h-14 w-full items-center justify-between border-b border-[#3E3026] bg-[#2C221E] px-4 sm:px-6 text-xs text-[#FFFDF9] select-none shadow-xs z-30">
      {/* Left: Mobile Toggle, Optional Back & Product Identity */}
      <div className="flex items-center gap-3">
        <button
          onClick={onMenuToggle}
          className="rounded p-1 text-[#EAE3D9] hover:bg-[#3E3026] hover:text-white lg:hidden"
          aria-label="Toggle navigation menu"
        >
          <Menu className="h-5 w-5" />
        </button>

        {onBackToLanding && (
          <button
            type="button"
            onClick={onBackToLanding}
            className="flex items-center gap-1.5 rounded-full border border-[#4A3B33] bg-[#3E3026] px-3 py-1 text-xs font-semibold text-[#EAE3D9] hover:bg-[#8B4513] hover:text-white transition-all shadow-2xs"
            title="Return to Landing Page"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Landing Page</span>
          </button>
        )}

        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#8B4513] text-white shadow-xs">
            <Waves className="h-4 w-4" />
          </div>
          <div>
            <div className="flex items-baseline gap-2">
              <span className="text-base font-extrabold tracking-tight text-[#FFFDF9]">
                PRAVAAH
              </span>
              <span className="hidden lg:inline text-xs font-medium text-[#EAE3D9]/90">
                | Yamuna Flood Intelligence & Decision Support
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Right: Monitoring Corridor & Live System Status */}
      <div className="flex items-center gap-2 sm:gap-3">
        {/* Monitoring Region Badge */}
        <div className="hidden rounded-full border border-[#4A3B33] bg-[#382B24] px-3 py-1 text-xs text-[#EAE3D9] md:flex items-center gap-1.5 font-medium">
          <span className="text-[#D8CEBE]">Study Region:</span>
          <span className="font-semibold text-white">Hathnikund to Delhi ORB (251 km)</span>
        </div>

        {/* Backend Connection Badge */}
        <div
          className={`flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-semibold transition-colors ${
            isLoading
              ? 'border-amber-400/40 bg-amber-950/60 text-amber-200'
              : isConnected
              ? 'border-emerald-500/40 bg-emerald-950/60 text-emerald-300'
              : 'border-red-400/40 bg-red-950/60 text-red-300'
          }`}
          title={
            isConnected
              ? `Connected to ${healthData?.service || 'PRAVAAH API'}`
              : error || 'Service offline'
          }
        >
          {isLoading ? (
            <RefreshCw className="h-3 w-3 animate-spin text-amber-300" />
          ) : isConnected ? (
            <CheckCircle2 className="h-3 w-3 text-emerald-400" />
          ) : (
            <XCircle className="h-3 w-3 text-red-400" />
          )}

          <span className="hidden sm:inline">
            {isLoading
              ? 'Connecting...'
              : isConnected
              ? 'API Active'
              : 'Offline'}
          </span>
        </div>

        {/* Manual Reconnect Action */}
        {!isConnected && (
          <button
            onClick={onRetry}
            disabled={isLoading}
            className="flex items-center gap-1 rounded border border-[#4A3B33] bg-[#3E3026] px-2.5 py-1 text-xs font-medium text-[#EAE3D9] hover:bg-[#8B4513] hover:text-white transition-colors disabled:opacity-50"
            title="Retry connection"
          >
            <RefreshCw className={`h-3 w-3 ${isLoading ? 'animate-spin' : ''}`} />
            <span className="hidden sm:inline">Retry</span>
          </button>
        )}
      </div>
    </header>
  );
};
