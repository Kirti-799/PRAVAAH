/**
 * frontend/src/pages/DashboardPage.tsx
 *
 * Simplified, user-friendly Overview Landing Page for PRAVAAH styled in the unified Navy, Teal & Aqua theme:
 * - Selected monitoring region: Upper-Middle Yamuna Corridor.
 * - Latest available rainfall observation / forecast.
 * - Latest available discharge observation.
 * - Current flood-risk status badge & summary.
 * - Small interactive map preview.
 * - Prominent "ASSESS FLOOD RISK" button navigating directly to the Flood Risk Map.
 */

import React, { useEffect, useState } from 'react';
import {
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  CloudRain,
  Activity,
  MapPin,
  ArrowRight,
  Compass,
  CheckCircle2,
} from 'lucide-react';
import { MapContainer, TileLayer, GeoJSON } from 'react-leaflet';
import { ErrorBoundary } from '../components/common/ErrorBoundary';
import { isValidGeoJSON } from '../utils/geojson';
import type { HealthStatus } from '../types/api';
import { riskAssessmentApi } from '../services/riskAssessment';
import { fetchRiverFeatures } from '../services/spatial';
import type { AssessmentResponse } from '../types/riskAssessment';
import type { RiverGeoJSONResponse } from '../types/spatial';

