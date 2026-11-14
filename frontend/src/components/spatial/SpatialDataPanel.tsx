import React, { useEffect, useState } from 'react';
import {
  Layers,
  Mountain,
  RefreshCw,
  ShieldAlert,
  Database,
  Compass,
  GitFork,
} from 'lucide-react';

import { HydrographyPanel } from './HydrographyPanel';
import { CatchmentPanel } from './CatchmentPanel';

import type {
  SpatialInventoryResponse,
  StudyAreaMetadataResponse,
  DEMStatusResponse,
  TerrainSummaryResponse,
  RiverNetworkStatusResponse,
} from '../../types/spatial';
import {
  fetchSpatialInventory,
  fetchStudyAreaMetadata,
  fetchDEMStatus,
  fetchTerrainSummary,
  fetchRiverStatus,
} from '../../services/spatial';

export const SpatialDataPanel: React.FC = () => {
  const [inventory, setInventory] = useState<SpatialInventoryResponse | null>(null);
  const [studyArea, setStudyArea] = useState<StudyAreaMetadataResponse | null>(null);
  const [demStatus, setDemStatus] = useState<DEMStatusResponse | null>(null);
  const [terrain, setTerrain] = useState<TerrainSummaryResponse | null>(null);
  const [riverStatus, setRiverStatus] = useState<RiverNetworkStatusResponse | null>(null);
  const [activeSpatialTab, setActiveSpatialTab] = useState<'catchment' | 'hydrography' | 'terrain'>('catchment');

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadSpatialData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [invData, saData, demData, terrainData, riverData] = await Promise.all([
        fetchSpatialInventory(),
        fetchStudyAreaMetadata(),
        fetchDEMStatus(),
        fetchTerrainSummary().catch(() => null),
        fetchRiverStatus().catch(() => null),
      ]);
      setInventory(invData);
      setStudyArea(saData);
      setDemStatus(demData);
      setTerrain(terrainData);
      setRiverStatus(riverData);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to load spatial data infrastructure metadata.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadSpatialData();
  }, []);

  if (isLoading) {
    return (
      <div className="rounded-xl border border-[#D8ECEC] bg-[#FFFFFF] p-4 text-xs text-[#5A6A7E]">
        <div className="flex items-center gap-2">
          <RefreshCw className="h-4 w-4 animate-spin text-[#119E9A]" />
          <span>Auditing spatial data infrastructure & digital elevation status...</span>
        </div>
      </div>
    );
  }

  if (error || !studyArea || !inventory || !demStatus) {
    return (
      <div className="rounded-xl border border-[#D8ECEC] bg-[#F5F9F9] p-3 text-xs">
        <div className="flex items-center justify-between">
          <span className="font-semibold text-[#182746]">Spatial Data Infrastructure</span>
          <button
            type="button"
            onClick={loadSpatialData}
            className="flex items-center gap-1 rounded-lg border border-[#D8ECEC] bg-[#FFFFFF] px-2 py-0.5 text-[10px] text-[#5A6A7E] hover:bg-[#E6F5F5]"
          >
            <RefreshCw className="h-3 w-3" />
            Retry
          </button>
        </div>
        <p className="mt-1 text-[11px] text-rose-700">
          {error || 'Spatial data infrastructure service currently unreachable.'}
        </p>
      </div>
    );
  }

  const bounds = studyArea.bounds;

  return (
    <div className="rounded-xl border border-[#D8ECEC] bg-[#FFFFFF] p-4 text-xs text-[#2B3A4A] space-y-3.5 shadow-xs">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#D8ECEC] pb-2">
        <div className="flex items-center gap-1.5 font-semibold text-[#182746]">
          <Layers className="h-4 w-4 text-[#119E9A]" />
          <span>Spatial Data Infrastructure & Terrain Baseline</span>
        </div>
        <span className="rounded-full bg-[#E6F5F5] border border-[#C8E5E5] px-2 py-0.5 text-[9px] font-mono font-medium text-[#182746]">
          Phase 3D Active
        </span>
      </div>

      {/* Sub-workspace View Switcher */}
      <div className="flex items-center gap-1.5 border-b border-[#D8ECEC] pb-2 flex-wrap">
        <button
          type="button"
          onClick={() => setActiveSpatialTab('catchment')}
          className={`flex items-center gap-1.5 px-3 py-1 text-[10px] font-medium rounded-full transition-colors ${
            activeSpatialTab === 'catchment'
              ? 'bg-[#119E9A] text-white shadow-xs'
              : 'bg-[#F5F9F9] text-[#182746] hover:bg-[#E6F5F5] border border-[#D8ECEC]'
          }`}
        >
          <Compass className="h-3 w-3" />
          <span>Upstream Catchment & Rainfall (Phase 3D)</span>
        </button>
        <button
          type="button"
          onClick={() => setActiveSpatialTab('hydrography')}
          className={`flex items-center gap-1.5 px-3 py-1 text-[10px] font-medium rounded-full transition-colors ${
            activeSpatialTab === 'hydrography'
              ? 'bg-[#119E9A] text-white shadow-xs'
              : 'bg-[#F5F9F9] text-[#182746] hover:bg-[#E6F5F5] border border-[#D8ECEC]'
          }`}
        >
          <GitFork className="h-3 w-3" />
          <span>River Hydrography & Network (Phase 3B)</span>
        </button>
        <button
          type="button"
          onClick={() => setActiveSpatialTab('terrain')}
          className={`flex items-center gap-1.5 px-3 py-1 text-[10px] font-medium rounded-full transition-colors ${
            activeSpatialTab === 'terrain'
              ? 'bg-[#119E9A] text-white shadow-xs'
              : 'bg-[#F5F9F9] text-[#182746] hover:bg-[#E6F5F5] border border-[#D8ECEC]'
          }`}
        >
          <Mountain className="h-3 w-3" />
          <span>Terrain, DEM & Bounds (Phase 3A)</span>
        </button>
      </div>

      {activeSpatialTab === 'catchment' ? (
        <CatchmentPanel />
      ) : activeSpatialTab === 'hydrography' ? (
        <HydrographyPanel />
      ) : (
        <>

      {/* Prominent Scientific Notice */}
      <div className="rounded-xl border border-[#C8E5E5] bg-[#E6F5F5] p-2.5 space-y-1 text-[#182746]">
        <div className="flex items-center gap-1.5 font-semibold text-[10px] text-[#119E9A]">
          <ShieldAlert className="h-3.5 w-3.5" />
          <span>SCIENTIFIC INTEGRITY & BOUNDARY NOTICES</span>
        </div>
        <ul className="list-disc pl-4 text-[8.5px] text-[#5A6A7E] space-y-0.5 leading-tight">
          <li>
            <strong>BOUNDING EXTENT:</strong> Study area is a rectangular coordinate box, NOT a natural watershed boundary.
          </li>
          <li>
            <strong>ELEVATION SAFEGUARD:</strong> Terrain elevation alone does NOT establish flood inundation extent or evacuation safety.
          </li>
          <li>
            <strong>RIVER TOPOLOGY SAFEGUARD:</strong> River centerlines represent linear channel alignment; they do NOT imply bathymetry, depth, or flood boundaries.
          </li>
          <li>
            <strong>PROVENANCE POLICY:</strong> Zero synthetic data fabricated. Unacquired elevation and river datasets remain strictly labeled UNAVAILABLE.
          </li>
        </ul>
      </div>

      {/* SECTION 1: Study Area & Geodetic CRS Contract */}
      <div className="space-y-1.5">
        <div className="flex items-center justify-between text-[11px] font-medium text-[#182746]">
          <span className="flex items-center gap-1">
            <Compass className="h-3.5 w-3.5 text-[#119E9A]" />
            Study Area Geodetic Contract
          </span>
          <span className="rounded-full bg-[#E6F5F5] border border-[#C8E5E5] px-2 py-0.5 text-[8px] font-mono text-[#182746]">
            {studyArea.geometry_type}
          </span>
        </div>

        <div className="rounded-lg border border-[#D8ECEC] bg-[#F5F9F9] p-2.5 space-y-1.5 text-[10px]">
          <div className="flex justify-between text-[#5A6A7E]">
            <span className="font-semibold text-[#182746]">{studyArea.name}</span>
            <span className="font-mono text-[9px]">Reach: {studyArea.reach_length_km} km</span>
          </div>
          <p className="text-[9px] text-[#5A6A7E] leading-tight">{studyArea.description}</p>

          {/* Coordinate Bounds Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-1.5 pt-0.5 text-center text-[9px]">
            <div className="rounded-md bg-[#FFFFFF] p-1 border border-[#D8ECEC]">
              <div className="text-[#5A6A7E]">West Lon</div>
              <div className="font-mono font-semibold text-[#182746]">{bounds.west_lon}°E</div>
            </div>
            <div className="rounded-md bg-[#FFFFFF] p-1 border border-[#D8ECEC]">
              <div className="text-[#5A6A7E]">South Lat</div>
              <div className="font-mono font-semibold text-[#182746]">{bounds.south_lat}°N</div>
            </div>
            <div className="rounded-md bg-[#FFFFFF] p-1 border border-[#D8ECEC]">
              <div className="text-[#5A6A7E]">East Lon</div>
              <div className="font-mono font-semibold text-[#182746]">{bounds.east_lon}°E</div>
            </div>
            <div className="rounded-md bg-[#FFFFFF] p-1 border border-[#D8ECEC]">
              <div className="text-[#5A6A7E]">North Lat</div>
              <div className="font-mono font-semibold text-[#182746]">{bounds.north_lat}°N</div>
            </div>
          </div>

          {/* CRS Discipline Callout */}
          <div className="rounded-md bg-[#FFFFFF] p-2 border border-[#D8ECEC] text-[9px] text-[#182746] space-y-0.5">
            <div>
              <strong>Geographic CRS:</strong> <code className="font-mono text-[#119E9A]">{studyArea.geographic_crs}</code>
            </div>
            <div>
              <strong>Projected CRS:</strong> <code className="font-mono text-[#119E9A]">{studyArea.projected_crs}</code>
            </div>
            <p className="text-[8px] text-[#5A6A7E] pt-0.5 leading-tight">
              {studyArea.projected_crs_justification}
            </p>
          </div>
        </div>
      </div>

      {/* SECTION 2: Digital Elevation Model (DEM) Status */}
      <div className="space-y-1.5">
        <div className="flex items-center justify-between text-[11px] font-medium text-[#182746]">
          <span className="flex items-center gap-1">
            <Mountain className="h-3.5 w-3.5 text-[#119E9A]" />
            Digital Elevation Model (DEM) Status
          </span>
          <span
            className={`rounded-full px-2 py-0.5 text-[8px] font-mono font-semibold ${
              demStatus.dem_availability === 'AVAILABLE'
                ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                : 'bg-rose-100 text-rose-800 border border-rose-300'
            }`}
          >
            {demStatus.dem_availability}
          </span>
        </div>

        {demStatus.dem_availability === 'UNAVAILABLE' ? (
          <div className="rounded-lg border border-dashed border-[#D8ECEC] bg-[#F5F9F9] p-3 space-y-2 text-[10px]">
            <div className="flex items-center gap-2 text-amber-800">
              <Database className="h-4 w-4 shrink-0 text-amber-700" />
              <span className="font-medium">No Validated DEM Raster Detected in Repository</span>
            </div>

            <p className="text-[9px] text-[#5A6A7E] leading-relaxed">
              In strict compliance with Phase 3A integrity guidelines, synthetic elevation surfaces are not fabricated.
              To activate real terrain analysis, place official 30m GeoTIFF tiles covering the Yamuna corridor into:
              <br />
              <code className="mt-0.5 inline-block font-mono text-[8.5px] text-[#119E9A] bg-[#FFFFFF] px-1.5 py-0.5 rounded border border-[#D8ECEC]">
                {demStatus.scanned_directory}
              </code>
            </p>

            {demStatus.acquisition_guide && (
              <div className="rounded-md bg-[#FFFFFF] p-2 border border-[#D8ECEC] space-y-1 text-[9px] text-[#182746]">
                <div className="font-semibold text-[#119E9A]">Ingestion Requirements:</div>
                <ul className="list-disc pl-3 text-[8.5px] text-[#5A6A7E] space-y-0.5">
                  {demStatus.acquisition_guide.required_properties.map((prop, idx) => (
                    <li key={idx}>{prop}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ) : (
          /* Available DEM Metadata Card */
          demStatus.validation_report && (
            <div className="rounded-lg border border-[#D8ECEC] bg-[#F5F9F9] p-2.5 space-y-2 text-[10px]">
              <div className="flex items-center justify-between text-[#182746]">
                <span className="font-semibold">{demStatus.validation_report.file_name}</span>
                <span className="font-mono text-[9px] text-emerald-700">
                  {demStatus.validation_report.validation_status}
                </span>
              </div>

              <div className="grid grid-cols-3 gap-1.5 text-center text-[9px]">
                <div className="rounded-md bg-[#FFFFFF] p-1 border border-[#D8ECEC]">
                  <div className="text-[#5A6A7E]">Grid Size</div>
                  <div className="font-mono font-semibold text-[#182746]">
                    {demStatus.validation_report.dimensions.width} × {demStatus.validation_report.dimensions.height}
                  </div>
                </div>
                <div className="rounded-md bg-[#FFFFFF] p-1 border border-[#D8ECEC]">
                  <div className="text-[#5A6A7E]">CRS EPSG</div>
                  <div className="font-mono font-semibold text-[#182746]">
                    {demStatus.validation_report.crs_epsg || 'Undefined'}
                  </div>
                </div>
                <div className="rounded-md bg-[#FFFFFF] p-1 border border-[#D8ECEC]">
                  <div className="text-[#5A6A7E]">Missing / NoData</div>
                  <div className="font-mono font-semibold text-[#182746]">
                    {demStatus.validation_report.missing_cells_percentage}%
                  </div>
                </div>
              </div>

              {/* Elevation Statistics */}
              <div className="rounded-md bg-[#FFFFFF] p-1.5 border border-[#D8ECEC] text-[9px] text-[#182746] flex items-center justify-between">
                <span>
                  Elev Min: <strong>{demStatus.validation_report.min_elevation_m} m</strong>
                </span>
                <span>
                  Mean: <strong>{demStatus.validation_report.mean_elevation_m} m</strong>
                </span>
                <span>
                  Max: <strong>{demStatus.validation_report.max_elevation_m} m</strong>
                </span>
              </div>
            </div>
          )
        )}
      </div>

      {/* SECTION 3: River Network & Geospatial Hydrography (Phase 3B) */}
      <div className="space-y-1.5">
        <div className="flex items-center justify-between text-[11px] font-medium text-[#182746]">
          <span className="flex items-center gap-1">
            <Layers className="h-3.5 w-3.5 text-[#119E9A]" />
            River Network & Hydrography (Phase 3B)
          </span>
          <span
            className={`rounded-full px-2 py-0.5 text-[8px] font-mono font-semibold ${
              riverStatus?.river_data_availability === 'AVAILABLE'
                ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                : 'bg-rose-100 text-rose-800 border border-rose-300'
            }`}
          >
            {riverStatus?.river_data_availability || 'UNAVAILABLE'}
          </span>
        </div>

        {!riverStatus || riverStatus.river_data_availability === 'UNAVAILABLE' ? (
          <div className="rounded-lg border border-dashed border-[#D8ECEC] bg-[#F5F9F9] p-2.5 space-y-2 text-[10px]">
            <div className="flex items-center gap-2 text-amber-800">
              <Database className="h-4 w-4 shrink-0 text-amber-700" />
              <span className="font-medium">No Validated River Vector Dataset Detected in Repository</span>
            </div>

            <p className="text-[9px] text-[#5A6A7E] leading-relaxed">
              In strict adherence to PRAVAAH scientific standards, synthetic river alignments are not fabricated.
              To ingest authentic river centerlines, place verified GeoJSON, GeoPackage, or Shapefile datasets into:
              <br />
              <code className="mt-0.5 inline-block font-mono text-[8.5px] text-[#119E9A] bg-[#FFFFFF] px-1.5 py-0.5 rounded border border-[#D8ECEC]">
                {riverStatus?.scanned_directory || 'data/raw/spatial/hydrography'}
              </code>
            </p>

            {riverStatus?.acquisition_guide && (
              <div className="rounded-md bg-[#FFFFFF] p-2 border border-[#D8ECEC] space-y-1 text-[9px] text-[#182746]">
                <div className="font-semibold text-[#119E9A]">Ingestion Requirements:</div>
                <ul className="list-disc pl-3 text-[8.5px] text-[#5A6A7E] space-y-0.5">
                  {riverStatus.acquisition_guide.required_properties.map((prop, idx) => (
                    <li key={idx}>{prop}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ) : (
          /* Available River Network Card */
          riverStatus.validation_report && (
            <div className="rounded-lg border border-[#D8ECEC] bg-[#F5F9F9] p-2.5 space-y-2 text-[10px]">
              <div className="flex items-center justify-between text-[#182746]">
                <span className="font-semibold">{riverStatus.validation_report.dataset_file}</span>
                <span className="font-mono text-[9px] text-emerald-700">
                  {riverStatus.validation_report.validation_status}
                </span>
              </div>

              <div className="grid grid-cols-3 gap-1.5 text-center text-[9px]">
                <div className="rounded-md bg-[#FFFFFF] p-1 border border-[#D8ECEC]">
                  <div className="text-[#5A6A7E]">Total Features</div>
                  <div className="font-mono font-semibold text-[#182746]">
                    {riverStatus.validation_report.total_features}
                  </div>
                </div>
                <div className="rounded-md bg-[#FFFFFF] p-1 border border-[#D8ECEC]">
                  <div className="text-[#5A6A7E]">Reach Length</div>
                  <div className="font-mono font-semibold text-[#182746]">
                    {riverStatus.validation_report.total_length_km} km
                  </div>
                </div>
                <div className="rounded-md bg-[#FFFFFF] p-1 border border-[#D8ECEC]">
                  <div className="text-[#5A6A7E]">Corridor Overlap</div>
                  <div className="font-mono font-semibold text-[#182746]">
                    {(riverStatus.validation_report.study_area_containment_ratio * 100).toFixed(1)}%
                  </div>
                </div>
              </div>

              {/* Waterways by Type */}
              <div className="rounded-md bg-[#FFFFFF] p-1.5 border border-[#D8ECEC] text-[9px] text-[#182746] flex items-center justify-between">
                <span>
                  Metric CRS: <strong>{riverStatus.validation_report.projected_metric_crs}</strong>
                </span>
                <span>
                  Types: <strong>{Object.entries(riverStatus.validation_report.features_by_type).map(([k, v]) => `${k}: ${v}`).join(', ')}</strong>
                </span>
              </div>
            </div>
          )
        )}
      </div>

      {/* SECTION 4: Topographical Terrain Slope Analysis */}
      <div className="space-y-1.5">
        <div className="flex items-center justify-between text-[11px] font-medium text-[#182746]">
          <span className="flex items-center gap-1">
            <Compass className="h-3.5 w-3.5 text-[#119E9A]" />
            Terrain Slope Analysis
          </span>
          <span className="text-[9px] text-[#5A6A7E]">
            {terrain?.status === 'AVAILABLE' ? 'Metric Gradient Active' : 'Awaiting DEM Ingestion'}
          </span>
        </div>

        {terrain?.status === 'AVAILABLE' && terrain.slope_summary ? (
          <div className="rounded-lg border border-[#D8ECEC] bg-[#F5F9F9] p-2.5 space-y-1 text-[9px] text-[#182746]">
            <div className="grid grid-cols-3 gap-1.5 text-center">
              <div className="rounded-md bg-[#FFFFFF] p-1.5 border border-[#D8ECEC]">
                <div className="text-[#5A6A7E]">Mean Slope</div>
                <div className="font-mono font-semibold text-[#182746]">
                  {terrain.slope_summary.mean_slope_deg}°
                </div>
              </div>
              <div className="rounded-md bg-[#FFFFFF] p-1.5 border border-[#D8ECEC]">
                <div className="text-[#5A6A7E]">Max Slope</div>
                <div className="font-mono font-semibold text-[#182746]">
                  {terrain.slope_summary.max_slope_deg}°
                </div>
              </div>
              <div className="rounded-md bg-[#FFFFFF] p-1.5 border border-[#D8ECEC]">
                <div className="text-[#5A6A7E]">Mean Gradient</div>
                <div className="font-mono font-semibold text-[#182746]">
                  {terrain.slope_summary.mean_slope_percent}%
                </div>
              </div>
            </div>
            <p className="text-[8px] text-[#5A6A7E] pt-0.5 leading-tight">
              Computed via {terrain.slope_summary.computation_method}.
            </p>
          </div>
        ) : (
          <div className="rounded-lg bg-[#F5F9F9] border border-[#D8ECEC] p-2.5 text-[9px] text-[#5A6A7E] leading-tight">
            Slope analysis will compute metric 2D gradients automatically once a validated DEM raster is supplied.
          </div>
        )}
      </div>

      {/* SECTION 5: Spatial Dataset Inventory */}
      <div className="space-y-1.5">
        <div className="flex items-center justify-between text-[11px] font-medium text-[#182746]">
          <span className="flex items-center gap-1">
            <Database className="h-3.5 w-3.5 text-[#119E9A]" />
            Spatial Dataset Inventory & Provenance
          </span>
          <span className="text-[9px] text-[#5A6A7E]">
            {inventory.total_datasets} candidate sources
          </span>
        </div>

        <div className="space-y-1 max-h-48 overflow-y-auto pr-1">
          {inventory.datasets.map((ds) => (
            <div
              key={ds.dataset_id}
              className="rounded-lg border border-[#D8ECEC] bg-[#FFFFFF] p-2 text-[9px] text-[#2B3A4A] space-y-0.5"
            >
              <div className="flex items-center justify-between">
                <span className="font-semibold text-[#182746]">{ds.name}</span>
                <span className="rounded-full bg-rose-100 text-rose-800 border border-rose-300 px-1.5 py-0.2 text-[7.5px] font-mono uppercase">
                  {ds.current_status}
                </span>
              </div>
              <div className="flex justify-between text-[#5A6A7E] text-[8px]">
                <span>Agency: {ds.source_agency}</span>
                <span>Res: {ds.spatial_resolution}</span>
              </div>
              <p className="text-[8px] text-[#5A6A7E] italic leading-tight">
                Blocker: {ds.acquisition_blockers}
              </p>
            </div>
          ))}
        </div>
      </div>
      </>
      )}
    </div>
  );
};
