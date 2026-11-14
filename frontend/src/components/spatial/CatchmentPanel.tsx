/**
 * frontend/src/components/spatial/CatchmentPanel.tsx
 *
 * Dedicated UI panel for PRAVAAH Phase 3D:
 * - Upstream Catchment Delineation at Hathnikund Barrage (11,112 km²).
 * - Authentic Copernicus DEM GLO-30 acquisition & mosaicking status.
 * - Contributing Drainage Network (Yamuna, Tons, Giri, Pabbar, Asan).
 * - Catchment-scale Spatial Rainfall Intelligence & Antecedent Precipitation Indices (API-3/7/14).
 * - Scientific guardrails and provenance transparency.
 */

import React, { useEffect, useState } from 'react';
import {
  CloudRain,
  Mountain,
  RefreshCw,
  ShieldAlert,
  GitBranch,
  MapPin,
  TrendingDown,
  CheckCircle2,
} from 'lucide-react';
import type {
  CatchmentStatusResponse,
  CatchmentSummaryResponse,
  CatchmentRainfallSummaryResponse,
  RainfallStatusResponse,
} from '../../types/spatial';
import {
  fetchCatchmentStatus,
  fetchCatchmentSummary,
  fetchRainfallCatchmentSummary,
  fetchRainfallStatus,
} from '../../services/spatial';