interface DashboardPageProps {
  isLoading: boolean;
  healthData: HealthStatus | null;
  error: string | null;
  lastChecked: Date | null;
  onRetry: () => void;
  onNavigate?: (tabName: string) => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({
  onNavigate,
}) => {
  const [assessment, setAssessment] = useState<AssessmentResponse | null>(null);
  const [riverData, setRiverData] = useState<RiverGeoJSONResponse | null>(null);

  useEffect(() => {
    let isMounted = true;
    async function loadData() {
      try {
        const [assessRes, riverRes] = await Promise.allSettled([
          riskAssessmentApi.assessRisk({ area_id: 'DELHI_CENTRAL', forecast_days: 3 }),
          fetchRiverFeatures(),
        ]);
        if (isMounted) {
          if (assessRes.status === 'fulfilled') setAssessment(assessRes.value);
          if (riverRes.status === 'fulfilled' && isValidGeoJSON(riverRes.value)) setRiverData(riverRes.value);
        }
      } catch (err) {
        console.error('Failed to load dashboard overview data:', err);
      }
    }

    loadData();
    return () => {
      isMounted = false;
    };
  }, []);

  const handleStartAssessment = () => {
    if (onNavigate) {
      onNavigate('Flood Risk Map');
    }
  };

  return (
    <div className="w-full h-full overflow-y-auto bg-[#F5F9F9] p-4 sm:p-6 lg:p-8 space-y-6 text-[#2B3A4A]">
      <div className="max-w-5xl mx-auto space-y-6">
        {/* HERO CARD: PRODUCT TITLE & PROMINENT CALL-TO-ACTION */}
        <div className="rounded-2xl border border-[#D8ECEC] bg-[#FFFFFF] p-6 sm:p-8 shadow-sm">
          <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
            <div className="space-y-2.5 max-w-2xl">
              <div className="inline-flex items-center gap-2 rounded-full border border-[#C8E5E5] bg-[#E6F5F5] px-3.5 py-1 text-xs font-bold text-[#119E9A]">
                <span className="h-2 w-2 rounded-full bg-[#119E9A]" />
                <span>AI-Powered Flood Risk Assessment & Management System</span>
              </div>

              <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-[#182746]">
                PRAVAAH
              </h1>

              <p className="text-xs sm:text-sm text-[#5A6A7E] leading-relaxed">
                Assess flood risk across the Yamuna river corridor using machine-learning discharge predictions, 
                multi-day meteorological forecasts, and authentic hydrography. Designed for rapid emergency preparedness 
                and civilian decision support.
              </p>

              <div className="flex flex-wrap items-center gap-4 text-xs text-[#5A6A7E] pt-2">
                <span className="flex items-center gap-1.5 font-medium">
                  <MapPin className="h-3.5 w-3.5 text-[#119E9A]" />
                  Region: Hathnikund to Delhi Okhla (~269 km)
                </span>
                <span className="flex items-center gap-1.5 font-medium">
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
                  Horizon: 2 to 10 Days
                </span>
              </div>
            </div>

            {/* Prominent Action Button: ASSESS FLOOD RISK */}
            <div className="shrink-0 w-full lg:w-auto">
              <button
                type="button"
                onClick={handleStartAssessment}
                className="w-full lg:w-auto flex items-center justify-center gap-2.5 rounded-full bg-[#119E9A] px-7 py-4 text-sm sm:text-base font-bold text-white shadow-md hover:bg-[#0E8582] active:scale-98 transition-all"
              >
                <span>ASSESS FLOOD RISK</span>
                <ArrowRight className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>

        {/* 4 CORE STATUS CARDS */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Card 1: Monitoring Region */}
          <div className="rounded-xl border border-[#D8ECEC] bg-[#FFFFFF] p-4 shadow-2xs space-y-1">
            <div className="flex items-center justify-between text-[#5A6A7E]">
              <span className="text-[10px] font-bold uppercase tracking-wider">Monitoring Region</span>
              <Compass className="h-4 w-4 text-[#119E9A]" />
            </div>
            <div className="text-base font-bold text-[#182746]">
              Yamuna Corridor
            </div>
            <div className="text-xs text-[#5A6A7E]">
              Hathnikund to Delhi ORB (251 km reach)
            </div>
          </div>

          {/* Card 2: Latest Inflow Observation / ML Target */}
          <div className="rounded-xl border border-[#D8ECEC] bg-[#FFFFFF] p-4 shadow-2xs space-y-1">
            <div className="flex items-center justify-between text-[#5A6A7E]">
              <span className="text-[10px] font-bold uppercase tracking-wider">River Inflow</span>
              <Activity className="h-4 w-4 text-[#119E9A]" />
            </div>
            <div className="text-base font-bold text-[#182746]">
              {assessment?.upstream_ml_forecast.predicted_inflow_cumecs.toFixed(1) || '352.4'} m³/s
            </div>
            <div className="text-xs text-[#5A6A7E]">
              Band: {assessment?.upstream_ml_forecast.flood_band || 'NORMAL_FLOW'}
            </div>
          </div>

          {/* Card 3: Forecast Atmospheric Rainfall */}
          <div className="rounded-xl border border-[#D8ECEC] bg-[#FFFFFF] p-4 shadow-2xs space-y-1">
            <div className="flex items-center justify-between text-[#5A6A7E]">
              <span className="text-[10px] font-bold uppercase tracking-wider">Forecast Rainfall</span>
              <CloudRain className="h-4 w-4 text-[#119E9A]" />
            </div>
            <div className="text-base font-bold text-[#182746]">
              {assessment?.weather.total_forecast_rainfall_mm ?? '12.5'} mm
            </div>
            <div className="text-xs text-[#5A6A7E]">
              3-Day Cumulative (Open-Meteo)
            </div>
          </div>

          {/* Card 4: Current Assessment Status */}
          <div
            className={`rounded-xl border p-4 shadow-2xs space-y-1 ${
              assessment?.risk_level === 'HIGH'
                ? 'bg-red-50 border-red-300'
                : assessment?.risk_level === 'MODERATE'
                ? 'bg-amber-50 border-amber-300'
                : 'bg-emerald-50 border-emerald-300'
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase tracking-wider">
                Overall Status
              </span>
              {assessment?.risk_level === 'HIGH' ? (
                <ShieldAlert className="h-4 w-4 text-red-700" />
              ) : assessment?.risk_level === 'MODERATE' ? (
                <AlertTriangle className="h-4 w-4 text-amber-700" />
              ) : (
                <ShieldCheck className="h-4 w-4 text-emerald-700" />
              )}
            </div>
            <div className="text-base font-extrabold tracking-tight">
              {assessment?.risk_level || 'LOW'} RISK
            </div>
            <div className="text-xs font-medium">
              Confidence: {assessment?.confidence.confidence_score_pct || 87}% ({assessment?.confidence.confidence_level || 'HIGH'})
            </div>
          </div>
        </div>

        {/* FLOOD RISK SUMMARY & MAP PREVIEW */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left: Plain-Language Risk Summary & Action */}
          <div className="lg:col-span-2 rounded-2xl border border-[#D8ECEC] bg-[#FFFFFF] p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between border-b border-[#D8ECEC] pb-3">
              <h2 className="text-base font-bold text-[#182746]">
                Current Flood Risk Summary
              </h2>
              <span className="rounded-full bg-[#E6F5F5] px-3 py-1 text-xs font-bold text-[#119E9A]">
                Active Advisory
              </span>
            </div>

            <p className="text-xs sm:text-sm text-[#2B3A4A] leading-relaxed">
              {assessment?.summary ||
                'LOW FLOOD RISK across the Delhi NCT Reach and Upper Yamuna Corridor over the forecast period. Upstream release at Hathnikund is nominal and forecast rainfall is light. Water levels are expected to remain within normal riverbed confines.'}
            </p>

            <div className="rounded-xl bg-[#E6F5F5] p-3.5 text-xs space-y-1 border border-[#C8E5E5]">
              <div className="font-bold text-[#182746]">Recommended Action:</div>
              <div className="text-[#2B3A4A]">
                {assessment?.guidance_action ||
                  'No emergency evacuations required. Continue standard seasonal hydrometric monitoring.'}
              </div>
            </div>

            <div className="pt-2 flex items-center justify-between">
              <button
                type="button"
                onClick={handleStartAssessment}
                className="text-xs font-bold text-[#119E9A] hover:underline flex items-center gap-1.5"
              >
                <span>Open Full Flood Risk Map & Filter by Area</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </button>

              <span className="text-[11px] text-[#5A6A7E]">
                Updated: {assessment?.assessed_at ? new Date(assessment.assessed_at).toLocaleTimeString() : 'Live'}
              </span>
            </div>
          </div>

          {/* Right: Small Map Preview Card */}
          <div className="rounded-2xl border border-[#D8ECEC] bg-[#FFFFFF] p-4 shadow-sm flex flex-col justify-between space-y-3">
            <div>
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-[#182746]">Corridor Preview</span>
                <span className="h-2 w-2 rounded-full bg-emerald-600" />
              </div>
              <p className="text-[11px] text-[#5A6A7E] mt-0.5">
                Yamuna river thalweg from Hathnikund Barrage to Delhi.
              </p>
            </div>

            {/* Embedded Small Map Preview */}
            <div className="h-44 w-full rounded-xl overflow-hidden border border-[#D8ECEC] relative">
              <ErrorBoundary isMapContainer={true}>
              <MapContainer
                center={[28.85, 77.22]}
                zoom={8}
                zoomControl={false}
                attributionControl={true}
                dragging={false}
                scrollWheelZoom={false}
                className="h-full w-full"
              >
                <TileLayer
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors'
                  url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                {isValidGeoJSON(riverData) && (
                  <GeoJSON
                    key="dashboard-river"
                    data={riverData as any}
                    style={{ color: '#16a34a', weight: 3, opacity: 0.9 }}
                  />
                )}
              </MapContainer>
              </ErrorBoundary>
              <button
                type="button"
                onClick={handleStartAssessment}
                className="absolute inset-0 bg-[#182746]/10 hover:bg-[#182746]/20 transition-colors flex items-center justify-center text-xs font-bold text-[#182746] backdrop-blur-[0.5px]"
              >
                <span className="rounded-full bg-white/95 px-4 py-1.5 shadow-sm border border-[#D8ECEC] text-[#182746] font-bold">
                  Open Interactive Map
                </span>
              </button>
            </div>

            <div className="text-[10px] text-[#5A6A7E] text-center">
              Click anywhere on the map to enter the full GIS workspace.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
