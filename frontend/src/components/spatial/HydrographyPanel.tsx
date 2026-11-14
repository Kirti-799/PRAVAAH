import React, { useEffect, useState } from 'react';
import {
  GitFork,
  Layers,
  MapPin,
  RefreshCw,
  ShieldAlert,
  Sliders,
  Info,
  Navigation,
} from 'lucide-react';

import type {
  HydrographyStatusResponse,
  RiverChainageResponse,
  ChainageStation,
} from '../../types/spatial';
import {
  fetchHydrographyStatus,
  fetchHydrographyChainage,
} from '../../services/spatial';

export const HydrographyPanel: React.FC = () => {
  const [status, setStatus] = useState<HydrographyStatusResponse | null>(null);
  const [chainage, setChainage] = useState<RiverChainageResponse | null>(null);
  const [selectedLayer, setSelectedLayer] = useState<string>('all');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadHydrography = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [statusData, chainageData] = await Promise.all([
        fetchHydrographyStatus(),
        fetchHydrographyChainage(5.0).catch(() => null),
      ]);
      setStatus(statusData);
      setChainage(chainageData);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to load river hydrography metadata.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadHydrography();
  }, []);

  if (isLoading) {
    return (
      <div className="rounded-xl border border-[#D8ECEC] bg-[#FFFFFF] p-4 text-xs text-[#5A6A7E]">
        <div className="flex items-center gap-2">
          <RefreshCw className="h-4 w-4 animate-spin text-[#119E9A]" />
          <span>Validating river hydrography, NetworkX topology & chainage stations...</span>
        </div>
      </div>
    );
  }

  if (error || !status) {
    return (
      <div className="rounded-xl border border-[#D8ECEC] bg-[#F5F9F9] p-3 text-xs">
        <div className="flex items-center justify-between">
          <span className="font-semibold text-[#182746]">River Hydrography & Network (Phase 3B)</span>
          <button
            type="button"
            onClick={loadHydrography}
            className="flex items-center gap-1 rounded-lg border border-[#D8ECEC] bg-[#FFFFFF] px-2 py-0.5 text-[10px] text-[#5A6A7E] hover:bg-[#E6F5F5]"
          >
            <RefreshCw className="h-3 w-3" />
            Retry
          </button>
        </div>
        <p className="mt-1 text-[11px] text-rose-700">
          {error || 'Hydrography service currently unreachable.'}
        </p>
      </div>
    );
  }

  const isAvailable = status.hydrography_availability === 'AVAILABLE';
  const report = status.processing_report;

  return (
    <div className="space-y-3 text-[#2B3A4A]">
      {/* SECTION 1: Status & Repository Ingestion Bar */}
      <div className="rounded-xl border border-[#D8ECEC] bg-[#F5F9F9] p-3 space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <GitFork className="h-4 w-4 text-[#119E9A]" />
            <span className="font-semibold text-[#182746] text-xs">
              Yamuna River Hydrography & Network
            </span>
          </div>
          <div className="flex items-center gap-1.5">
            <span
              className={`rounded-full px-2 py-0.5 text-[8px] font-mono font-semibold ${
                isAvailable
                  ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                  : 'bg-rose-100 text-rose-800 border border-rose-300'
              }`}
            >
              {status.hydrography_availability}
            </span>
            <button
              type="button"
              onClick={loadHydrography}
              className="flex items-center gap-1 rounded-md border border-[#D8ECEC] bg-[#FFFFFF] px-1.5 py-0.5 text-[9px] text-[#5A6A7E] hover:bg-[#E6F5F5]"
              title="Refresh hydrography audit"
            >
              <RefreshCw className="h-2.5 w-2.5" />
            </button>
          </div>
        </div>

        {!isAvailable ? (
          <div className="rounded-lg border border-dashed border-[#D8ECEC] bg-[#FFFFFF] p-2.5 space-y-1.5 text-[10px]">
            <div className="flex items-center gap-1.5 text-amber-800 font-medium">
              <Info className="h-3.5 w-3.5 shrink-0 text-amber-700" />
              <span>Vector Hydrography Unacquired in Local Folders</span>
            </div>
            <p className="text-[9px] text-[#5A6A7E] leading-tight">
              In adherence to PRAVAAH scientific standards, synthetic river polylines are not fabricated.
              Candidate datasets (OSM waterways or CWC reach vectors) can be placed in:
              <br />
              <code className="font-mono text-[8px] text-[#119E9A] bg-[#F5F9F9] px-1.5 py-0.5 rounded border border-[#D8ECEC] inline-block mt-0.5">
                data/raw/spatial/hydrography/osm_yamuna_waterways.geojson
              </code>
            </p>
            {status.acquisition_guide && (
              <div className="text-[8.5px] text-[#2B3A4A] space-y-0.5 pt-1 border-t border-[#D8ECEC]">
                <div className="font-semibold text-[#182746]">Target Coverage:</div>
                <div className="text-[#5A6A7E]">{status.acquisition_guide.required_coverage}</div>
              </div>
            )}
          </div>
        ) : (
          report && (
            <div className="space-y-1.5 text-[10px]">
              <div className="flex items-center justify-between text-[#182746] text-[9.5px]">
                <span className="font-mono font-medium">{report.source_file}</span>
                <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[8px] font-mono text-emerald-800 border border-emerald-300">
                  {report.validation_status}
                </span>
              </div>

              <div className="grid grid-cols-4 gap-1 text-center text-[9px]">
                <div className="rounded-md bg-[#FFFFFF] p-1 border border-[#D8ECEC]">
                  <div className="text-[#5A6A7E] text-[8px]">Network Length</div>
                  <div className="font-mono font-semibold text-[#182746]">
                    {report.total_network_length_km.toFixed(1)} km
                  </div>
                </div>
                <div className="rounded-md bg-[#FFFFFF] p-1 border border-[#D8ECEC]">
                  <div className="text-[#5A6A7E] text-[8px]">Valid Features</div>
                  <div className="font-mono font-semibold text-[#182746]">
                    {report.valid_features_count}
                  </div>
                </div>
                <div className="rounded-md bg-[#FFFFFF] p-1 border border-[#D8ECEC]">
                  <div className="text-[#5A6A7E] text-[8px]">Main Channel</div>
                  <div className="font-mono font-semibold text-[#182746]">
                    {report.main_channel_length_km.toFixed(1)} km
                  </div>
                </div>
                <div className="rounded-md bg-[#FFFFFF] p-1 border border-[#D8ECEC]">
                  <div className="text-[#5A6A7E] text-[8px]">Continuity</div>
                  <div className={`font-mono font-semibold text-[8px] ${
                    report.main_channel_continuity === 'CONTINUOUS'
                      ? 'text-emerald-700'
                      : 'text-amber-700'
                  }`}>
                    {report.main_channel_continuity}
                  </div>
                </div>
              </div>
            </div>
          )
        )}
      </div>

      {/* SECTION 2: Classified Hydrographic Layers */}
      {isAvailable && report && (
        <div className="rounded-xl border border-[#D8ECEC] bg-[#FFFFFF] p-3 space-y-2 text-[10px]">
          <div className="flex items-center justify-between">
            <span className="flex items-center gap-1 font-semibold text-[#182746] text-[11px]">
              <Layers className="h-3.5 w-3.5 text-[#119E9A]" />
              Classified Hydrographic Layers (EPSG:32643)
            </span>
            <span className="text-[8.5px] text-[#5A6A7E]">
              UTM Zone 43N Metric
            </span>
          </div>

          {/* Layer Filter Buttons */}
          <div className="flex gap-1 overflow-x-auto pb-0.5 text-[8.5px]">
            <button
              type="button"
              onClick={() => setSelectedLayer('all')}
              className={`px-2 py-0.5 rounded-full font-medium transition-colors ${
                selectedLayer === 'all'
                  ? 'bg-[#119E9A] text-white'
                  : 'bg-[#F5F9F9] text-[#182746] hover:bg-[#E6F5F5] border border-[#D8ECEC]'
              }`}
            >
              All Layers
            </button>
            {Object.keys(report.features_by_class).map((k) => (
              <button
                key={k}
                type="button"
                onClick={() => setSelectedLayer(k)}
                className={`px-2 py-0.5 rounded-full font-medium uppercase transition-colors ${
                  selectedLayer === k
                    ? 'bg-[#119E9A] text-white'
                    : 'bg-[#F5F9F9] text-[#182746] hover:bg-[#E6F5F5] border border-[#D8ECEC]'
                }`}
              >
                {k.replace('_', ' ')}
              </button>
            ))}
          </div>

          <div className="grid grid-cols-2 gap-1.5">
            {Object.entries(report.features_by_class)
              .filter(([clsName]) => selectedLayer === 'all' || selectedLayer === clsName)
              .map(([clsName, count]) => {
                const km = report.length_by_class_km[clsName] || 0;
                const formattedName = clsName.replace('_', ' ').toUpperCase();
                return (
                  <div
                    key={clsName}
                    className="rounded-lg border border-[#D8ECEC] bg-[#F5F9F9] p-2 text-[9px] space-y-0.5"
                  >
                    <div className="flex items-center justify-between font-medium text-[#182746]">
                      <span>{formattedName}</span>
                      <span className="font-mono text-[#119E9A] font-semibold">{Number(count)} segs</span>
                    </div>
                    <div className="text-[8px] text-[#5A6A7E]">
                      Linear Length: <strong>{km.toFixed(1)} km</strong>
                    </div>
                  </div>
                );
              })}
          </div>
        </div>
      )}

      {/* SECTION 3: NetworkX Topology & Connectivity */}
      {isAvailable && report?.topology_summary && (
        <div className="rounded-xl border border-[#D8ECEC] bg-[#F5F9F9] p-3 space-y-2 text-[10px]">
          <div className="flex items-center justify-between">
            <span className="flex items-center gap-1 font-semibold text-[#182746] text-[11px]">
              <Sliders className="h-3.5 w-3.5 text-[#119E9A]" />
              Network Topology Analysis (NetworkX)
            </span>
            <span className="rounded-full bg-[#E6F5F5] text-[#182746] border border-[#C8E5E5] px-2 py-0.5 text-[8px] font-mono">
              Undirected Reach Graph
            </span>
          </div>

          <div className="grid grid-cols-3 gap-1.5 text-center text-[9px]">
            <div className="rounded-md bg-[#FFFFFF] p-1 border border-[#D8ECEC]">
              <div className="text-[#5A6A7E] text-[8px]">Nodes / Edges</div>
              <div className="font-mono font-semibold text-[#182746]">
                {report.topology_summary.total_nodes} / {report.topology_summary.total_edges}
              </div>
            </div>
            <div className="rounded-md bg-[#FFFFFF] p-1 border border-[#D8ECEC]">
              <div className="text-[#5A6A7E] text-[8px]">Connected Comps</div>
              <div className="font-mono font-semibold text-[#182746]">
                {report.topology_summary.connected_components_count}
              </div>
            </div>
            <div className="rounded-md bg-[#FFFFFF] p-1 border border-[#D8ECEC]">
              <div className="text-[#5A6A7E] text-[8px]">Confluences (deg≥3)</div>
              <div className="font-mono font-semibold text-[#182746]">
                {report.topology_summary.confluence_junctions_count}
              </div>
            </div>
          </div>

          <div className="rounded-md bg-[#FFFFFF] p-2 border border-[#D8ECEC] text-[8.5px] text-[#2B3A4A] space-y-0.5">
            <div className="flex justify-between">
              <span>Dead-end Terminals: <strong>{report.topology_summary.dead_end_nodes_count}</strong></span>
              <span>
                Braids / Cycles: <strong>{report.topology_summary.has_cycles_or_braids ? `${report.topology_summary.cycles_count} loops` : 'None detected'}</strong>
              </span>
            </div>
            <div className="text-[8px] text-[#5A6A7E] italic pt-0.5">
              Flow Direction Guard: Hydraulic connectivity is undirected; flow vectors are NOT assumed from digitization direction alone.
            </div>
          </div>
        </div>
      )}

      {/* SECTION 4: River Chainage & Stationing (Hathnikund to Delhi) */}
      {isAvailable && (report?.chainage_summary || chainage) && (() => {
        const chainageReport = report?.chainage_summary || chainage;
        if (!chainageReport) return null;
        return (
        <div className="rounded-xl border border-[#D8ECEC] bg-[#FFFFFF] p-3 space-y-2 text-[10px]">
          <div className="flex items-center justify-between">
            <span className="flex items-center gap-1 font-semibold text-[#182746] text-[11px]">
              <Navigation className="h-3.5 w-3.5 text-[#119E9A]" />
              Downstream River Chainage (Stationing)
            </span>
            <span className={`rounded-full px-2 py-0.5 text-[8px] font-mono font-semibold ${
              chainageReport.status === 'AVAILABLE'
                ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                : 'bg-rose-100 text-rose-800 border border-rose-300'
            }`}>
              {chainageReport.status}
            </span>
          </div>

          {chainageReport.status === 'AVAILABLE' ? (
            <div className="space-y-1.5">
              <div className="flex justify-between text-[9px] text-[#5A6A7E] border-b border-[#D8ECEC] pb-1">
                <span>Origin: <strong>{chainageReport.origin_point_name}</strong></span>
                <span>Total Reach: <strong>{chainageReport.total_chainage_km.toFixed(1)} km</strong></span>
              </div>

              <div className="max-h-36 overflow-y-auto space-y-1 pr-1">
                {chainageReport.stations.map((stn: ChainageStation) => (
                  <div
                    key={stn.station_id}
                    className={`rounded-md p-1.5 text-[8.5px] flex items-center justify-between border ${
                      stn.is_landmark
                        ? 'bg-[#E6F5F5] border-[#C8E5E5] font-semibold text-[#182746]'
                        : 'bg-[#FFFFFF] border-[#D8ECEC] text-[#2B3A4A]'
                    }`}
                  >
                    <div className="flex items-center gap-1">
                      <MapPin className="h-2.5 w-2.5 text-[#119E9A]" />
                      <span>{stn.landmark_name || stn.reach_name}</span>
                    </div>
                    <div className="font-mono text-[8px] text-[#5A6A7E]">
                      km {stn.chainage_km.toFixed(1)} ({stn.latitude.toFixed(3)}°N, {stn.longitude.toFixed(3)}°E)
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <p className="text-[8.5px] text-rose-700 italic">
              Chainage generation refused: channel continuity exhibits gaps preventing rigorous distance accumulation.
            </p>
          )}
        </div>
        );
      })()}

      {/* SECTION 5: Scientific Guardrails Notice */}
      <div className="rounded-xl border border-[#C8E5E5] bg-[#E6F5F5] p-2.5 space-y-1 text-[9px] text-[#182746]">
        <div className="flex items-center gap-1.5 font-semibold text-[#119E9A]">
          <ShieldAlert className="h-3.5 w-3.5 shrink-0" />
          <span>Scientific & Geospatial Guardrails Enforced (Phase 3B)</span>
        </div>
        <ul className="list-disc pl-3 text-[8px] text-[#5A6A7E] space-y-0.5 leading-tight">
          <li>River centerlines denote channel thalwegs; they do NOT delineate flood inundation extents or water depths.</li>
          <li>Topological reaches are undirected; downstream flow orientation is not inferred without hydrodynamic validation.</li>
          <li>Mapped embankments/bunds reflect planimetric alignment only; certified crest elevations and flood barrier integrity are unverified.</li>
        </ul>
      </div>
    </div>
  );
};
