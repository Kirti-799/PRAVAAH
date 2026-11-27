/**
 * frontend/src/components/map/InteractiveGISMap.tsx
 *
 * Interactive GIS workstation map for PRAVAAH using React-Leaflet and OpenStreetMap.
 * Features:
 * - Study corridor bounding box overlay [28.50°N - 30.40°N, 76.85°E - 77.60°E]
 * - Multi-layer toggleable visibility with strict availability guardrails
 * - Real corridor monitoring stations (Hathnikund, Yamunanagar, Karnal, Panipat, Sonipat, Delhi ORB, Okhla)
 * - Click-to-inspect coordinate inspection and weather dispatching
 * - Basemap switching (OSM Standard, Carto Positron, OpenTopoMap)
 * - Map reset-to-extent, coordinate readout, and scale indicator
 * - Cream-and-brown cartographic styling
 */

import React, { useState, useEffect } from 'react';
import {
  MapContainer,
  TileLayer,
  Rectangle,
  Marker,
  CircleMarker,
  Popup,
  GeoJSON,
  useMapEvents,
} from 'react-leaflet';
import L from 'leaflet';
import { ErrorBoundary } from '../common/ErrorBoundary';
import { isValidGeoJSON } from '../../utils/geojson';
import {
  Play,
  Pause,
  ChevronLeft,
  ChevronRight,
  RotateCcw,
  Activity,
} from 'lucide-react';
import type { BasemapOption, WeatherLocation } from '../../types/weather';
import { fetchBasemapConfig, fetchCorridorLocations } from '../../services/weather';
import {
  fetchRiverFeatures,
  fetchCatchmentGeometry,
  fetchCatchmentDrainage,
  fetchRainfallCatchmentSummary,
} from '../../services/spatial';
import { fetchSpatialRoutingSimulation } from '../../services/routing';
import { fetchSheltersGeoJSON, fetchEvacuationCorridorsGeoJSON } from '../../services/disaster';
import type { RiverGeoJSONResponse, CatchmentRainfallSummaryResponse } from '../../types/spatial';
import type {
  SpatialRoutingSimulationResponse,
  SpatialRoutingPoint,
} from '../../types/routing';

// Layer Availability Types
export type LayerStatus =
  | 'AVAILABLE'
  | 'UNAVAILABLE_IN_REPOSITORY'
  | 'SOURCE_UNAVAILABLE'
  | 'LOADING'
  | 'VALIDATION_FAILED';

export interface GISLayerDef {
  id: string;
  name: string;
  category: 'Boundary' | 'Hydrography' | 'Terrain' | 'Meteorology' | 'Human Exposure';
  status: LayerStatus;
  visible: boolean;
  color: string;
  description: string;
}

const DEFAULT_LAYERS: GISLayerDef[] = [
  {
    id: 'study_bounds',
    name: 'Study Corridor Boundary',
    category: 'Boundary',
    status: 'AVAILABLE',
    visible: false,
    color: '#8B4513',
    description: 'Upper-to-Middle Yamuna Corridor [28.50°N - 30.40°N, 76.85°E - 77.60°E]',
  },
  {
    id: 'upstream_catchment',
    name: 'Upstream Catchment Boundary',
    category: 'Boundary',
    status: 'AVAILABLE',
    visible: false,
    color: '#8B4513',
    description: '11,365 km² DEM D8 delineated basin (CWC Survey: 11,112 km²)',
  },
  {
    id: 'corridor_stations',
    name: 'Monitoring & Barrage Stations',
    category: 'Boundary',
    status: 'AVAILABLE',
    visible: true,
    color: '#8B4513',
    description: '7 primary hydrometric & meteorological reference stations (Hathnikund to Okhla)',
  },
  {
    id: 'main_yamuna',
    name: 'Main Yamuna River Centerline',
    category: 'Hydrography',
    status: 'AVAILABLE',
    visible: true,
    color: '#2B5B84',
    description: 'Validated river centerline geometry (251.05 km to Delhi ORB / 268.94 km to Okhla)',
  },
  {
    id: 'catchment_drainage',
    name: 'Catchment Drainage Network (DEM)',
    category: 'Hydrography',
    status: 'AVAILABLE',
    visible: false,
    color: '#3B82F6',
    description: 'DEM-derived contributing stream network (Yamuna, Tons, Giri, Pabbar, Asan)',
  },
  {
    id: 'routing_wave',
    name: '1D Flood Wave Progression (Muskingum)',
    category: 'Hydrography',
    status: 'AVAILABLE',
    visible: false,
    color: '#7C3AED',
    description: '1D Muskingum routed flood wave progression along Yamuna thalweg (2023 Episode)',
  },
  {
    id: 'tributaries',
    name: 'Tributaries (Hindon, Tons, Giri)',
    category: 'Hydrography',
    status: 'UNAVAILABLE_IN_REPOSITORY',
    visible: false,
    color: '#60A5FA',
    description: 'Raw vector data not yet ingested in repository catalog',
  },
  {
    id: 'canals',
    name: 'Canals (WJC & EJC Off-takes)',
    category: 'Hydrography',
    status: 'UNAVAILABLE_IN_REPOSITORY',
    visible: false,
    color: '#0284C7',
    description: 'Western & Eastern Yamuna Canal geometries awaiting Phase 3D ingestion',
  },
  {
    id: 'drains',
    name: 'Drains & Minor Waterways',
    category: 'Hydrography',
    status: 'UNAVAILABLE_IN_REPOSITORY',
    visible: false,
    color: '#94A3B8',
    description: 'Najafgarh and secondary storm water outfalls awaiting CWC/DJB vector dataset',
  },
  {
    id: 'embankments',
    name: 'Embankments & Flood Bunds',
    category: 'Hydrography',
    status: 'UNAVAILABLE_IN_REPOSITORY',
    visible: false,
    color: '#D97706',
    description: 'Official flood protection bund geometries unavailable in public sources',
  },
  {
    id: 'dem_elevation',
    name: 'Copernicus DEM GLO-30 Mosaic',
    category: 'Terrain',
    status: 'AVAILABLE',
    visible: false,
    color: '#84CC16',
    description: 'Copernicus DEM GLO-30 30m mosaic (4 tiles acquired, 255m - 6740m MSL)',
  },
  {
    id: 'terrain_slope',
    name: 'Topographical Slope Map',
    category: 'Terrain',
    status: 'AVAILABLE',
    visible: false,
    color: '#F59E0B',
    description: 'Horn slope derived from validated 30m Copernicus DEM mosaic',
  },
  {
    id: 'catchment_rainfall_grid',
    name: 'Catchment Spatial Rainfall Grid',
    category: 'Meteorology',
    status: 'AVAILABLE',
    visible: true,
    color: '#0D9488',
    description: '20 multi-point elevational sampling nodes with 24h/72h forecast and API-3',
  },
  {
    id: 'rainfall_obs',
    name: 'Rainfall Observations (IMD)',
    category: 'Meteorology',
    status: 'UNAVAILABLE_IN_REPOSITORY',
    visible: false,
    color: '#10B981',
    description: 'IMD official ground gauge daily totals awaiting institutional API access',
  },
  {
    id: 'rainfall_forecast',
    name: 'Rainfall Forecast (Open-Meteo)',
    category: 'Meteorology',
    status: 'AVAILABLE',
    visible: true,
    color: '#06B6D4',
    description: 'Point forecast markers connected to Open-Meteo live integration pipeline',
  },
  {
    id: 'admin_bounds',
    name: 'Administrative Boundaries',
    category: 'Human Exposure',
    status: 'UNAVAILABLE_IN_REPOSITORY',
    visible: false,
    color: '#64748B',
    description: 'District and tehsil boundaries (Haryana, UP, Delhi NCT) awaiting Shapefile ingestion',
  },
  {
    id: 'pop_exposure',
    name: 'Population Exposure Grid',
    category: 'Human Exposure',
    status: 'UNAVAILABLE_IN_REPOSITORY',
    visible: false,
    color: '#EC4899',
    description: 'High-resolution population density grids awaiting Phase 4 socioeconomic milestone',
  },
  {
    id: 'shelters',
    name: 'Evacuation Shelters (Illustrative Prototype)',
    category: 'Human Exposure',
    status: 'AVAILABLE',
    visible: true,
    color: '#8B5CF6',
    description: 'Illustrative relief camps based on public DDMA guidelines (Unvalidated for operational life-safety)',
  },
  {
    id: 'evacuation_corridors',
    name: 'Evacuation Corridors (Illustrative Prototype)',
    category: 'Human Exposure',
    status: 'AVAILABLE',
    visible: true,
    color: '#D97706',
    description: 'Illustrative arterial vectors (Route geometry unvalidated for hydraulic submergence safety)',
  },
];