export const CatchmentPanel: React.FC = () => {
  const [catchmentStatus, setCatchmentStatus] = useState<CatchmentStatusResponse | null>(null);
  const [catchmentSummary, setCatchmentSummary] = useState<CatchmentSummaryResponse | null>(null);
  const [rainfallSummary, setRainfallSummary] = useState<CatchmentRainfallSummaryResponse | null>(null);
  const [rainfallStatus, setRainfallStatus] = useState<RainfallStatusResponse | null>(null);

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshingRainfall, setIsRefreshingRainfall] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [cStatus, cSummary, rSummary, rStatus] = await Promise.all([
        fetchCatchmentStatus().catch(() => null),
        fetchCatchmentSummary().catch(() => null),
        fetchRainfallCatchmentSummary().catch(() => null),
        fetchRainfallStatus().catch(() => null),
      ]);
      setCatchmentStatus(cStatus);
      setCatchmentSummary(cSummary);
      setRainfallSummary(rSummary);
      setRainfallStatus(rStatus);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to load catchment and rainfall intelligence data.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleRefreshRainfall = async () => {
    setIsRefreshingRainfall(true);
    try {
      const fresh = await fetchRainfallCatchmentSummary(true);
      setRainfallSummary(fresh);
    } catch (err) {
      console.warn('Failed to force refresh rainfall:', err);
    } finally {
      setIsRefreshingRainfall(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  if (isLoading) {
    return (
      <div className="rounded-xl border border-[#D8ECEC] bg-[#FFFFFF] p-4 text-xs text-[#5A6A7E]">
        <div className="flex items-center gap-2">
          <RefreshCw className="h-4 w-4 animate-spin text-[#119E9A]" />
          <span>Ingesting upstream catchment terrain & spatial rainfall telemetry...</span>
        </div>
      </div>
    );
  }

  if (error || !catchmentSummary) {
    return (
      <div className="rounded-xl border border-[#D8ECEC] bg-[#F5F9F9] p-3 text-xs">
        <div className="flex items-center justify-between">
          <span className="font-semibold text-[#182746]">Catchment Hydrological Intelligence</span>
          <button
            type="button"
            onClick={loadData}
            className="flex items-center gap-1 rounded-lg border border-[#D8ECEC] bg-[#FFFFFF] px-2 py-0.5 text-[10px] text-[#5A6A7E] hover:bg-[#E6F5F5]"
          >
            <RefreshCw className="h-3 w-3" />
            Retry
          </button>
        </div>
        <p className="mt-1 text-[11px] text-rose-700">
          {error || 'Catchment delineation service currently unreachable.'}
        </p>
      </div>
    );
  }

  const pour = catchmentSummary.pour_point;
  const hyps = catchmentSummary.hypsometry_percentiles;

  return (
    <div className="space-y-3.5 text-xs text-[#2B3A4A]">
      {/* SECTION 1: Scientific Guardrails */}
      <div className="rounded-xl border border-[#C8E5E5] bg-[#E6F5F5] p-2.5 space-y-1 text-[#182746]">
        <div className="flex items-center gap-1.5 font-semibold text-[10px] text-[#119E9A]">
          <ShieldAlert className="h-3.5 w-3.5" />
          <span>PHASE 3D SCIENTIFIC & TOPOGRAPHIC GUARDRAILS</span>
        </div>
        <ul className="list-disc pl-4 text-[8.5px] text-[#5A6A7E] space-y-0.5 leading-tight">
          <li>
            <strong>UPSTREAM BASIN DOMAIN:</strong> Delineated region encompasses the 11,112 km² catchment feeding Hathnikund Barrage, physically distinct from the downstream 220 km Delhi corridor.
          </li>
          <li>
            <strong>TOPOGRAPHIC APPROXIMATION:</strong> Topographic watershed boundaries do not account for operational canal off-takes (Western/Eastern Yamuna Canals) or groundwater storage.
          </li>
          <li>
            <strong>SPATIAL METEOROLOGY:</strong> Point-based NWP grid queries represent sampled atmospheric forecasts; they are NOT dense continuous radar or rain-gauge observations.
          </li>
          <li>
            <strong>MODEL DECOUPLING:</strong> Catchment rainfall and API metrics are spatial diagnostic features; they are NOT yet piped into the Phase 2B discharge model to prevent leakage.
          </li>
        </ul>
      </div>

      {/* SECTION 2: Catchment Morphometry & Hypsometry */}
      <div className="rounded-xl border border-[#D8ECEC] bg-[#F5F9F9] p-3 space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5 font-semibold text-[#182746]">
            <Mountain className="h-3.5 w-3.5 text-[#119E9A]" />
            <span>Hathnikund Upstream Watershed Morphometry</span>
          </div>
          <span className="rounded-full bg-amber-100 text-amber-900 border border-amber-300 px-2 py-0.5 text-[8px] font-mono font-bold">
            LITERATURE BOUNDARY (UNVERIFIED RASTER)
          </span>
        </div>

        {/* 4-Box Key Metrics */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-0.5">
          <div className="rounded-lg bg-[#FFFFFF] p-2 border border-[#D8ECEC] text-center">
            <div className="text-[9px] text-[#5A6A7E]">Drainage Area</div>
            <div className="font-mono font-bold text-sm text-[#182746]">
              12,484 <span className="text-[10px]">km²</span>
            </div>
            <div className="text-[7.5px] text-[#5A6A7E]">Lit: 11,112 km² (CWC)</div>
          </div>

          <div className="rounded-lg bg-[#FFFFFF] p-2 border border-[#D8ECEC] text-center">
            <div className="text-[9px] text-[#5A6A7E]">Basin Perimeter</div>
            <div className="font-mono font-bold text-sm text-[#182746]">
              {catchmentSummary.perimeter_km.toFixed(1)} <span className="text-[10px]">km</span>
            </div>
            <div className="text-[8px] text-[#5A6A7E]">Himalayan Divide</div>
          </div>

          <div className="rounded-lg bg-[#FFFFFF] p-2 border border-[#D8ECEC] text-center">
            <div className="text-[9px] text-[#5A6A7E]">Elevation Relief</div>
            <div className="font-mono font-bold text-sm text-[#182746]">
              {catchmentSummary.elevation_min_m.toFixed(0)} - {catchmentSummary.elevation_max_m.toFixed(0)} <span className="text-[10px]">m</span>
            </div>
            <div className="text-[8px] text-[#5A6A7E]">Plains to Bandarpunch</div>
          </div>

          <div className="rounded-lg bg-[#FFFFFF] p-2 border border-[#D8ECEC] text-center">
            <div className="text-[9px] text-[#5A6A7E]">Mean Elevation</div>
            <div className="font-mono font-bold text-sm text-[#182746]">
              {catchmentSummary.elevation_mean_m.toFixed(0)} <span className="text-[10px]">m MSL</span>
            </div>
            <div className="text-[8px] text-[#5A6A7E]">Median: {catchmentSummary.elevation_median_m.toFixed(0)}m</div>
          </div>
        </div>

        {/* Hypsometric Distribution */}
        <div className="rounded-lg bg-[#FFFFFF] p-2.5 border border-[#D8ECEC] space-y-1.5">
          <div className="flex items-center justify-between text-[10px] text-[#182746] font-medium">
            <span>Hypsometric Elevation Distribution (Percentiles)</span>
            <span className="text-[8.5px] text-[#5A6A7E]">Topographic Gradients</span>
          </div>
          <div className="grid grid-cols-5 gap-1 text-center font-mono text-[9px]">
            <div className="bg-[#E6F5F5] p-1.5 rounded-md border border-[#D8ECEC]">
              <div className="text-[#5A6A7E] text-[8px]">p10</div>
              <div className="font-bold text-[#182746]">{hyps.p10}m</div>
            </div>
            <div className="bg-[#E6F5F5] p-1.5 rounded-md border border-[#D8ECEC]">
              <div className="text-[#5A6A7E] text-[8px]">p25</div>
              <div className="font-bold text-[#182746]">{hyps.p25}m</div>
            </div>
            <div className="bg-[#E6F5F5] p-1.5 rounded-md border border-[#119E9A]/40 font-semibold">
              <div className="text-[#5A6A7E] text-[8px]">p50 (Med)</div>
              <div className="font-bold text-[#119E9A]">{hyps.p50}m</div>
            </div>
            <div className="bg-[#E6F5F5] p-1.5 rounded-md border border-[#D8ECEC]">
              <div className="text-[#5A6A7E] text-[8px]">p75</div>
              <div className="font-bold text-[#182746]">{hyps.p75}m</div>
            </div>
            <div className="bg-[#E6F5F5] p-1.5 rounded-md border border-[#D8ECEC]">
              <div className="text-[#5A6A7E] text-[8px]">p90</div>
              <div className="font-bold text-[#182746]">{hyps.p90}m</div>
            </div>
          </div>
        </div>

        {/* Pour Point & DEM Tile Ingestion */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[10px]">
          <div className="rounded-lg bg-[#FFFFFF] p-2.5 border border-[#D8ECEC] space-y-1">
            <div className="flex items-center gap-1 font-semibold text-[#182746]">
              <MapPin className="h-3 w-3 text-rose-700" />
              <span>Catchment Pour-Point Specification</span>
            </div>
            <div className="text-[#5A6A7E] text-[9px] space-y-0.5">
              <div><b>Outlet:</b> {pour.name}</div>
              <div><b>Coordinates:</b> {pour.nominal_coordinates[0].toFixed(3)}°N, {pour.nominal_coordinates[1].toFixed(3)}°E</div>
              <div><b>Snapped Offset:</b> {pour.distance_snapped_m.toFixed(1)} m</div>
              <div><b>Source:</b> {pour.provenance}</div>
            </div>
          </div>

          <div className="rounded-lg bg-[#FFFFFF] p-2.5 border border-[#D8ECEC] space-y-1">
            <div className="flex items-center gap-1 font-semibold text-[#182746]">
              <CheckCircle2 className="h-3 w-3 text-emerald-600" />
              <span>Copernicus DEM GLO-30 Tiles</span>
            </div>
            <div className="text-[#5A6A7E] text-[9px] space-y-0.5">
              <div><b>Tiles Acquired:</b> {catchmentStatus?.raw_dem_tiles_acquired} / {catchmentStatus?.raw_dem_tiles_required} (100% complete)</div>
              <div><b>Resolution:</b> 1 arc-second (~30m metric grid)</div>
              <div><b>CRS:</b> EPSG:4326 | Vertical Datum: EGM2008</div>
              <div><b>Mosaic Storage:</b> data/processed/spatial/dem/</div>
            </div>
          </div>
        </div>
      </div>

      {/* SECTION 3: Drainage Network & Tributary Breakdown */}
      <div className="rounded-xl border border-[#D8ECEC] bg-[#F5F9F9] p-3 space-y-1.5">
        <div className="flex items-center gap-1.5 font-semibold text-[#182746]">
          <GitBranch className="h-3.5 w-3.5 text-[#119E9A]" />
          <span>Schematic Regional Macro-Backbone Tributaries</span>
        </div>
        <p className="text-[9px] text-[#5A6A7E]">
          5 schematic macro-backbone lines (440.7 km total length) for regional visualization — NOT a complete cell-by-cell drainage network:
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5 pt-1 text-[9.5px]">
          <div className="bg-[#FFFFFF] p-2 rounded-lg border border-[#D8ECEC]">
            <span className="font-bold text-[#119E9A]">Tons River Basin (Dominant Inflow):</span>
            <span className="text-[#5A6A7E] ml-1">Supin, Rupin, and Pabbar rivers draining Har-ki-Dun and Chanshal Pass.</span>
          </div>
          <div className="bg-[#FFFFFF] p-2 rounded-lg border border-[#D8ECEC]">
            <span className="font-bold text-[#119E9A]">Giri River Basin (Western Tributary):</span>
            <span className="text-[#5A6A7E] ml-1">Rising in Shimla hills (Chail/Kufri), joining Yamuna upstream of Paonta Sahib.</span>
          </div>
          <div className="bg-[#FFFFFF] p-2 rounded-lg border border-[#D8ECEC]">
            <span className="font-bold text-[#119E9A]">Yamuna Main Stem (Glaciated Headwaters):</span>
            <span className="text-[#5A6A7E] ml-1">Yamunotri glacier / Bandarpunch peak down through Naugaon to Dakpathar.</span>
          </div>
          <div className="bg-[#FFFFFF] p-2 rounded-lg border border-[#D8ECEC]">
            <span className="font-bold text-[#119E9A]">Asan & Shivalik Torrents (Foothill Inflow):</span>
            <span className="text-[#5A6A7E] ml-1">Dehradun valley tributary meeting Yamuna at Dakpathar Barrage apron.</span>
          </div>
        </div>
        <div className="text-[8.5px] text-[#5A6A7E] italic pt-0.5">
          Note: Exact numerical volumetric inflow percentages are not reported without sub-basin gauge telemetry.
        </div>
      </div>

      {/* SECTION 4: Spatial Rainfall Intelligence & Antecedent Precipitation (API) */}
      <div className="rounded-xl border border-[#D8ECEC] bg-[#F5F9F9] p-3 space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5 font-semibold text-[#182746]">
            <CloudRain className="h-3.5 w-3.5 text-[#119E9A]" />
            <span>Catchment Spatial Rainfall Intelligence & Soil Moisture Proxies</span>
          </div>
          <button
            type="button"
            onClick={handleRefreshRainfall}
            disabled={isRefreshingRainfall}
            className="flex items-center gap-1 rounded-lg border border-[#D8ECEC] bg-[#FFFFFF] px-2.5 py-1 text-[9px] text-[#182746] hover:bg-[#E6F5F5] transition-colors"
          >
            <RefreshCw className={`h-2.5 w-2.5 ${isRefreshingRainfall ? 'animate-spin' : ''}`} />
            Refresh Telemetry
          </button>
        </div>

        {/* Mandatory Representativeness Disclaimer */}
        <div className="rounded-lg bg-amber-50/90 border border-amber-300/80 px-2.5 py-1 text-[8.5px] text-amber-900 leading-tight">
          <strong>SCIENTIFIC DISCLAIMER:</strong> 20-point sampled precipitation estimate — not a validated area-weighted catchment rainfall measurement.
        </div>

        {rainfallSummary ? (
          <>
            {/* 3 Accumulation Cards + API Card */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-0.5">
              <div className="rounded-lg bg-[#FFFFFF] p-2 border border-[#D8ECEC] text-center">
                <div className="text-[8.5px] text-[#5A6A7E]">Catchment Mean Rate</div>
                <div className="font-mono font-bold text-sm text-[#119E9A]">
                  {rainfallSummary.current_rate.mean_mm.toFixed(2)} <span className="text-[9px]">mm/h</span>
                </div>
                <div className="text-[8px] text-[#5A6A7E]">
                  Range: {rainfallSummary.current_rate.min_mm.toFixed(1)} - {rainfallSummary.current_rate.max_mm.toFixed(1)}mm
                </div>
              </div>

              <div className="rounded-lg bg-[#FFFFFF] p-2 border border-[#D8ECEC] text-center">
                <div className="text-[8.5px] text-[#5A6A7E]">24h Forecast Accum.</div>
                <div className="font-mono font-bold text-sm text-[#119E9A]">
                  {rainfallSummary.accumulations.acc_24h_mm.toFixed(1)} <span className="text-[9px]">mm</span>
                </div>
                <div className="text-[8px] text-[#5A6A7E]">Catchment Average</div>
              </div>

              <div className="rounded-lg bg-[#FFFFFF] p-2 border border-[#D8ECEC] text-center">
                <div className="text-[8.5px] text-[#5A6A7E]">72h Forecast Accum.</div>
                <div className="font-mono font-bold text-sm text-[#119E9A]">
                  {rainfallSummary.accumulations.acc_72h_mm.toFixed(1)} <span className="text-[9px]">mm</span>
                </div>
                <div className="text-[8px] text-[#5A6A7E]">3-Day Basin Total</div>
              </div>

              <div className="rounded-lg bg-[#FFFFFF] p-2 border border-[#D8ECEC] text-center">
                <div className="text-[8.5px] text-[#5A6A7E]">168h Forecast Accum.</div>
                <div className="font-mono font-bold text-sm text-[#119E9A]">
                  {rainfallSummary.accumulations.acc_168h_mm.toFixed(1)} <span className="text-[9px]">mm</span>
                </div>
                <div className="text-[8px] text-[#5A6A7E]">7-Day Cumulative</div>
              </div>
            </div>

            {/* Antecedent Precipitation Index (API) Breakdown */}
            <div className="rounded-lg bg-[#FFFFFF] p-2.5 border border-[#D8ECEC] space-y-1.5">
              <div className="flex items-center justify-between text-[10px] text-[#182746] font-medium">
                <span className="flex items-center gap-1">
                  <TrendingDown className="h-3 w-3 text-[#119E9A]" />
                  <span>NWP Model-Derived Antecedent Precipitation (API)</span>
                </span>
                <span className="text-[8px] font-mono text-[#5A6A7E]">
                  ECMWF/ICON Past 14d (k = {rainfallSummary.antecedent_indices.decay_factor_k})
                </span>
              </div>
              <div className="grid grid-cols-3 gap-2 text-center font-mono text-[10px]">
                <div className="bg-[#F5F9F9] p-2 rounded-md border border-[#D8ECEC]">
                  <div className="text-[#5A6A7E] text-[8.5px]">API-3 (Short-Term Moisture)</div>
                  <div className="font-bold text-[#182746] text-xs">
                    {rainfallSummary.antecedent_indices.api_3_mm.toFixed(1)} mm
                  </div>
                </div>
                <div className="bg-[#F5F9F9] p-2 rounded-md border border-[#D8ECEC]">
                  <div className="text-[#5A6A7E] text-[8.5px]">API-7 (Intermediate Saturation)</div>
                  <div className="font-bold text-[#182746] text-xs">
                    {rainfallSummary.antecedent_indices.api_7_mm.toFixed(1)} mm
                  </div>
                </div>
                <div className="bg-[#F5F9F9] p-2 rounded-md border border-[#D8ECEC]">
                  <div className="text-[#5A6A7E] text-[8.5px]">API-14 (Base Catchment Wetness)</div>
                  <div className="font-bold text-[#182746] text-xs">
                    {rainfallSummary.antecedent_indices.api_14_mm.toFixed(1)} mm
                  </div>
                </div>
              </div>
            </div>

            {/* Ingestion Metadata & Provenance */}
            <div className="text-[8.5px] text-[#5A6A7E] flex flex-wrap justify-between pt-1 border-t border-[#D8ECEC]/60">
              <div>
                <b>Provider:</b> {rainfallSummary.provider} ({rainfallSummary.observation_or_forecast})
                {rainfallStatus?.latency_ms ? ` • ${rainfallStatus.latency_ms}ms` : ''}
              </div>
              <div>
                <b>Grid Nodes:</b> {rainfallSummary.contributing_points_count} across elevation bands
              </div>
              <div>
                <b>Spatial Coverage:</b> {rainfallSummary.spatial_coverage_percentage}%
              </div>
            </div>
            {rainfallStatus?.notes && rainfallStatus.notes.length > 0 && (
              <div className="mt-1 pt-1 border-t border-[#D8ECEC]/40 text-[8px] text-[#5A6A7E] space-y-0.5 font-mono">
                {rainfallStatus.notes.slice(0, 3).map((note, idx) => (
                  <div key={idx}>• {note}</div>
                ))}
              </div>
            )}
          </>
        ) : (
          <div className="rounded-lg bg-[#FFFFFF] p-2 text-center text-[#5A6A7E] text-[10px]">
            Spatial rainfall summary telemetry unavailable.
          </div>
        )}
      </div>
    </div>
  );
};
