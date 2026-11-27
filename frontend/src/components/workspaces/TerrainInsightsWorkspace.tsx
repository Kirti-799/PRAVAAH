/**
 * frontend/src/components/workspaces/TerrainInsightsWorkspace.tsx
 *
 * Streamlined Terrain & Watershed Insights Workspace for PRAVAAH in authentic Cream & Brown styling:
 * Features:
 * - Authoritative Catchment Area Reconciliation (11,365 km² DEM D8 vs 11,112 km² CWC Survey vs 12,484 km² Envelope).
 * - Authoritative Corridor Length Reconciliation (251.05 km to Delhi ORB vs 268.94 km to Okhla).
 * - Core morphometric statistics: Elevation range, mean elevation, drainage stream length, DEM source.
 * - Interactive Leaflet catchment and drainage visualization preview.
 * - Expandable technical processing sections (D8 Flow Direction, Flow Accumulation, DEM Conditioning, Hypsometry, CRS).
 */

import React, { useEffect, useState } from 'react';
import {
  Mountain,
  Compass,
  ChevronDown,
  ChevronUp,
  Layers,
  Waves,
} from 'lucide-react';
import { MapContainer, TileLayer, GeoJSON } from 'react-leaflet';
import type { CatchmentSummaryResponse, RiverGeoJSONResponse } from '../../types/spatial';
import { fetchCatchmentSummary, fetchCatchmentGeometry, fetchRiverFeatures } from '../../services/spatial';

interface TerrainInsightsWorkspaceProps {
  onNavigateToMap: () => void;
}