// Helper to create custom HTML pin markers
function createCustomPin(color: string, label: string, isBarrage: boolean = false) {
  return L.divIcon({
    className: 'custom-gis-pin',
    html: `
      <div style="
        display: flex;
        align-items: center;
        justify-content: center;
        background-color: ${color};
        color: #FFFFFF;
        width: ${isBarrage ? '32px' : '26px'};
        height: ${isBarrage ? '32px' : '26px'};
        border-radius: 50%;
        border: 2px solid #FFFFFF;
        box-shadow: 0 2px 5px rgba(0,0,0,0.3);
        font-weight: 700;
        font-size: 11px;
        font-family: monospace;
      ">
        ${label}
      </div>
    `,
    iconSize: [isBarrage ? 32 : 26, isBarrage ? 32 : 26],
    iconAnchor: [isBarrage ? 16 : 13, isBarrage ? 16 : 13],
    popupAnchor: [0, isBarrage ? -18 : -14],
  });
}

// Inner helper component for map click and bounds control
function MapEventController({
  onMapClick,
}: {
  onMapClick: (lat: number, lon: number) => void;
}) {
  useMapEvents({
    click(e) {
      onMapClick(e.latlng.lat, e.latlng.lng);
    },
  });
  return null;
}

interface InteractiveGISMapProps {
  selectedCoordinate?: { lat: number; lon: number } | null;
  onSelectCoordinate?: (lat: number, lon: number, locationName?: string) => void;
}

