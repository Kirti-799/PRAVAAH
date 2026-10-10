import React from 'react';
import { Map, Layers, Database, AlertCircle, Compass } from 'lucide-react';

export const WorkspacePanel: React.FC = () => {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-6 lg:p-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-5">
        <div>
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <Map className="h-5 w-5 text-teal-400" />
            Geospatial Workspace & Risk Map Canvas
          </h2>
          <p className="mt-1 text-xs text-slate-400">
            Interactive GIS viewport designated for flood risk heatmaps, terrain analysis, and routing layers.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 rounded-md bg-slate-800 px-2.5 py-1 text-xs font-mono text-slate-300 border border-slate-700">
            <Layers className="h-3.5 w-3.5 text-teal-400" />
            MapLibre GL JS (Planned)
          </span>
        </div>
      </div>

      {/* Empty State Canvas */}
      <div className="mt-6 flex min-h-[320px] flex-col items-center justify-center rounded-lg border border-dashed border-slate-800 bg-slate-950/60 p-8 text-center">
        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-900 border border-slate-800 text-teal-400 shadow-inner">
          <Compass className="h-7 w-7 text-teal-400/80" />
        </div>

        <h3 className="mt-4 text-sm font-semibold text-white sm:text-base">
          Geospatial Map Visualization Awaiting Phase Integration
        </h3>

        <p className="mt-2 max-w-lg text-xs leading-relaxed text-slate-400">
          In strict accordance with Phase 0 specifications, operational map tiles and fabricated risk polygons are not displayed. Live geospatial rendering using MapLibre GL JS, GeoJSON boundaries, and digital elevation models will be connected in subsequent phases once backend GIS pipelines are active.
        </p>

        <div className="mt-6 grid grid-cols-1 gap-3 sm:grid-cols-3 max-w-xl w-full text-left">
          <div className="rounded-lg border border-slate-800/80 bg-slate-900/60 p-3">
            <span className="text-[11px] font-semibold text-slate-300 flex items-center gap-1.5">
              <Database className="h-3.5 w-3.5 text-teal-400" />
              GIS Data Pipeline
            </span>
            <p className="mt-1 text-[11px] text-slate-400">
              Raster DEM & hydrological vector data schemas in <code className="text-teal-400">geospatial/</code>.
            </p>
          </div>

          <div className="rounded-lg border border-slate-800/80 bg-slate-900/60 p-3">
            <span className="text-[11px] font-semibold text-slate-300 flex items-center gap-1.5">
              <Layers className="h-3.5 w-3.5 text-teal-400" />
              Vector Tiles
            </span>
            <p className="mt-1 text-[11px] text-slate-400">
              Multi-scale administrative boundaries and flood extent polygons.
            </p>
          </div>

          <div className="rounded-lg border border-slate-800/80 bg-slate-900/60 p-3">
            <span className="text-[11px] font-semibold text-slate-300 flex items-center gap-1.5">
              <AlertCircle className="h-3.5 w-3.5 text-teal-400" />
              Safety Guarantee
            </span>
            <p className="mt-1 text-[11px] text-slate-400">
              Zero mock predictions: Real hazard alerts require validated models.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