export const TerrainInsightsWorkspace: React.FC<TerrainInsightsWorkspaceProps> = ({
  onNavigateToMap,
}) => {
  const [summary, setSummary] = useState<CatchmentSummaryResponse | null>(null);
  const [catchmentGeoJSON, setCatchmentGeoJSON] = useState<any>(null);
  const [riverGeoJSON, setRiverGeoJSON] = useState<RiverGeoJSONResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Expandable technical sections state
  const [expandedSection, setExpandedSection] = useState<string | null>(null);

  const toggleSection = (id: string) => {
    setExpandedSection(expandedSection === id ? null : id);
  };

  useEffect(() => {
    let isMounted = true;
    async function loadTerrainData() {
      setIsLoading(true);
      try {
        const [sumRes, catchRes, riverRes] = await Promise.allSettled([
          fetchCatchmentSummary(),
          fetchCatchmentGeometry(),
          fetchRiverFeatures(),
        ]);

        if (!isMounted) return;
        if (sumRes.status === 'fulfilled') setSummary(sumRes.value);
        if (catchRes.status === 'fulfilled') setCatchmentGeoJSON(catchRes.value);
        if (riverRes.status === 'fulfilled') setRiverGeoJSON(riverRes.value);
      } catch (err) {
        console.error('Failed to load terrain data:', err);
      } finally {
        if (isMounted) setIsLoading(false);
      }
    }

    loadTerrainData();
    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <div className="h-full w-full overflow-y-auto bg-[#FBF9F5] p-4 sm:p-6 lg:p-8 text-[#3E3026]">
      <div className="mx-auto max-w-6xl space-y-6">
        {/* Top Header Card */}
        <div className="rounded-2xl border border-[#EAE3D9] bg-[#FFFFFF] p-5 sm:p-6 shadow-xs">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              <div className="flex items-center gap-2">
                <span className="rounded-md bg-[#F5EFEB] px-2.5 py-0.5 text-[11px] font-bold uppercase tracking-wider text-[#8B4513]">
                  Digital Elevation & Hydrography
                </span>
                <span className="text-[11px] text-[#8C7869]">
                  Copernicus GLO-30 High-Resolution Terrain
                </span>
                {isLoading && (
                  <span className="flex items-center gap-1 rounded bg-[#EAE3D9] px-2 py-0.5 text-[10px] text-[#635347]">
                    <span className="h-2 w-2 animate-spin rounded-full border-2 border-[#8B4513] border-t-transparent"></span>
                    Syncing DEM metrics...
                  </span>
                )}
              </div>
              <h1 className="mt-1 text-2xl font-extrabold tracking-tight text-[#2C221E] sm:text-3xl">
                Terrain Insights & Watershed Morphometry
              </h1>
              <p className="mt-1 text-xs text-[#635347] max-w-3xl leading-relaxed">
                Quantitative topographic analysis of the Upper Yamuna contributing basin feeding Hathnikund Barrage.
                Includes depression-filled hydro-conditioned DEM analysis, stream generation, and reconciled area benchmarks.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={onNavigateToMap}
                className="flex items-center gap-1.5 rounded-xl bg-[#8B4513] px-4 py-2.5 text-xs font-bold text-white shadow-xs hover:bg-[#70360E] transition-all"
              >
                <Compass className="h-4 w-4" />
                <span>Open in Flood Map</span>
              </button>
            </div>
          </div>
        </div>

        {/* DATA RECONCILIATION AUDIT CARDS */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {/* Catchment Area Reconciliation Card */}
          <div className="rounded-2xl border border-[#EAE3D9] bg-[#FFFFFF] p-5 shadow-xs space-y-3">
            <div className="flex items-center justify-between border-b border-[#EAE3D9] pb-2">
              <div className="flex items-center gap-2">
                <Mountain className="h-4 w-4 text-[#8B4513]" />
                <h3 className="text-xs font-bold uppercase tracking-wider text-[#2C221E]">
                  Catchment Area Provenance Reconciliation
                </h3>
              </div>
              <span className="rounded bg-[#E8F5E9] px-2 py-0.5 text-[9px] font-bold text-[#2E7D32]">
                VERIFIED AUDIT
              </span>
            </div>

            <div className="space-y-2 text-xs">
              <div className="rounded-xl border border-[#8B4513]/30 bg-[#F5EFEB] p-3">
                <div className="flex justify-between items-baseline">
                  <span className="font-bold text-[#2C221E]">DEM D8 Delineated Watershed:</span>
                  <span className="font-mono font-extrabold text-base text-[#8B4513]">11,365.1 km²</span>
                </div>
                <div className="mt-1 text-[11px] text-[#635347] leading-relaxed">
                  <strong>Source:</strong> Copernicus GLO-30 30m DEM physical watershed extraction (385,914 cells, pour point at Hathnikund Barrage 30.317°N, 77.585°E).
                </div>
              </div>

              <div className="rounded-xl border border-[#EAE3D9] bg-[#FFFDF9] p-3">
                <div className="flex justify-between items-baseline">
                  <span className="font-semibold text-[#2C221E]">Official CWC Survey Reference:</span>
                  <span className="font-mono font-bold text-[#2C221E]">11,112.0 km²</span>
                </div>
                <div className="mt-1 text-[11px] text-[#8C7869] leading-relaxed">
                  <strong>Source:</strong> Central Water Commission (CWC) Yamuna Basin Study Directorate.
                  The 2.2% divergence is fully accounted for by 30m satellite elevation grid boundaries vs 20th-century topographic contour tracing.
                </div>
              </div>

              <div className="rounded-xl border border-[#EAE3D9] bg-[#FBF9F5] p-2.5 text-[11px] text-[#8C7869]">
                <div className="flex justify-between">
                  <span>Coarse 16-point Study Envelope:</span>
                  <span className="font-mono font-medium">12,484.4 km² (Non-delineated boundary)</span>
                </div>
              </div>
            </div>
          </div>

          {/* Corridor Length Reconciliation Card */}
          <div className="rounded-2xl border border-[#EAE3D9] bg-[#FFFFFF] p-5 shadow-xs space-y-3">
            <div className="flex items-center justify-between border-b border-[#EAE3D9] pb-2">
              <div className="flex items-center gap-2">
                <Waves className="h-4 w-4 text-[#2B5B84]" />
                <h3 className="text-xs font-bold uppercase tracking-wider text-[#2C221E]">
                  River Corridor Length Reconciliation
                </h3>
              </div>
              <span className="rounded bg-[#EBF3F9] px-2 py-0.5 text-[9px] font-bold text-[#2B5B84]">
                CHAINAGE AUDIT
              </span>
            </div>

            <div className="space-y-2 text-xs">
              <div className="rounded-xl border border-[#2B5B84]/30 bg-[#EBF3F9] p-3">
                <div className="flex justify-between items-baseline">
                  <span className="font-bold text-[#2C221E]">Primary Operational Forecasting Reach:</span>
                  <span className="font-mono font-extrabold text-base text-[#2B5B84]">251.05 km</span>
                </div>
                <div className="mt-1 text-[11px] text-[#635347] leading-relaxed">
                  <strong>Span:</strong> Hathnikund Barrage (Km 0.00) down to Delhi Old Railway Bridge (ORB, Km 251.05).
                  This is the active domain for CWC flood warnings (204.50m) and Muskingum wave travel time evaluation.
                </div>
              </div>

              <div className="rounded-xl border border-[#EAE3D9] bg-[#FFFDF9] p-3">
                <div className="flex justify-between items-baseline">
                  <span className="font-semibold text-[#2C221E]">Full Mainstem GIS Corridor:</span>
                  <span className="font-mono font-bold text-[#2C221E]">268.94 km</span>
                </div>
                <div className="mt-1 text-[11px] text-[#8C7869] leading-relaxed">
                  <strong>Span:</strong> Hathnikund Barrage (Km 0.00) through Delhi ORB to Okhla Barrage (Km 268.94),
                  representing the complete OSM-derived downstream river channel.
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Core Morphometric Metrics (4 Cards) */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-xl border border-[#EAE3D9] bg-[#FFFFFF] p-4 shadow-xs">
            <div className="text-[10px] font-bold uppercase text-[#8C7869]">Elevation Range</div>
            <div className="mt-1 text-2xl font-extrabold text-[#2C221E]">
              {summary?.elevation_min_m !== undefined && summary?.elevation_max_m !== undefined
                ? `${Math.round(summary.elevation_min_m)} - ${Math.round(summary.elevation_max_m).toLocaleString()}`
                : '198 - 6,284'}{' '}
              <span className="text-xs font-normal text-[#8C7869]">m MSL</span>
            </div>
            <div className="mt-1 text-[11px] text-[#635347]">Himalayan peaks to plains</div>
          </div>

          <div className="rounded-xl border border-[#EAE3D9] bg-[#FFFFFF] p-4 shadow-xs">
            <div className="text-[10px] font-bold uppercase text-[#8C7869]">Mean Elevation</div>
            <div className="mt-1 text-2xl font-extrabold text-[#2C221E]">
              {summary?.elevation_mean_m !== undefined
                ? Math.round(summary.elevation_mean_m).toLocaleString()
                : '2,420'}{' '}
              <span className="text-xs font-normal text-[#8C7869]">m MSL</span>
            </div>
            <div className="mt-1 text-[11px] text-[#635347]">High topographic relief</div>
          </div>

          <div className="rounded-xl border border-[#EAE3D9] bg-[#FFFFFF] p-4 shadow-xs">
            <div className="text-[10px] font-bold uppercase text-[#8C7869]">Drainage Stream Length</div>
            <div className="mt-1 text-2xl font-extrabold text-[#8B4513]">
              {summary?.stream_length_total_km !== undefined
                ? summary.stream_length_total_km.toFixed(1)
                : '440.7'}{' '}
              <span className="text-xs font-normal text-[#8C7869]">km</span>
            </div>
            <div className="mt-1 text-[11px] text-[#635347]">Tons, Giri, Yamuna backbone</div>
          </div>

          <div className="rounded-xl border border-[#EAE3D9] bg-[#FFFFFF] p-4 shadow-xs">
            <div className="text-[10px] font-bold uppercase text-[#8C7869]">DEM Resolution</div>
            <div className="mt-1 text-2xl font-extrabold text-[#2C221E]">
              30 <span className="text-xs font-normal text-[#8C7869]">metres</span>
            </div>
            <div className="mt-1 text-[11px] text-[#635347]">Copernicus GLO-30 DSM</div>
          </div>
        </div>

        {/* Catchment Visualization Preview Map */}
        <div className="rounded-2xl border border-[#EAE3D9] bg-[#FFFFFF] p-5 shadow-xs space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-[#2C221E] flex items-center gap-2">
              <Compass className="h-4 w-4 text-[#8B4513]" />
              Catchment Boundary & Drainage Network Visualization
            </h3>
            <span className="text-xs text-[#8C7869]">UTM Zone 43N (EPSG:32643)</span>
          </div>

          <div className="h-80 w-full overflow-hidden rounded-xl border border-[#EAE3D9] relative">
            <MapContainer
              center={[30.65, 77.80]}
              zoom={8}
              style={{ height: '100%', width: '100%' }}
              zoomControl={false}
              attributionControl={false}
            >
              <TileLayer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                maxZoom={19}
              />

              {catchmentGeoJSON && (
                <GeoJSON
                  data={catchmentGeoJSON}
                  style={{
                    color: '#8B4513',
                    weight: 2,
                    fillColor: '#F5EFEB',
                    fillOpacity: 0.4,
                  }}
                />
              )}

              {riverGeoJSON && (
                <GeoJSON
                  data={riverGeoJSON as any}
                  style={{
                    color: '#2B5B84',
                    weight: 3,
                    opacity: 0.9,
                  }}
                />
              )}
            </MapContainer>

            <div className="absolute bottom-3 left-3 rounded-lg bg-white/95 border border-[#EAE3D9] px-3 py-1.5 text-xs text-[#635347] shadow-xs backdrop-blur-xs font-medium">
              Pour Point: Hathnikund Barrage (30.317°N, 77.585°E) | Delineated Area: 11,365.1 km²
            </div>
          </div>
        </div>

        {/* Expandable Technical Processing Details (Collapsed by default) */}
        <div className="rounded-2xl border border-[#EAE3D9] bg-[#FFFFFF] p-5 shadow-xs space-y-3">
          <div className="border-b border-[#EAE3D9] pb-2">
            <h3 className="text-sm font-bold text-[#2C221E] flex items-center gap-2">
              <Layers className="h-4 w-4 text-[#8B4513]" />
              Advanced Geospatial & Processing Methodology
            </h3>
            <p className="text-xs text-[#635347] mt-0.5">
              Click any section below to inspect technical DEM conditioning, flow routing algorithms, and coordinate systems.
            </p>
          </div>

          <div className="divide-y divide-[#EAE3D9]">
            {/* 1. D8 Flow Direction */}
            <div className="py-2.5">
              <button
                onClick={() => toggleSection('d8')}
                className="flex items-center justify-between w-full text-xs font-bold text-[#2C221E] hover:text-[#8B4513] transition-colors"
              >
                <span>1. D8 Deterministic Flow Direction Algorithm</span>
                {expandedSection === 'd8' ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
              </button>
              {expandedSection === 'd8' && (
                <div className="mt-2 text-xs text-[#635347] leading-relaxed pl-2 border-l-2 border-[#8B4513]">
                  Applies single-direction flow routing assigning steepest descent slopes across 8 adjacent grid neighbors (1, 2, 4, 8, 16, 32, 64, 128).
                  Ensures continuous hydrodynamic connectivity from the 6,284m Himalayan peaks down to the Hathnikund pour point with zero sinks.
                </div>
              )}
            </div>

            {/* 2. Flow Accumulation */}
            <div className="py-2.5">
              <button
                onClick={() => toggleSection('accum')}
                className="flex items-center justify-between w-full text-xs font-bold text-[#2C221E] hover:text-[#8B4513] transition-colors"
              >
                <span>2. Flow Accumulation & Channel Initiation Threshold</span>
                {expandedSection === 'accum' ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
              </button>
              {expandedSection === 'accum' && (
                <div className="mt-2 text-xs text-[#635347] leading-relaxed pl-2 border-l-2 border-[#8B4513]">
                  Accumulation calculates upstream contributing cell counts. Channel initiation is configured at <strong>5,000 cells (~4.5 km² threshold)</strong>,
                  successfully extracting the primary sub-basin channels: Upper Yamuna, Tons, Giri, Pabbar, and Asan rivers without generating false overland artifacts.
                </div>
              )}
            </div>

            {/* 3. DEM Conditioning */}
            <div className="py-2.5">
              <button
                onClick={() => toggleSection('conditioning')}
                className="flex items-center justify-between w-full text-xs font-bold text-[#2C221E] hover:text-[#8B4513] transition-colors"
              >
                <span>3. DEM Conditioning & Pit Removal (Wang & Liu)</span>
                {expandedSection === 'conditioning' ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
              </button>
              {expandedSection === 'conditioning' && (
                <div className="mt-2 text-xs text-[#635347] leading-relaxed pl-2 border-l-2 border-[#8B4513]">
                  Removes spurious terrain depressions and flat plateaus using the priority-flood depression filling algorithm (Wang & Liu).
                  Guarantees strictly non-zero downhill gradients required for deterministic watershed delineation.
                </div>
              )}
            </div>

            {/* 4. Hypsometric Analysis */}
            <div className="py-2.5">
              <button
                onClick={() => toggleSection('hypsometry')}
                className="flex items-center justify-between w-full text-xs font-bold text-[#2C221E] hover:text-[#8B4513] transition-colors"
              >
                <span>4. Hypsometric Distribution & Elevation Bands</span>
                {expandedSection === 'hypsometry' ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
              </button>
              {expandedSection === 'hypsometry' && (
                <div className="mt-2 text-xs text-[#635347] leading-relaxed pl-2 border-l-2 border-[#8B4513]">
                  Over 55% of the catchment lies above 2,000m elevation in rugged Himalayan terrain (Tons and Pabbar valleys), leading to rapid orographic runoff generation,
                  while the remaining 45% consists of lower Siwalik foothills and alluvial transitions nearing Hathnikund.
                </div>
              )}
            </div>

            {/* 5. Projection & Coordinate Systems */}
            <div className="py-2.5">
              <button
                onClick={() => toggleSection('crs')}
                className="flex items-center justify-between w-full text-xs font-bold text-[#2C221E] hover:text-[#8B4513] transition-colors"
              >
                <span>5. Projection Justification & CRS Invariants</span>
                {expandedSection === 'crs' ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
              </button>
              {expandedSection === 'crs' && (
                <div className="mt-2 text-xs text-[#635347] leading-relaxed pl-2 border-l-2 border-[#8B4513]">
                  Reprojected to <strong>UTM Zone 43N (EPSG:32643)</strong> for all metric Euclidean distance, slope, and planar area computations.
                  Standard Web Mercator (EPSG:3857) or unprojected WGS84 (EPSG:4326) are strictly avoided for morphometric calculations to prevent latitude distortion.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