export const InteractiveGISMap: React.FC<InteractiveGISMapProps> = ({
  selectedCoordinate,
  onSelectCoordinate,
}) => {
  const [mapInstance, setMapInstance] = useState<L.Map | null>(null);
  const [basemaps, setBasemaps] = useState<BasemapOption[]>([]);
  const [selectedBasemapId, setSelectedBasemapId] = useState<string>('osm_standard');
  const [layers, setLayers] = useState<GISLayerDef[]>(DEFAULT_LAYERS);
  const [stations, setStations] = useState<WeatherLocation[]>([]);
  const [riverGeoJSON, setRiverGeoJSON] = useState<RiverGeoJSONResponse | null>(null);
  const [catchmentGeoJSON, setCatchmentGeoJSON] = useState<any>(null);
  const [drainageGeoJSON, setDrainageGeoJSON] = useState<any>(null);
  const [rainfallSummary, setRainfallSummary] = useState<CatchmentRainfallSummaryResponse | null>(null);
  const [spatialRoutingData, setSpatialRoutingData] = useState<SpatialRoutingSimulationResponse | null>(null);
  const [sheltersGeoJSON, setSheltersGeoJSON] = useState<any>(null);
  const [corridorsGeoJSON, setCorridorsGeoJSON] = useState<any>(null);
  const [activeStepIndex, setActiveStepIndex] = useState<number>(3);
  const [isPlayingWave, setIsPlayingWave] = useState<boolean>(false);
  const [selectedRoutingPoint, setSelectedRoutingPoint] = useState<SpatialRoutingPoint | null>(null);
  const [activeCursorCoords, setActiveCursorCoords] = useState<{ lat: number; lon: number } | null>(null);
  const [showLayerDrawer, setShowLayerDrawer] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Authoritative corridor bounds: West 76.85, East 77.60, South 28.50, North 30.40
  const corridorBounds: L.LatLngBoundsExpression = [
    [28.50, 76.85],
    [30.40, 77.60],
  ];
  // Upstream Himalayan catchment bounds: South 30.25, North 31.50, West 77.05, East 78.65
  const catchmentBounds: L.LatLngBoundsExpression = [
    [30.25, 77.05],
    [31.50, 78.65],
  ];
  const corridorCenter: [number, number] = [29.45, 77.22];

  const handleResetBounds = () => {
    if (mapInstance) {
      mapInstance.fitBounds(corridorBounds, { padding: [20, 20] });
    }
  };

  const handleFitCatchment = () => {
    if (mapInstance) {
      mapInstance.fitBounds(catchmentBounds, { padding: [20, 20] });
    }
  };

  // Sync external selected coordinate from parent workspace
  useEffect(() => {
    if (selectedCoordinate) {
      setActiveCursorCoords({ lat: selectedCoordinate.lat, lon: selectedCoordinate.lon });
    }
  }, [selectedCoordinate]);

  useEffect(() => {
    async function loadMapData() {
      setIsLoading(true);
      try {
        // Load basemaps, corridor locations, river features, upstream catchment, 1D routing wave, and shelters
        const [
          baseConfig,
          locsData,
          riverData,
          catchData,
          drainData,
          rainData,
          waveData,
          sheltersData,
          corridorsData,
        ] = await Promise.all([
          fetchBasemapConfig().catch(() => null),
          fetchCorridorLocations().catch(() => null),
          fetchRiverFeatures().catch(() => null),
          fetchCatchmentGeometry().catch(() => null),
          fetchCatchmentDrainage().catch(() => null),
          fetchRainfallCatchmentSummary().catch(() => null),
          fetchSpatialRoutingSimulation('EPISODE_2023_08', 36.0, 0.20, 5.0).catch(() => null),
          fetchSheltersGeoJSON().catch(() => null),
          fetchEvacuationCorridorsGeoJSON().catch(() => null),
        ]);

        if (baseConfig && baseConfig.basemaps.length > 0) {
          setBasemaps(baseConfig.basemaps);
          setSelectedBasemapId(baseConfig.default_basemap_id || 'osm_standard');
        }

        if (locsData && locsData.locations) {
          setStations(locsData.locations);
        }

        if (riverData && riverData.features && riverData.features.length > 0) {
          setRiverGeoJSON(riverData);
        } else {
          // If no river features in database, mark layer status
          setLayers((prev) =>
            prev.map((l) =>
              l.id === 'main_yamuna' ? { ...l, status: 'UNAVAILABLE_IN_REPOSITORY' } : l
            )
          );
        }

        if (catchData && catchData.features && catchData.features.length > 0) {
          setCatchmentGeoJSON(catchData);
        }

        if (drainData && drainData.features && drainData.features.length > 0) {
          setDrainageGeoJSON(drainData);
        }

        if (rainData) {
          setRainfallSummary(rainData);
        }

        if (waveData && waveData.time_steps && waveData.time_steps.length > 0) {
          setSpatialRoutingData(waveData);
          // Default to peak inflow date index if available
          const peakIdx = waveData.time_steps.findIndex(
            (s) => s.date === waveData.peak_observed_inflow_date
          );
          if (peakIdx >= 0) {
            setActiveStepIndex(peakIdx);
          }
        }

        if (sheltersData && sheltersData.features && sheltersData.features.length > 0) {
          setSheltersGeoJSON(sheltersData);
        }

        if (corridorsData && corridorsData.features && corridorsData.features.length > 0) {
          setCorridorsGeoJSON(corridorsData);
        }
      } catch (err) {
        console.warn('Map initialization data load warning:', err);
      } finally {
        setIsLoading(false);
      }
    }

    loadMapData();
  }, []);

  // Animation playback interval for 1D routing wave progression
  useEffect(() => {
    if (!isPlayingWave || !spatialRoutingData || spatialRoutingData.time_steps.length === 0) return;
    const interval = setInterval(() => {
      setActiveStepIndex((prev) => (prev + 1) % spatialRoutingData.time_steps.length);
    }, 1400);
    return () => clearInterval(interval);
  }, [isPlayingWave, spatialRoutingData]);

  const handleToggleLayer = (id: string) => {
    setLayers((prev) =>
      prev.map((layer) => {
        if (layer.id === id) {
          // Guardrail: Do not toggle layers that are unavailable in repository
          if (layer.status !== 'AVAILABLE') return layer;
          return { ...layer, visible: !layer.visible };
        }
        return layer;
      })
    );
  };

  const handleMapClick = (lat: number, lon: number) => {
    setActiveCursorCoords({ lat, lon });
  };

  const currentBasemap =
    basemaps.find((b) => b.id === selectedBasemapId) || {
      id: 'osm_standard',
      name: 'OpenStreetMap Standard',
      tile_url: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors',
      max_zoom: 19,
      min_zoom: 4,
      is_default: true,
      terms_of_use_url: 'https://operations.osmfoundation.org/policies/tiles/',
      description: 'Default OSM Cartography',
    };

  const isLayerVisible = (id: string) => {
    const l = layers.find((item) => item.id === id);
    return l ? l.visible && l.status === 'AVAILABLE' : false;
  };

  return (
    <div className="relative w-full h-full flex flex-col bg-[#FBF9F5] text-[#3E3026] select-none overflow-hidden">
      {/* Top Map Header / Controls Bar */}
      <div className="h-10 px-3 bg-[#FFFFFF] border-b border-[#EAE3D9] flex items-center justify-between z-10 shadow-xs">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-[#2C221E]">
            <span className="w-2.5 h-2.5 rounded-full bg-[#8B4513] animate-pulse"></span>
            PRAVAAH GIS WORKSTATION
          </div>
          <span className="text-xs text-[#635347]">|</span>
          <span className="text-xs text-[#635347] font-mono">
            Corridor: Hathnikund (30.31°N) → Delhi ORB (28.66°N)
          </span>
        </div>

        <div className="flex items-center gap-3">
          {/* Basemap Switcher */}
          <div className="flex items-center gap-1.5 text-xs">
            <span className="text-[#635347] font-medium">Basemap:</span>
            <select
              value={selectedBasemapId}
              onChange={(e) => setSelectedBasemapId(e.target.value)}
              className="bg-[#F5EFEB] text-[#3E3026] text-xs font-medium rounded px-2 py-0.5 border border-[#EAE3D9] focus:outline-none focus:ring-1 focus:ring-[#8B4513]"
            >
              {basemaps.length > 0 ? (
                basemaps.map((b) => (
                  <option key={b.id} value={b.id}>
                    {b.name}
                  </option>
                ))
              ) : (
                <option value="osm_standard">OpenStreetMap Standard</option>
              )}
            </select>
          </div>

          {/* Reset Extent */}
          <button
            onClick={handleResetBounds}
            className="px-2.5 py-1 text-xs font-medium bg-[#FFFFFF] text-[#2C221E] border border-[#EAE3D9] rounded shadow-xs hover:bg-[#F5EFEB] transition-colors flex items-center gap-1.5"
            title="Reset map viewport to Yamuna Study Corridor extent"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Corridor Extent
          </button>

          {/* Catchment Extent */}
          <button
            onClick={handleFitCatchment}
            className="px-2.5 py-1 text-xs font-medium bg-[#FFFFFF] text-[#8B4513] border border-[#D8CEBE] rounded shadow-xs hover:bg-[#F5EFEB] transition-colors flex items-center gap-1.5"
            title="Fit map viewport to Upstream Himalayan Catchment feeding Hathnikund"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 00-9.78 2.096A4.001 4.001 0 003 15z" />
            </svg>
            Catchment Extent
          </button>

          {/* Layer Panel Toggle */}
          <button
            onClick={() => setShowLayerDrawer(!showLayerDrawer)}
            className={`px-2.5 py-1 text-xs font-medium rounded border transition-colors flex items-center gap-1.5 ${
              showLayerDrawer
                ? 'bg-[#2C221E] text-[#FFFFFF] border-[#2C221E]'
                : 'bg-[#FFFFFF] text-[#2C221E] border-[#EAE3D9] hover:bg-[#F5EFEB]'
            }`}
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
            Layers ({layers.filter((l) => l.visible && l.status === 'AVAILABLE').length}/{layers.length})
          </button>
        </div>
      </div>

      {/* Main Map Body Container */}
      <div className="relative flex-1 w-full h-full">
        {isLoading && (
          <div className="absolute top-3 left-1/2 -translate-x-1/2 z-20 bg-[#FFFFFF]/95 backdrop-blur-xs border border-[#EAE3D9] px-3 py-1.5 rounded-full shadow-md text-xs font-medium text-[#2C221E] flex items-center gap-2">
            <span className="w-2.5 h-2.5 border-2 border-[#8B4513] border-t-transparent rounded-full animate-spin" />
            <span>Loading Spatial Layers...</span>
          </div>
        )}
        <ErrorBoundary isMapContainer={true}>
        <MapContainer
          ref={setMapInstance}
          center={corridorCenter}
          zoom={8}
          minZoom={6}
          maxZoom={18}
          className="w-full h-full z-0"
          style={{ background: '#FBF9F5' }}
        >
          {/* Tile Layer with Dynamic Provider */}
          <TileLayer
            key={currentBasemap.id}
            url={currentBasemap.tile_url}
            attribution={currentBasemap.attribution}
            maxZoom={currentBasemap.max_zoom}
            minZoom={currentBasemap.min_zoom}
          />

          {/* Map Click Events */}
          <MapEventController onMapClick={handleMapClick} />

          {/* LAYER 1: Study Corridor Extent Box */}
          {isLayerVisible('study_bounds') && (
            <Rectangle
              bounds={corridorBounds}
              pathOptions={{
                color: '#2C221E',
                weight: 2,
                dashArray: '6, 6',
                fillColor: '#25345B',
                fillOpacity: 0.05,
              }}
            >
              <Popup>
                <div className="text-xs p-1">
                  <div className="font-bold text-[#2C221E] uppercase tracking-wide">
                    Yamuna Study Corridor Boundary
                  </div>
                  <div className="mt-1 text-[#3E3026]">
                    <div><b>West:</b> 76.85° E | <b>East:</b> 77.60° E</div>
                    <div><b>South:</b> 28.50° N | <b>North:</b> 30.40° N</div>
                    <div className="mt-1 text-[11px] text-[#635347]">
                      Spatial Domain: Hathnikund Barrage to Delhi Old Railway Bridge / Okhla.
                    </div>
                  </div>
                </div>
              </Popup>
            </Rectangle>
          )}

          {/* LAYER 2: River Centerline GeoJSON */}
          {isLayerVisible('main_yamuna') && isValidGeoJSON(riverGeoJSON) && (
            <GeoJSON
              key="map-river"
              data={riverGeoJSON as any}
              style={{
                color: '#2563EB',
                weight: 3.5,
                opacity: 0.85,
              }}
              onEachFeature={(feature, layer) => {
                const props = feature.properties || {};
                layer.bindPopup(`
                  <div style="font-family: sans-serif; font-size: 12px; color: #1e293b; min-width: 180px;">
                    <div style="font-weight: 700; color: #1d4ed8; font-size: 13px;">${props.name || 'Yamuna River Centerline'}</div>
                    <div style="margin-top: 4px; color: #475569;">Segment: <b>${props.feature_id || props.segment_id || 'YAM_MAIN'}</b></div>
                    <div style="color: #475569;">Type: <b>${props.waterway_type || 'Main River'}</b></div>
                    ${props.length_km ? `<div style="color: #475569;">Length: <b>${props.length_km} km</b></div>` : ''}
                    <div style="margin-top: 6px; padding-top: 4px; border-top: 1px solid #e2e8f0; font-size: 10px; color: #64748b;">
                      Source: OpenStreetMap Relation 326077<br/>
                      Attribution: © OpenStreetMap contributors (ODbL)
                    </div>
                  </div>
                `);
              }}
            />
          )}

          {/* LAYER: 1D Muskingum Flood Wave Progression (Phase 3E.4) */}
          {isLayerVisible('routing_wave') && spatialRoutingData && (() => {
            const currentStep = spatialRoutingData.time_steps[activeStepIndex] || spatialRoutingData.time_steps[0];
            if (!currentStep) return null;

            return (
              <>
                {currentStep.points.map((pt) => {
                  const isHKB = pt.value_type === 'OBSERVED';
                  const isORB = pt.value_type === 'SIMULATED';
                  const isStation = pt.is_monitoring_station;

                  let fillColor = '#3B82F6';
                  if (isHKB) fillColor = '#059669';
                  else if (isORB) fillColor = '#7C3AED';
                  else if (pt.discharge_cumecs > 4500) fillColor = '#DC2626';
                  else if (pt.discharge_cumecs > 2000) fillColor = '#EA580C';
                  else if (pt.discharge_cumecs > 800) fillColor = '#D97706';

                  const radius = isStation
                    ? (isHKB || isORB ? 9 : 7)
                    : Math.max(3.5, Math.min(8, 3.5 + (pt.discharge_cumecs / 1500)));

                  return (
                    <CircleMarker
                      key={`${pt.station_id}-${currentStep.step_index}`}
                      center={[pt.latitude, pt.longitude]}
                      radius={radius}
                      pathOptions={{
                        fillColor: fillColor,
                        fillOpacity: isStation ? 0.95 : 0.85,
                        color: isHKB || isORB ? '#FFFFFF' : '#3E3026',
                        weight: isHKB || isORB ? 2.5 : 1,
                      }}
                      eventHandlers={{
                        click: () => setSelectedRoutingPoint(pt),
                      }}
                    >
                      <Popup>
                        <div className="text-xs p-1 min-w-[220px] text-[#3E3026]">
                          <div className="font-bold border-b border-[#EAE3D9] pb-1 flex items-center justify-between">
                            <span className="font-semibold text-[13px]" style={{ color: isHKB ? '#059669' : isORB ? '#7C3AED' : '#2C221E' }}>
                              {pt.name}
                            </span>
                            <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded uppercase tracking-wider ${
                              isHKB ? 'bg-emerald-100 text-emerald-800' : isORB ? 'bg-purple-100 text-purple-800' : 'bg-teal-100 text-teal-800'
                            }`}>
                              {pt.value_type}
                            </span>
                          </div>

                          <div className="mt-2 space-y-1">
                            <div className="flex justify-between">
                              <span className="text-[#635347]">Chainage:</span>
                              <span className="font-mono font-bold">Km {pt.chainage_km.toFixed(1)}</span>
                            </div>
                            <div className="flex justify-between items-baseline">
                              <span className="text-[#635347]">1D Routed Flow:</span>
                              <span className="font-mono font-bold text-sm" style={{ color: fillColor }}>
                                {pt.discharge_cumecs.toLocaleString()} m³/s
                              </span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-[#635347]">Simulation Date:</span>
                              <span className="font-mono font-medium">{currentStep.date}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-[#635347]">Reach:</span>
                              <span className="font-mono text-[10px] text-[#8B4513]">{pt.reach_id}</span>
                            </div>
                            <div className="mt-1 pt-1 border-t border-[#EAE3D9] text-[10px] text-[#2C221E]">
                              <b>Provenance:</b> {pt.data_provenance}
                            </div>
                            <div className="text-[9px] text-[#635347] italic pt-0.5">
                              1D channel routing representation; does NOT indicate water depth or flood inundation extent.
                            </div>
                          </div>
                        </div>
                      </Popup>
                    </CircleMarker>
                  );
                })}
              </>
            );
          })()}


          {/* LAYER: Upstream Himalayan Catchment Polygon (Phase 3D) */}
          {isLayerVisible('upstream_catchment') && isValidGeoJSON(catchmentGeoJSON) && (
            <GeoJSON
              key="map-catchment"
              data={catchmentGeoJSON}
              style={{
                color: '#4338CA',
                weight: 2.5,
                dashArray: '5, 5',
                fillColor: '#6366F1',
                fillOpacity: 0.12,
              }}
              onEachFeature={(feature, layer) => {
                const props = feature.properties || {};
                layer.bindPopup(`
                  <div style="font-family: sans-serif; font-size: 12px; color: #3E3026; min-width: 200px;">
                    <div style="font-weight: 700; color: #4338CA; border-bottom: 1px solid #EAE3D9; padding-bottom: 3px;">
                      ${props.name || 'Upper Yamuna Catchment'}
                    </div>
                    <div style="margin-top: 6px; line-height: 1.4;">
                      <div><b>Drainage Area:</b> 11,112 km² (CWC Basin Benchmark)</div>
                      <div><b>Outlet Pour Point:</b> ${props.pour_point || 'Hathnikund Barrage'}</div>
                      <div><b>Elevation Range:</b> ${props.elevation_min_m || 295}m to ${props.elevation_max_m || 6387}m MSL</div>
                      <div><b>Primary Inflow:</b> ${props.primary_tributary || 'Tons River (~60%)'}</div>
                      <div style="margin-top: 4px; font-size: 10px; color: #635347; font-style: italic;">
                        Natural watershed divide distinct from downstream corridor.
                      </div>
                    </div>
                  </div>
                `);
              }}
            />
          )}

          {/* LAYER: DEM-Derived Contributing Drainage Lines (Phase 3D) */}
          {isLayerVisible('catchment_drainage') && isValidGeoJSON(drainageGeoJSON) && (
            <GeoJSON
              key="map-drainage"
              data={drainageGeoJSON}
              style={{
                color: '#0284C7',
                weight: 2.2,
                opacity: 0.9,
              }}
              onEachFeature={(feature, layer) => {
                const props = feature.properties || {};
                layer.bindPopup(`
                  <div style="font-family: sans-serif; font-size: 12px; color: #3E3026;">
                    <div style="font-weight: 700; color: #0284C7;">
                      ${props.river_name || 'Himalayan Stream Channel'}
                    </div>
                    <div style="margin-top: 4px;">
                      <b>Stream Order:</b> ${props.stream_order || 4}
                    </div>
                    <div style="font-size: 10px; color: #635347;">
                      Contributing tributary to Hathnikund Barrage
                    </div>
                  </div>
                `);
              }}
            />
          )}

          {/* LAYER: Spatial Rainfall Grid Sampling Nodes (Phase 3D) */}
          {isLayerVisible('catchment_rainfall_grid') &&
            rainfallSummary &&
            rainfallSummary.sample_grid_points.map((pt) => {
              const acc = pt.forecast_24h_mm;
              const circleColor =
                acc > 25 ? '#DC2626' : acc > 10 ? '#D97706' : acc > 2 ? '#0284C7' : '#059669';

              return (
                <CircleMarker
                  key={pt.id}
                  center={[pt.latitude, pt.longitude]}
                  radius={7}
                  pathOptions={{
                    fillColor: circleColor,
                    fillOpacity: 0.85,
                    color: '#FFFFFF',
                    weight: 1.5,
                  }}
                >
                  <Popup>
                    <div className="text-xs p-1 min-w-[210px] text-[#3E3026]">
                      <div className="font-bold text-[#2C221E] border-b border-[#EAE3D9] pb-1 flex items-center justify-between">
                        <span>{pt.name}</span>
                        <span className="text-[10px] font-mono text-[#635347]">~{pt.elevation_m}m</span>
                      </div>
                      <div className="mt-1.5 space-y-1">
                        <div className="flex justify-between">
                          <span className="text-[#635347]">Current Precip:</span>
                          <span className="font-mono font-bold text-[#0284C7]">{pt.current_mm.toFixed(2)} mm/h</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-[#635347]">24h Forecast:</span>
                          <span className="font-mono font-bold text-[#0284C7]">{pt.forecast_24h_mm.toFixed(1)} mm</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-[#635347]">API-3 Soil Proxy:</span>
                          <span className="font-mono font-bold text-[#8B4513]">{pt.api_3_mm.toFixed(1)} mm</span>
                        </div>
                        <div className="text-[10px] text-[#635347] font-mono pt-0.5">
                          Coord: {pt.latitude.toFixed(2)}°N, {pt.longitude.toFixed(2)}°E
                        </div>
                      </div>
                      <div className="mt-2 pt-1 border-t border-[#EAE3D9]">
                        <button
                          onClick={() => onSelectCoordinate?.(pt.latitude, pt.longitude, pt.name)}
                          className="w-full py-1 text-center font-medium bg-[#8B4513] text-[#FFFFFF] rounded text-[11px] hover:bg-[#70360E] transition-colors"
                        >
                          Query Detailed Node Forecast
                        </button>
                      </div>
                    </div>
                  </Popup>
                </CircleMarker>
              );
            })}

          {/* LAYER 3: Corridor Stations (Hathnikund, Delhi ORB, etc.) */}
          {isLayerVisible('corridor_stations') &&
            stations.map((stn) => {
              const isBarrage = stn.station_type === 'BARRAGE';
              const pinColor = isBarrage ? '#991B1B' : '#8B4513';
              const label = isBarrage ? 'BRG' : 'STN';
              return (
                <Marker
                  key={stn.id}
                  position={[stn.latitude, stn.longitude]}
                  icon={createCustomPin(pinColor, label, isBarrage)}
                >
                  <Popup>
                    <div className="text-xs p-1 min-w-[200px]">
                      <div className="font-bold text-[#2C221E] border-b border-[#EAE3D9] pb-1">
                        {stn.name}
                      </div>
                      <div className="mt-1.5 space-y-0.5 text-[#3E3026]">
                        <div><b>Type:</b> {stn.station_type}</div>
                        <div><b>Coordinates:</b> {stn.latitude.toFixed(3)}°N, {stn.longitude.toFixed(3)}°E</div>
                        {stn.chainage_km !== null && (
                          <div><b>Chainage:</b> Km {stn.chainage_km?.toFixed(1)}</div>
                        )}
                        {stn.danger_level_m && (
                          <div className="text-red-700 font-semibold">
                            <b>Danger Level:</b> {stn.danger_level_m.toFixed(2)} m
                          </div>
                        )}
                      </div>
                      <div className="mt-2 pt-1 border-t border-[#EAE3D9]">
                        <button
                          onClick={() => onSelectCoordinate?.(stn.latitude, stn.longitude, stn.name)}
                          className="w-full py-1 text-center font-medium bg-[#8B4513] text-[#FFFFFF] rounded text-[11px] hover:bg-[#70360E] transition-colors"
                        >
                          Query Weather & Forecast
                        </button>
                      </div>
                    </div>
                  </Popup>
                </Marker>
              );
            })}

          {/* LAYER: Designated DDMA Relief Shelters */}
          {isLayerVisible('shelters') && isValidGeoJSON(sheltersGeoJSON) && (
            <GeoJSON
              key="map-shelters"
              data={sheltersGeoJSON}
              pointToLayer={(_feature, latlng) => {
                return L.circleMarker(latlng, {
                  radius: 7,
                  fillColor: '#8B5CF6',
                  color: '#FFFFFF',
                  weight: 2,
                  opacity: 1,
                  fillOpacity: 0.9,
                });
              }}
              onEachFeature={(feature, layer) => {
                const p = feature.properties || {};
                layer.bindPopup(`
                  <div style="font-family: sans-serif; font-size: 12px; color: #3E3026; min-width: 220px;">
                    <div style="font-weight: 700; color: #6D28D9; border-bottom: 1px solid #EAE3D9; padding-bottom: 4px;">
                      ${p.name || 'Relief Shelter'}
                    </div>
                    <div style="margin-top: 6px; line-height: 1.4;">
                      <div><b>Zone:</b> ${p.zone || 'Delhi NCT'}</div>
                      <div><b>Capacity:</b> ${p.capacity_persons ? p.capacity_persons.toLocaleString() : 'N/A'} persons</div>
                      <div><b>Elevation:</b> ${p.elevation_msl || 'N/A'} m MSL</div>
                      <div><b>Distance to River:</b> ${p.distance_to_river_m || 'N/A'} m</div>
                      <div><b>Agency:</b> ${p.contact_agency || 'DDMA'}</div>
                      <div><b>Status:</b> <span style="color: #6D28D9; font-weight: bold;">Illustrative Prototype (Unvalidated)</span></div>
                      <div style="margin-top: 4px; font-size: 10px; color: #4B5563;">
                        <b>Facilities:</b> ${(p.facilities || []).join(', ')}
                      </div>
                      <div style="margin-top: 4px; font-size: 9px; color: #9CA3AF; font-style: italic;">
                        Illustrative reference location; unvalidated for emergency navigation.
                      </div>
                    </div>
                  </div>
                `);
              }}
            />
          )}

          {/* LAYER: Emergency Evacuation Corridors */}
          {isLayerVisible('evacuation_corridors') && isValidGeoJSON(corridorsGeoJSON) && (
            <GeoJSON
              key="map-corridors"
              data={corridorsGeoJSON}
              style={{
                color: '#D97706',
                weight: 3.5,
                dashArray: '6, 6',
                opacity: 0.9,
              }}
              onEachFeature={(feature, layer) => {
                const p = feature.properties || {};
                layer.bindPopup(`
                  <div style="font-family: sans-serif; font-size: 12px; color: #3E3026; min-width: 200px;">
                    <div style="font-weight: 700; color: #B45309; border-bottom: 1px solid #EAE3D9; padding-bottom: 4px;">
                      ${p.name || 'Evacuation Corridor'}
                    </div>
                    <div style="margin-top: 6px; line-height: 1.4;">
                      <div><b>Origin:</b> ${p.origin_zone}</div>
                      <div><b>Distance:</b> ${p.distance_km} km</div>
                      <div><b>Transit Mode:</b> ${p.transit_mode}</div>
                      <div><b>Priority:</b> <span style="font-weight: bold; color: #B45309;">${p.priority_level}</span></div>
                      <div><b>Status:</b> <span style="color: #B45309; font-weight: bold;">Illustrative Vector Prototype</span></div>
                      <div style="margin-top: 4px; font-size: 9px; color: #9CA3AF; font-style: italic;">
                        Route geometry and elevation unvalidated for flood clearance.
                      </div>
                    </div>
                  </div>
                `);
              }}
            />
          )}

          {/* User Selected / Clicked Point Marker */}
          {activeCursorCoords && (
            <Marker
              position={[activeCursorCoords.lat, activeCursorCoords.lon]}
              icon={createCustomPin('#D97706', 'LOC', false)}
            >
              <Popup>
                <div className="text-xs p-1 min-w-[190px]">
                  <div className="font-bold text-[#2C221E]">Selected Geographic Point</div>
                  <div className="mt-1 font-mono text-[11px] text-[#3E3026]">
                    Lat: {activeCursorCoords.lat.toFixed(4)}°N<br />
                    Lon: {activeCursorCoords.lon.toFixed(4)}°E
                  </div>
                  <div className="mt-2">
                    <button
                      onClick={() =>
                        onSelectCoordinate?.(
                          activeCursorCoords.lat,
                          activeCursorCoords.lon,
                          `Point (${activeCursorCoords.lat.toFixed(2)}N, ${activeCursorCoords.lon.toFixed(2)}E)`
                        )
                      }
                      className="w-full py-1 text-center font-medium bg-[#8B4513] text-[#FFFFFF] rounded text-[11px] hover:bg-[#70360E] transition-colors"
                    >
                      Retrieve Weather at Point
                    </button>
                  </div>
                </div>
              </Popup>
            </Marker>
          )}
        </MapContainer>
        </ErrorBoundary>

        {/* Selected Chainage Point Inspection Card (Phase 3E.4) */}
        {selectedRoutingPoint && (
          <div className="absolute top-3 left-3 bg-[#FFFFFF]/95 backdrop-blur-xs border border-[#EAE3D9] rounded-lg shadow-lg z-20 p-3 max-w-xs text-xs pointer-events-auto">
            <div className="flex items-center justify-between pb-1 border-b border-[#EAE3D9]">
              <span className="font-bold text-[#2C221E] text-[13px]">{selectedRoutingPoint.name}</span>
              <button
                onClick={() => setSelectedRoutingPoint(null)}
                className="text-[#635347] hover:text-[#3E3026] text-sm font-bold ml-2"
              >
                &times;
              </button>
            </div>
            <div className="mt-2 space-y-1 text-[#3E3026]">
              <div className="flex justify-between">
                <span className="text-[#635347]">Thalweg Chainage:</span>
                <span className="font-mono font-bold">Km {selectedRoutingPoint.chainage_km.toFixed(1)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#635347]">Coordinates:</span>
                <span className="font-mono text-[10px] text-[#8B4513]">
                  {selectedRoutingPoint.latitude.toFixed(3)}°N, {selectedRoutingPoint.longitude.toFixed(3)}°E
                </span>
              </div>
              <div className="flex justify-between items-baseline">
                <span className="text-[#635347]">1D Flow Rate:</span>
                <span className="font-mono font-bold text-sm text-[#2563EB]">
                  {selectedRoutingPoint.discharge_cumecs.toLocaleString()} m³/s
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-[#635347]">Value Type:</span>
                <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded uppercase tracking-wider ${
                  selectedRoutingPoint.value_type === 'OBSERVED'
                    ? 'bg-emerald-100 text-emerald-800'
                    : selectedRoutingPoint.value_type === 'SIMULATED'
                    ? 'bg-purple-100 text-purple-800'
                    : 'bg-teal-100 text-teal-800'
                }`}>
                  {selectedRoutingPoint.value_type}
                </span>
              </div>
              <div className="text-[10px] text-[#635347] pt-1 border-t border-[#EAE3D9]/60">
                <b>Provenance:</b> {selectedRoutingPoint.data_provenance}
              </div>
            </div>
          </div>
        )}

        {/* Floating Layer Control Drawer */}
        {showLayerDrawer && (
          <div className="absolute top-3 right-3 w-80 max-h-[88%] bg-[#FFFFFF]/95 backdrop-blur-xs border border-[#EAE3D9] rounded-lg shadow-lg z-20 flex flex-col overflow-hidden">
            <div className="px-3 py-2 bg-[#F5EFEB] border-b border-[#EAE3D9] flex items-center justify-between">
              <span className="text-xs font-bold text-[#2C221E] uppercase tracking-wide">
                GIS Layer Control & Catalog
              </span>
              <button
                onClick={() => setShowLayerDrawer(false)}
                className="text-[#635347] hover:text-[#3E3026] text-sm font-bold"
              >
                &times;
              </button>
            </div>

            <div className="p-2.5 overflow-y-auto space-y-2 text-xs">
              <div className="text-[11px] text-[#635347] italic pb-1 border-b border-[#EAE3D9]/60">
                Data Integrity Guardrail: Only verified layers with active source data in repository can be toggled.
              </div>

              {layers.map((layer) => {
                const isAvail = layer.status === 'AVAILABLE';
                return (
                  <div
                    key={layer.id}
                    className={`p-2 rounded border transition-colors ${
                      isAvail
                        ? layer.visible
                          ? 'bg-[#FFFFFF] border-[#8B4513]/40 shadow-xs'
                          : 'bg-[#FBF9F5]/50 border-[#EAE3D9]'
                        : 'bg-gray-100/60 border-gray-200 opacity-60 cursor-not-allowed'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <label className="flex items-center gap-2 cursor-pointer font-medium text-[#3E3026]">
                        <input
                          type="checkbox"
                          checked={layer.visible && isAvail}
                          disabled={!isAvail}
                          onChange={() => handleToggleLayer(layer.id)}
                          className="rounded text-[#8B4513] focus:ring-[#8B4513] accent-[#8B4513]"
                        />
                        <span className="flex items-center gap-1.5">
                          <span
                            className="w-2.5 h-2.5 rounded-full inline-block"
                            style={{ backgroundColor: layer.color }}
                          ></span>
                          {layer.name}
                        </span>
                      </label>

                      {/* Status Badge */}
                      <span
                        className={`text-[9px] font-bold px-1.5 py-0.5 rounded uppercase tracking-wider ${
                          isAvail
                            ? 'bg-emerald-100 text-emerald-800'
                            : 'bg-amber-100 text-amber-800'
                        }`}
                      >
                        {layer.status === 'AVAILABLE' ? 'AVAILABLE' : 'UNAVAILABLE'}
                      </span>
                    </div>

                    <div className="mt-1 pl-5 text-[11px] text-[#635347] leading-tight">
                      {layer.description}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Floating Wave Timeline Controller (Phase 3E.4) */}
        {isLayerVisible('routing_wave') && spatialRoutingData && (() => {
          const currentStep = spatialRoutingData.time_steps[activeStepIndex] || spatialRoutingData.time_steps[0];
          const totalSteps = spatialRoutingData.time_steps.length;

          return (
            <div className="absolute bottom-4 left-1/2 -translate-x-1/2 bg-[#FFFFFF]/95 backdrop-blur-xs border border-[#EAE3D9] rounded-xl shadow-xl z-20 px-4 py-2.5 max-w-lg w-full pointer-events-auto">
              <div className="flex items-center justify-between gap-3 mb-1">
                <div className="flex items-center gap-1.5">
                  <Activity className="w-4 h-4 text-[#8B4513]" />
                  <span className="text-xs font-bold text-[#2C221E] uppercase tracking-wide">
                    1D Muskingum Flood Wave Progression
                  </span>
                </div>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#F5EFEB] text-[#2C221E] font-semibold">
                  {spatialRoutingData.episode_id || 'EPISODE_2023_08'} (K=36h, x=0.2)
                </span>
              </div>

              {/* Date, Navigation, and Playback Controls */}
              <div className="flex items-center justify-between gap-2 my-1">
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => setActiveStepIndex((prev) => Math.max(0, prev - 1))}
                    disabled={activeStepIndex === 0}
                    title="Previous Day"
                    className="p-1 rounded bg-[#F5EFEB] hover:bg-[#EAE3D9] text-[#2C221E] disabled:opacity-40 transition-colors"
                  >
                    <ChevronLeft className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => setIsPlayingWave(!isPlayingWave)}
                    title={isPlayingWave ? 'Pause Wave Animation' : 'Play Wave Animation'}
                    className="px-2 py-1 rounded bg-[#8B4513] hover:bg-[#70360E] text-[#FFFFFF] text-xs font-medium flex items-center gap-1 transition-colors"
                  >
                    {isPlayingWave ? (
                      <>
                        <Pause className="w-3.5 h-3.5" /> Pause
                      </>
                    ) : (
                      <>
                        <Play className="w-3.5 h-3.5" /> Animate
                      </>
                    )}
                  </button>
                  <button
                    onClick={() => setActiveStepIndex((prev) => Math.min(totalSteps - 1, prev + 1))}
                    disabled={activeStepIndex === totalSteps - 1}
                    title="Next Day"
                    className="p-1 rounded bg-[#F5EFEB] hover:bg-[#EAE3D9] text-[#2C221E] disabled:opacity-40 transition-colors"
                  >
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>

                {/* Current Date Display */}
                <div className="text-center">
                  <span className="font-mono font-bold text-sm text-[#3E3026]">{currentStep?.date}</span>
                  <span className="text-[10px] text-[#635347] ml-1.5">
                    ({activeStepIndex + 1}/{totalSteps})
                  </span>
                </div>

                {/* Reset button */}
                <button
                  onClick={() => {
                    setIsPlayingWave(false);
                    const pIdx = spatialRoutingData.time_steps.findIndex(s => s.date === spatialRoutingData.peak_observed_inflow_date);
                    setActiveStepIndex(pIdx >= 0 ? pIdx : 0);
                  }}
                  title="Jump to Peak Inflow Date"
                  className="text-[10px] font-medium px-2 py-1 rounded bg-[#F5EFEB] hover:bg-[#EAE3D9] text-[#2C221E] flex items-center gap-1"
                >
                  <RotateCcw className="w-3 h-3" /> Peak
                </button>
              </div>

              {/* Timeline Slider */}
              <div className="w-full mt-1">
                <input
                  type="range"
                  min={0}
                  max={totalSteps - 1}
                  value={activeStepIndex}
                  onChange={(e) => {
                    setIsPlayingWave(false);
                    setActiveStepIndex(parseInt(e.target.value, 10));
                  }}
                  className="w-full h-1.5 bg-[#EAE3D9] rounded-lg appearance-none cursor-pointer accent-[#8B4513]"
                />
              </div>

              {/* Key Inflow / Outflow Telemetry */}
              <div className="grid grid-cols-2 gap-2 mt-1.5 pt-1 border-t border-[#EAE3D9]/70 text-[11px]">
                <div className="flex items-center justify-between px-2 py-0.5 bg-emerald-50 rounded border border-emerald-200">
                  <span className="text-emerald-900 font-medium">Observed Release (HKB):</span>
                  <span className="font-mono font-bold text-emerald-800">
                    {currentStep?.observed_inflow_cumecs.toLocaleString()} m³/s
                  </span>
                </div>
                <div className="flex items-center justify-between px-2 py-0.5 bg-purple-50 rounded border border-purple-200">
                  <span className="text-purple-900 font-medium">Simulated Outflow (ORB):</span>
                  <span className="font-mono font-bold text-purple-800">
                    {currentStep?.simulated_outflow_cumecs.toLocaleString()} m³/s
                  </span>
                </div>
              </div>
            </div>
          );
        })()}

        {/* Map Legend Overlay (Bottom Left) */}
        <div className="absolute bottom-3 left-3 bg-[#FFFFFF]/95 backdrop-blur-xs border border-[#EAE3D9] rounded p-2.5 text-xs shadow-md z-20 max-w-xs pointer-events-auto">
          <div className="font-bold text-[#2C221E] mb-1.5 text-[11px] uppercase tracking-wider">
            Cartographic Legend
          </div>
          <div className="space-y-1 text-[11px] text-[#3E3026]">
            <div className="flex items-center gap-2">
              <span className="w-3.5 h-1 border-t-2 border-dashed border-[#2C221E]"></span>
              <span>Study Corridor Extent (Hathnikund to Delhi)</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3.5 h-1 border-t-2 border-dashed border-[#4338CA]"></span>
              <span>Hathnikund Upstream Catchment (11,112 km²)</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3.5 h-1 bg-[#0284C7]"></span>
              <span>Catchment Contributing Drainage (Tons, Giri, etc.)</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-[#0D9488]"></span>
              <span>Spatial Rainfall Nodes (20 Basin Points)</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-[#991B1B] text-[8px] text-white flex items-center justify-center font-bold">
                B
              </span>
              <span>Barrage Boundary (Hathnikund / Okhla)</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-[#8B4513] text-[8px] text-white flex items-center justify-center font-bold">
                S
              </span>
              <span>Corridor Monitoring Station</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3.5 h-1 bg-[#2563EB]"></span>
              <span>Main Yamuna River Centerline</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-[#059669]"></span>
              <span>Wave Inflow [OBSERVED HKB]</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-[#7C3AED]"></span>
              <span>Wave Outflow [SIMULATED ORB]</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-[#DC2626]"></span>
              <span>Peak Wave Thalweg Surge (&gt;4,000 m³/s)</span>
            </div>
          </div>
          {activeCursorCoords && (
            <div className="mt-2 pt-1.5 border-t border-[#EAE3D9] font-mono text-[10px] text-[#635347]">
              Active Click: {activeCursorCoords.lat.toFixed(4)}°N, {activeCursorCoords.lon.toFixed(4)}°E
            </div>
          )}
        </div>

      </div>
    </div>
  );
};
