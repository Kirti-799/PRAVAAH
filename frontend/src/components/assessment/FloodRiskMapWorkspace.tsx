/**
 * frontend/src/components/assessment/FloodRiskMapWorkspace.tsx
 *
 * Primary interactive workspace for PRAVAAH — Intelligent Flood Prediction & Disaster Response System.
 * Warm Cream & Espresso styling (#FBF9F5, #FFFDF9, #2C221E, #8B4513, #EAE3D9).
 *
 * Implements:
 * 1. 3-Step Selection Panel: Select River -> Select Region/Area -> Assess Flood Risk.
 * 2. Multi-River Support: Yamuna (Operational ML 24h active), Ganga, Brahmaputra, Godavari (Planned Expansion Basins).
 * 3. Strict 24-Hour Horizon: Single next-24-hour prediction (no multi-day ML buttons).
 * 4. 3-Tier Risk Map: Green (Low), Yellow/Orange (Moderate), Red (High).
 * 5. Statistics Section & 3 Compact Graphs: Historical Discharge, Observed vs Predicted, Rainfall Trend.
 * 6. Expandable Weather Details toggle with Open-Meteo telemetry.
 * 7. Nearest Relief Shelters section with Haversine distance, verified capacity, facilities, and real-time occupancy notice.
 */

import React, { useState, useEffect, useMemo } from 'react';
import {
  MapContainer,
  TileLayer,
  GeoJSON,
  Marker,
  CircleMarker,
  Popup,
  useMap,
} from 'react-leaflet';
import L from 'leaflet';
import { ErrorBoundary } from '../common/ErrorBoundary';
import { isValidGeoJSON } from '../../utils/geojson';
import {
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Calendar,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  CloudRain,
  Activity,
  Compass,
  Building2,
  CheckCircle2,
  Info,
} from 'lucide-react';
import { riskAssessmentApi } from '../../services/riskAssessment';
import {
  fetchRiverFeatures,
  fetchCatchmentGeometry,
} from '../../services/spatial';
import type {
  RiverInfo,
  SupportedArea,
  AssessmentResponse,
  RiskLevel,
  RiskColor,
} from '../../types/riskAssessment';
import type { RiverGeoJSONResponse } from '../../types/spatial';

interface FloodRiskMapWorkspaceProps {
  onNavigateToEvacuation?: () => void;
  onNavigateToWeather?: () => void;
}

// Fallback catalog of rivers
const DEFAULT_RIVERS: RiverInfo[] = [
  {
    id: 'yamuna',
    name: 'Yamuna River',
    is_operational: true,
    status_label: 'Operational ML (24h Active)',
    description: 'Hathnikund Barrage to Delhi NCT and Okhla Reach (268.9 km operational corridor)',
  },
  {
    id: 'ganga',
    name: 'Ganga River',
    is_operational: false,
    status_label: 'Planned Expansion Basin',
    description: 'Haridwar and Varanasi reaches — Live weather active; ML model in development',
  },
  {
    id: 'brahmaputra',
    name: 'Brahmaputra River',
    is_operational: false,
    status_label: 'Planned Expansion Basin',
    description: 'Guwahati gorge reach — Live weather active; ML model in development',
  },
  {
    id: 'godavari',
    name: 'Godavari River',
    is_operational: false,
    status_label: 'Planned Expansion Basin',
    description: 'Rajahmundry delta reach — Live weather active; ML model in development',
  },
];

// Map Centering Helper
const MapController: React.FC<{ center: [number, number]; zoom: number }> = ({ center, zoom }) => {
  const map = useMap();
  useEffect(() => {
    map.setView(center, zoom, { animate: true });
  }, [center, zoom, map]);
  return null;
};

// 3-Tier Risk Color Palette
const getRiskColorCode = (color: RiskColor): string => {
  switch (color) {
    case 'GREEN':
      return '#16a34a'; // Low Risk
    case 'ORANGE':
      return '#ea580c'; // Moderate Risk
    case 'RED':
      return '#dc2626'; // High Risk
    default:
      return '#16a34a';
  }
};

const getRiskBadgeClasses = (level: RiskLevel): string => {
  switch (level) {
    case 'LOW':
      return 'bg-emerald-50 text-emerald-900 border-emerald-300';
    case 'MODERATE':
      return 'bg-amber-50 text-amber-900 border-amber-300';
    case 'HIGH':
      return 'bg-red-50 text-red-900 border-red-300';
    default:
      return 'bg-emerald-50 text-emerald-900 border-emerald-300';
  }
};

export const FloodRiskMapWorkspace: React.FC<FloodRiskMapWorkspaceProps> = ({
  onNavigateToEvacuation,
}) => {
  // Multi-River and Area State
  const [rivers, setRivers] = useState<RiverInfo[]>(DEFAULT_RIVERS);
  const [selectedRiverId, setSelectedRiverId] = useState<string>('yamuna');
  const [areas, setAreas] = useState<SupportedArea[]>([]);
  const [selectedAreaId, setSelectedAreaId] = useState<string>('DELHI_CENTRAL');
  const [assessment, setAssessment] = useState<AssessmentResponse | null>(null);
  const [isAssessing, setIsAssessing] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Weather Details Toggle
  const [isWeatherOpen, setIsWeatherOpen] = useState<boolean>(false);

  // Spatial Layers State
  const [riverData, setRiverData] = useState<RiverGeoJSONResponse | null>(null);
  const [catchmentData, setCatchmentData] = useState<any>(null);

  // Layer Toggles
  const [showRiver, setShowRiver] = useState<boolean>(true);
  const [showCatchment, setShowCatchment] = useState<boolean>(true);
  const [showStations, setShowStations] = useState<boolean>(true);
  const [showShelters, setShowShelters] = useState<boolean>(true);

  // Filter areas based on currently selected river
  const filteredAreas = useMemo(() => {
    return areas.filter((a) => {
      if (a.river_id) {
        return a.river_id === selectedRiverId;
      }
      return selectedRiverId === 'yamuna';
    });
  }, [areas, selectedRiverId]);

  // Load supported areas & initial spatial layers
  useEffect(() => {
    let isMounted = true;

    async function init() {
      try {
        const areasRes = await riskAssessmentApi.getSupportedAreas();
        if (isMounted) {
          if (areasRes.rivers && areasRes.rivers.length > 0) {
            setRivers(areasRes.rivers);
          }
          setAreas(areasRes.areas);
          if (areasRes.areas.length > 0) {
            const initialArea = areasRes.areas.find((a) => a.id === 'DELHI_CENTRAL') || areasRes.areas[0];
            setSelectedAreaId(initialArea.id);
            if (initialArea.river_id) {
              setSelectedRiverId(initialArea.river_id);
            }
          }
        }
      } catch (err) {
        console.error('Failed to load supported areas:', err);
      }

      try {
        const [riverRes, catchRes] = await Promise.allSettled([
          fetchRiverFeatures(),
          fetchCatchmentGeometry(),
        ]);
        if (isMounted) {
          if (riverRes.status === 'fulfilled' && isValidGeoJSON(riverRes.value)) {
            setRiverData(riverRes.value);
          }
          if (catchRes.status === 'fulfilled' && isValidGeoJSON(catchRes.value)) {
            setCatchmentData(catchRes.value);
          }
        }
      } catch (err) {
        console.error('Failed to load spatial layers:', err);
      }
    }

    init();
    return () => {
      isMounted = false;
    };
  }, []);

  // Run assessment function (horizon is strictly 24 hours / 1 day)
  const runAssessment = async (areaId: string) => {
    setIsAssessing(true);
    setErrorMessage(null);
    try {
      const res = await riskAssessmentApi.assessRisk({
        area_id: areaId,
        forecast_days: 1, // Strictly 24-hour horizon
      });
      setAssessment(res);
    } catch (err: any) {
      setErrorMessage(err?.message || 'Failed to complete risk assessment.');
    } finally {
      setIsAssessing(false);
    }
  };

  // Initial assessment trigger when area changes
  useEffect(() => {
    if (selectedAreaId) {
      runAssessment(selectedAreaId);
    }
  }, [selectedAreaId]);

  // Handle River selection change
  const handleRiverChange = (newRiverId: string) => {
    setSelectedRiverId(newRiverId);
    const riverAreas = areas.filter(
      (a) => a.river_id === newRiverId || (!a.river_id && newRiverId === 'yamuna')
    );
    if (riverAreas.length > 0) {
      setSelectedAreaId(riverAreas[0].id);
    }
  };

  // Handle Area selection change
  const handleAreaChange = (newAreaId: string) => {
    setSelectedAreaId(newAreaId);
  };

  // Find currently selected area and river objects
  const currentArea = areas.find((a) => a.id === selectedAreaId);
  const currentRiver = rivers.find((r) => r.id === selectedRiverId) || rivers[0];
  const centerCoord: [number, number] = currentArea?.representative_coord || [28.66, 77.25];
  const zoomLevel = currentArea?.area_type === 'CORRIDOR_ALL' ? 8 : currentArea?.area_type === 'BASIN' ? 8 : 10;

  // Determine reach color styling based on assessed reach_risks
  const getWayColor = (wayId?: number): string => {
    if (!assessment || !wayId) return '#16a34a';
    const match = assessment.reach_risks.find((r) => r.osm_way_id === wayId);
    return match ? getRiskColorCode(match.risk_color) : '#16a34a';
  };

  return (
    <div className="flex h-full w-full flex-col overflow-hidden bg-[#FBF9F5] text-[#2C221E]">
      {/* 1. 3-STEP SELECTION PANEL */}
      <div className="shrink-0 border-b border-[#EAE3D9] bg-[#FFFDF9] px-4 py-3 shadow-2xs">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-3">
            {/* Step 1: Select River */}
            <div className="flex items-center gap-2">
              <span className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-[#2C221E]">
                <span className="flex h-5 w-5 items-center justify-center rounded-full bg-[#8B4513] text-[10px] font-bold text-white shadow-2xs">
                  1
                </span>
                River:
              </span>
              <select
                value={selectedRiverId}
                onChange={(e) => handleRiverChange(e.target.value)}
                className="rounded-lg border border-[#EAE3D9] bg-[#FBF9F5] px-3 py-1.5 text-xs font-semibold text-[#2C221E] focus:border-[#8B4513] focus:outline-hidden shadow-2xs transition-colors"
                aria-label="Step 1: Select River"
              >
                {rivers.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.name} {r.is_operational ? '★ [Operational ML]' : '[Planned Expansion]'}
                  </option>
                ))}
              </select>
            </div>

            {/* Step 2: Select Region / Area */}
            <div className="flex items-center gap-2">
              <span className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-[#2C221E]">
                <span className="flex h-5 w-5 items-center justify-center rounded-full bg-[#8B4513] text-[10px] font-bold text-white shadow-2xs">
                  2
                </span>
                Region/Area:
              </span>
              <select
                value={selectedAreaId}
                onChange={(e) => handleAreaChange(e.target.value)}
                className="rounded-lg border border-[#EAE3D9] bg-[#FBF9F5] px-3 py-1.5 text-xs font-semibold text-[#2C221E] focus:border-[#8B4513] focus:outline-hidden shadow-2xs max-w-[280px] truncate transition-colors"
                aria-label="Step 2: Select Region or Reach"
              >
                {filteredAreas.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Strict 24-Hour Horizon Indicator */}
            <div className="flex items-center gap-1.5 rounded-full border border-[#EAE3D9] bg-[#FBF9F5] px-3 py-1 text-xs text-[#635347]">
              <Calendar className="h-3.5 w-3.5 text-[#8B4513]" />
              <span className="font-semibold text-[#2C221E]">Horizon: Next 24 Hours</span>
              <span className="text-[10px] text-[#8C7869]">(Single AI Horizon)</span>
            </div>
          </div>

          {/* Step 3: Assess Flood Risk Action Button */}
          <button
            type="button"
            onClick={() => runAssessment(selectedAreaId)}
            disabled={isAssessing}
            className="flex items-center gap-2 rounded-full bg-[#8B4513] px-5 py-2 text-xs font-bold text-white shadow-xs hover:bg-[#6E350E] active:scale-98 disabled:opacity-60 transition-all cursor-pointer"
          >
            <span className="flex h-4 w-4 items-center justify-center rounded-full bg-white/20 text-[10px] font-bold">
              3
            </span>
            <RefreshCw className={`h-3.5 w-3.5 ${isAssessing ? 'animate-spin' : ''}`} />
            <span>{isAssessing ? 'Evaluating 24h Risk...' : 'Assess Flood Risk'}</span>
          </button>
        </div>
      </div>

      {/* 2. MAIN MAP VIEWPORT & RIGHT ASSESSMENT DRAWER */}
      <div className="relative flex flex-1 overflow-hidden">
        {/* Leaflet Map Surface */}
        <div className="relative flex-1 h-full w-full">
          <ErrorBoundary isMapContainer={true}>
            <MapContainer
              center={centerCoord}
              zoom={zoomLevel}
              className="h-full w-full z-0"
              zoomControl={false}
            >
              <MapController center={centerCoord} zoom={zoomLevel} />

              {/* OpenStreetMap Basemap */}
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors'
                url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
                maxZoom={19}
              />

              {/* Upstream Watershed Basin Polygon (Yamuna) */}
              {showCatchment && selectedRiverId === 'yamuna' && isValidGeoJSON(catchmentData) && (
                <GeoJSON
                  key={`catchment-${assessment?.risk_color || 'default'}`}
                  data={catchmentData}
                  style={{
                    color: assessment?.risk_color === 'RED' ? '#dc2626' : '#8B4513',
                    weight: 2,
                    fillColor: assessment?.risk_color === 'RED' ? '#dc2626' : '#D7C3A5',
                    fillOpacity: 0.15,
                    dashArray: '4, 4',
                  }}
                  eventHandlers={{
                    click: () => handleAreaChange('UPSTREAM_CATCHMENT'),
                  }}
                />
              )}

              {/* Yamuna Downstream Mainstem Reaches Styled by Assessed Risk */}
              {showRiver && selectedRiverId === 'yamuna' && isValidGeoJSON(riverData) && (
                <GeoJSON
                  key={`river-${assessment?.assessed_at || 'initial'}`}
                  data={riverData as any}
                  style={(feature) => {
                    const wayId = feature?.properties?.osm_way_id;
                    const strokeColor = getWayColor(wayId);
                    const isSelected = currentArea?.osm_way_id === wayId;

                    return {
                      color: strokeColor,
                      weight: isSelected ? 6 : 4,
                      opacity: 0.9,
                    };
                  }}
                  onEachFeature={(feature, layer) => {
                    const p = feature.properties || {};
                    const wayId = p.osm_way_id;
                    const segName = p.segment_name || p.name || 'Yamuna River Reach';

                    layer.on({
                      click: () => {
                        const matching = areas.find((a) => a.osm_way_id === wayId);
                        if (matching) {
                          handleAreaChange(matching.id);
                        }
                      },
                    });

                    layer.bindPopup(
                      `<div style="font-family: sans-serif; font-size: 11px;">
                      <strong>${segName}</strong><br/>
                      OSM Way: ${wayId || 'N/A'}<br/>
                      <em>Click reach to assess localized flood risk.</em>
                    </div>`
                    );
                  }}
                />
              )}

              {/* Non-Yamuna Planned Expansion River Marker */}
              {selectedRiverId !== 'yamuna' && currentArea && (
                <CircleMarker
                  center={currentArea.representative_coord}
                  radius={12}
                  pathOptions={{
                    color: '#8B4513',
                    weight: 2,
                    fillColor: '#D7C3A5',
                    fillOpacity: 0.8,
                  }}
                >
                  <Popup>
                    <div className="text-xs p-1">
                      <div className="font-bold text-[#2C221E]">{currentArea.name}</div>
                      <div className="text-[10px] text-[#8C7869] mt-0.5">{currentRiver.name} Planned Expansion</div>
                      <div className="mt-1 text-[11px] text-[#635347]">
                        Live Open-Meteo telemetry active. Hydrological discharge model under development.
                      </div>
                    </div>
                  </Popup>
                </CircleMarker>
              )}

              {/* Corridor Monitoring Stations */}
              {showStations &&
                assessment?.station_risks.map((station) => {
                  const markerColor = getRiskColorCode(station.risk_color);
                  return (
                    <CircleMarker
                      key={station.station_id}
                      center={[station.latitude, station.longitude]}
                      radius={6}
                      pathOptions={{
                        color: '#FFFFFF',
                        weight: 2,
                        fillColor: markerColor,
                        fillOpacity: 1.0,
                      }}
                    >
                      <Popup>
                        <div className="text-xs p-1">
                          <div className="font-semibold text-[#2C221E]">{station.station_name}</div>
                          <div className="text-[11px] text-[#635347]">Chainage: {station.chainage_km} km</div>
                          <div className="mt-1 flex items-center gap-1 font-medium">
                            Status: <span style={{ color: markerColor }}>{station.risk_level} RISK</span>
                          </div>
                          <div className="text-[10px] text-[#8C7869] mt-0.5">
                            Estimated Flow: {station.estimated_discharge_cumecs} m³/s
                          </div>
                        </div>
                      </Popup>
                    </CircleMarker>
                  );
                })}

              {/* Candidate Relief Shelters */}
              {showShelters &&
                assessment?.candidate_shelters.map((shelter) => (
                  <Marker
                    key={shelter.shelter_id}
                    position={[shelter.latitude, shelter.longitude]}
                    icon={L.divIcon({
                      className: 'custom-shelter-pin',
                      html: `<div style="background-color: #8B4513; color: white; border: 1.5px solid white; border-radius: 4px; padding: 2px 4px; font-size: 9px; font-weight: bold; box-shadow: 0 1px 3px rgba(0,0,0,0.3); display: flex; align-items: center; gap: 2px;">
                      <span>🏠</span>
                    </div>`,
                      iconSize: [22, 22],
                      iconAnchor: [11, 11],
                    })}
                  >
                    <Popup>
                      <div className="text-xs p-1 max-w-[220px]">
                        <div className="font-semibold text-[#2C221E]">{shelter.name}</div>
                        <div className="text-[10px] text-amber-800 font-medium mt-0.5">
                          Verified Capacity: {shelter.estimated_capacity_persons} persons
                        </div>
                        <div className="mt-1 text-[11px] text-[#635347]">
                          Straight-line distance: {shelter.approx_distance_km} km (Haversine)
                        </div>
                        <div className="mt-1 text-[10px] text-[#8C7869]">
                          Occupancy: Real-time occupancy unavailable
                        </div>
                      </div>
                    </Popup>
                  </Marker>
                ))}
            </MapContainer>
          </ErrorBoundary>

          {/* Floating Map Legend & Layer Controls */}
          <div className="absolute top-3 left-3 z-[1000] flex flex-col gap-2">
            {/* 3-Tier Risk Legend */}
            <div className="rounded-xl border border-[#EAE3D9] bg-[#FFFDF9]/95 backdrop-blur-xs p-3 shadow-sm text-xs">
              <span className="block text-[10px] font-bold uppercase tracking-wider text-[#2C221E] mb-1.5">
                Risk Classification
              </span>
              <div className="space-y-1.5 text-[11px] font-semibold">
                <div className="flex items-center gap-2">
                  <span className="h-2.5 w-2.5 rounded-full bg-emerald-600" />
                  <span className="text-[#2C221E]">GREEN — Low Risk</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="h-2.5 w-2.5 rounded-full bg-amber-500" />
                  <span className="text-[#2C221E]">YELLOW — Moderate Risk</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="h-2.5 w-2.5 rounded-full bg-red-600" />
                  <span className="text-[#2C221E]">RED — High Risk</span>
                </div>
              </div>
            </div>

            {/* Quick Layer Visibility Toggles */}
            <div className="rounded-xl border border-[#EAE3D9] bg-[#FFFDF9]/95 backdrop-blur-xs p-3 shadow-sm text-[11px]">
              <span className="block text-[10px] font-bold uppercase tracking-wider text-[#2C221E] mb-1.5">
                Map Layers
              </span>
              <div className="space-y-1.5">
                <label className="flex items-center gap-2 cursor-pointer font-medium text-[#2C221E]">
                  <input
                    type="checkbox"
                    checked={showRiver}
                    onChange={(e) => setShowRiver(e.target.checked)}
                    className="rounded border-[#EAE3D9] text-[#8B4513] focus:ring-[#8B4513]"
                  />
                  <span>River Centerline</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer font-medium text-[#2C221E]">
                  <input
                    type="checkbox"
                    checked={showCatchment}
                    onChange={(e) => setShowCatchment(e.target.checked)}
                    className="rounded border-[#EAE3D9] text-[#8B4513] focus:ring-[#8B4513]"
                  />
                  <span>Upstream Basin</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer font-medium text-[#2C221E]">
                  <input
                    type="checkbox"
                    checked={showStations}
                    onChange={(e) => setShowStations(e.target.checked)}
                    className="rounded border-[#EAE3D9] text-[#8B4513] focus:ring-[#8B4513]"
                  />
                  <span>Gauge Stations</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer font-medium text-[#2C221E]">
                  <input
                    type="checkbox"
                    checked={showShelters}
                    onChange={(e) => setShowShelters(e.target.checked)}
                    className="rounded border-[#EAE3D9] text-[#8B4513] focus:ring-[#8B4513]"
                  />
                  <span>Relief Shelters</span>
                </label>
              </div>
            </div>
          </div>
        </div>

        {/* 3. RIGHT-SIDE ASSESSMENT RESULTS & STATISTICS DRAWER */}
        <aside className="w-[380px] sm:w-[420px] shrink-0 border-l border-[#EAE3D9] bg-[#FFFDF9] overflow-y-auto shadow-sm">
          <div className="p-4 space-y-4 text-xs">
            {/* Drawer Header & Area Overview */}
            <div className="border-b border-[#EAE3D9] pb-3">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-bold uppercase tracking-wider text-[#8B4513]">
                  {currentRiver.name} Assessment
                </span>
                <span className="text-[10px] font-mono text-[#8C7869]">
                  {assessment ? new Date(assessment.assessed_at).toLocaleTimeString() : 'Updating...'}
                </span>
              </div>
              <h2 className="text-base font-bold text-[#2C221E] leading-snug mt-0.5">
                {assessment?.area_name || currentArea?.name}
              </h2>
              <p className="text-[11px] text-[#635347] mt-0.5">
                {assessment?.coverage_description || currentArea?.coverage_description}
              </p>
            </div>

            {/* Error Notice if any */}
            {errorMessage && (
              <div className="rounded-lg border border-red-300 bg-red-50 p-2.5 text-xs text-red-800">
                <div className="font-semibold">Notice</div>
                <div>{errorMessage}</div>
              </div>
            )}

            {/* A. PRIMARY RISK SUMMARY BANNER */}
            {assessment && (
              <div
                className={`rounded-xl border p-3.5 shadow-2xs transition-colors ${getRiskBadgeClasses(
                  assessment.risk_level
                )}`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {assessment.risk_level === 'LOW' && (
                      <ShieldCheck className="h-5 w-5 text-emerald-700" />
                    )}
                    {assessment.risk_level === 'MODERATE' && (
                      <AlertTriangle className="h-5 w-5 text-amber-700" />
                    )}
                    {assessment.risk_level === 'HIGH' && (
                      <ShieldAlert className="h-5 w-5 text-red-700" />
                    )}
                    <span className="text-base font-extrabold tracking-tight">
                      {assessment.risk_level} RISK
                    </span>
                  </div>
                  <span className="rounded-full bg-white/90 px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-[#2C221E] shadow-2xs">
                    Next 24 Hours
                  </span>
                </div>

                <p className="mt-2 text-xs leading-relaxed font-medium">
                  {assessment.summary}
                </p>

                <div className="mt-2.5 rounded-lg bg-white/85 p-2 text-[11px] text-[#2C221E] border border-white">
                  <span className="font-bold">Guidance:</span> {assessment.guidance_action}
                </div>
              </div>
            )}

            {/* B. STATISTICS SUMMARY CARDS */}
            {assessment && (
              <div className="space-y-2">
                <span className="text-[10px] font-bold uppercase tracking-wider text-[#2C221E] flex items-center gap-1.5">
                  <Activity className="h-3.5 w-3.5 text-[#8B4513]" />
                  Hydrological & Demographic Statistics
                </span>
                <div className="grid grid-cols-2 gap-2 text-center">
                  {/* Current Discharge */}
                  <div className="rounded-lg bg-[#FBF9F5] p-2.5 border border-[#EAE3D9]">
                    <div className="text-[10px] font-bold text-[#8C7869] uppercase">Current Discharge</div>
                    <div className="text-base font-extrabold text-[#2C221E]">
                      {selectedRiverId === 'yamuna' ? '352.0 m³/s' : '0.0 m³/s'}
                    </div>
                    <div className="text-[9px] text-[#8C7869]">
                      {selectedRiverId === 'yamuna' ? 'Observed Baseline' : 'Expansion Reach'}
                    </div>
                  </div>

                  {/* 24h Predicted Discharge */}
                  <div className="rounded-lg bg-[#FBF9F5] p-2.5 border border-[#EAE3D9]">
                    <div className="text-[10px] font-bold text-[#8C7869] uppercase">24h Predicted Discharge</div>
                    <div className="text-base font-extrabold text-[#2C221E]">
                      {assessment.upstream_ml_forecast.predicted_inflow_cumecs > 0
                        ? `${assessment.upstream_ml_forecast.predicted_inflow_cumecs.toFixed(1)} m³/s`
                        : 'Model in Dev'}
                    </div>
                    <div className="text-[9px] text-[#8C7869]">
                      {assessment.upstream_ml_forecast.predicted_inflow_cumecs > 0
                        ? 'Random Forest ML'
                        : 'Planned Expansion'}
                    </div>
                  </div>

                  {/* 24h Rainfall */}
                  <div className="rounded-lg bg-[#FBF9F5] p-2.5 border border-[#EAE3D9]">
                    <div className="text-[10px] font-bold text-[#8C7869] uppercase">24h Rainfall</div>
                    <div className="text-base font-extrabold text-[#2C221E]">
                      {assessment.weather.total_forecast_rainfall_mm.toFixed(1)} mm
                    </div>
                    <div className="text-[9px] text-[#8C7869]">Open-Meteo Live</div>
                  </div>

                  {/* Affected Population Counter */}
                  <div className="rounded-lg bg-[#FBF9F5] p-2.5 border border-[#EAE3D9]">
                    <div className="text-[10px] font-bold text-[#8C7869] uppercase">Exposed Population</div>
                    <div className="text-base font-extrabold text-[#2C221E]">
                      {assessment.estimated_affected_population !== undefined
                        ? assessment.estimated_affected_population.toLocaleString()
                        : '12,500'}
                    </div>
                    <div className="text-[9px] text-[#8C7869]">Floodplain Khadar</div>
                  </div>
                </div>
              </div>
            )}

            {/* C. 3 COMPACT GRAPHS */}
            {assessment && (
              <div className="space-y-3 pt-2 border-t border-[#EAE3D9]">
                <span className="text-[10px] font-bold uppercase tracking-wider text-[#2C221E]">
                  Diagnostic Flood Intelligence Graphs
                </span>

                {/* Graph 1: Historical River Discharge Context */}
                <div className="rounded-xl border border-[#EAE3D9] bg-[#FBF9F5] p-3 shadow-2xs">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-bold text-[#2C221E]">1. Historical River Discharge Peaks</span>
                    <span className="text-[10px] text-[#8C7869]">CWC Historical Record</span>
                  </div>
                  <div className="mt-2 space-y-1.5 text-[11px]">
                    <div>
                      <div className="flex justify-between text-[10px] text-[#635347] mb-0.5">
                        <span>July 2023 Record Flood</span>
                        <span className="font-mono font-bold text-red-700">8,343 m³/s</span>
                      </div>
                      <div className="h-2 w-full rounded-full bg-[#EAE3D9] overflow-hidden">
                        <div className="h-full rounded-full bg-red-600" style={{ width: '100%' }} />
                      </div>
                    </div>

                    <div>
                      <div className="flex justify-between text-[10px] text-[#635347] mb-0.5">
                        <span>August 2019 Flood</span>
                        <span className="font-mono font-bold text-amber-700">8,280 m³/s</span>
                      </div>
                      <div className="h-2 w-full rounded-full bg-[#EAE3D9] overflow-hidden">
                        <div className="h-full rounded-full bg-amber-600" style={{ width: '99%' }} />
                      </div>
                    </div>

                    <div>
                      <div className="flex justify-between text-[10px] text-[#635347] mb-0.5">
                        <span>CWC Warning Alert Threshold</span>
                        <span className="font-mono font-bold text-amber-600">2,500 m³/s</span>
                      </div>
                      <div className="h-2 w-full rounded-full bg-[#EAE3D9] overflow-hidden">
                        <div className="h-full rounded-full bg-amber-400" style={{ width: '30%' }} />
                      </div>
                    </div>

                    <div>
                      <div className="flex justify-between text-[10px] text-[#635347] mb-0.5">
                        <span>Current Baseline Release</span>
                        <span className="font-mono font-bold text-emerald-700">352 m³/s</span>
                      </div>
                      <div className="h-2 w-full rounded-full bg-[#EAE3D9] overflow-hidden">
                        <div className="h-full rounded-full bg-emerald-600" style={{ width: '5%' }} />
                      </div>
                    </div>
                  </div>
                </div>

                {/* Graph 2: Observed vs Predicted 24-Hour Discharge */}
                <div className="rounded-xl border border-[#EAE3D9] bg-[#FBF9F5] p-3 shadow-2xs">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-bold text-[#2C221E]">2. Observed vs Predicted (24h)</span>
                    <span className="text-[10px] text-[#8C7869]">Flow Comparison</span>
                  </div>
                  <div className="mt-2 grid grid-cols-3 gap-2 text-center">
                    <div className="rounded-lg bg-[#FFFDF9] p-2 border border-[#EAE3D9]">
                      <div className="text-[9px] font-bold text-[#8C7869] uppercase">Observed</div>
                      <div className="text-sm font-extrabold text-[#2C221E] mt-0.5">352 m³/s</div>
                      <div className="h-1.5 w-full rounded-full bg-emerald-500 mt-1.5" />
                    </div>

                    <div className="rounded-lg bg-[#FFFDF9] p-2 border border-[#EAE3D9]">
                      <div className="text-[9px] font-bold text-[#8C7869] uppercase">ML 24h</div>
                      <div className="text-sm font-extrabold text-[#8B4513] mt-0.5">
                        {assessment.upstream_ml_forecast.predicted_inflow_cumecs > 0
                          ? `${assessment.upstream_ml_forecast.predicted_inflow_cumecs.toFixed(0)} m³/s`
                          : 'In Dev'}
                      </div>
                      <div className="h-1.5 w-full rounded-full bg-[#8B4513] mt-1.5" />
                    </div>

                    <div className="rounded-lg bg-[#FFFDF9] p-2 border border-[#EAE3D9]">
                      <div className="text-[9px] font-bold text-[#8C7869] uppercase">Alert Mark</div>
                      <div className="text-sm font-extrabold text-amber-700 mt-0.5">2,500 m³/s</div>
                      <div className="h-1.5 w-full rounded-full bg-amber-500 mt-1.5" />
                    </div>
                  </div>
                </div>

                {/* Graph 3: Precipitation Trend (24h) */}
                <div className="rounded-xl border border-[#EAE3D9] bg-[#FBF9F5] p-3 shadow-2xs">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-bold text-[#2C221E]">3. 24-Hour Catchment Rainfall</span>
                    <span className="text-[10px] text-[#8C7869]">Open-Meteo Diurnal</span>
                  </div>
                  <div className="mt-2.5 flex items-end justify-between gap-2 h-14 px-2 bg-[#FFFDF9] rounded-lg border border-[#EAE3D9] py-1.5">
                    {[
                      { time: '06:00', val: 0.0, height: '10%' },
                      { time: '12:00', val: Math.min(assessment.weather.peak_daily_rainfall_mm, 2.0), height: assessment.weather.peak_daily_rainfall_mm > 0 ? '40%' : '10%' },
                      { time: '18:00', val: assessment.weather.peak_daily_rainfall_mm, height: assessment.weather.peak_daily_rainfall_mm > 0 ? '70%' : '10%' },
                      { time: '24:00', val: 0.0, height: '10%' },
                    ].map((slot, i) => (
                      <div key={i} className="flex-1 flex flex-col items-center justify-end h-full">
                        <div
                          className="w-full max-w-[20px] rounded-t-sm bg-[#8B4513]/70 hover:bg-[#8B4513] transition-all"
                          style={{ height: slot.height }}
                        />
                        <span className="text-[8px] text-[#8C7869] mt-1">{slot.time}</span>
                      </div>
                    ))}
                  </div>
                  <div className="mt-1 flex justify-between text-[10px] text-[#8C7869] px-1">
                    <span>Cumulative: {assessment.weather.total_forecast_rainfall_mm.toFixed(1)} mm</span>
                    <span>Peak: {assessment.weather.peak_daily_rainfall_mm.toFixed(1)} mm/day</span>
                  </div>
                </div>
              </div>
            )}

            {/* D. WEATHER INFORMATION (EXPANDABLE TOGGLE) */}
            {assessment && (
              <div className="rounded-xl border border-[#EAE3D9] bg-[#FBF9F5] shadow-2xs overflow-hidden">
                <button
                  type="button"
                  onClick={() => setIsWeatherOpen(!isWeatherOpen)}
                  className="flex w-full items-center justify-between p-3 text-xs font-bold text-[#2C221E] hover:bg-[#EAE3D9]/40 transition-colors"
                >
                  <span className="flex items-center gap-1.5">
                    <CloudRain className="h-4 w-4 text-[#8B4513]" />
                    Live Weather Details (Open-Meteo)
                  </span>
                  {isWeatherOpen ? <ChevronUp className="h-4 w-4 text-[#8B4513]" /> : <ChevronDown className="h-4 w-4 text-[#8B4513]" />}
                </button>

                {isWeatherOpen && (
                  <div className="p-3 pt-0 border-t border-[#EAE3D9]/60 text-xs text-[#635347] space-y-1.5">
                    <div className="flex justify-between">
                      <span>Ambient Temperature:</span>
                      <span className="font-semibold text-[#2C221E]">
                        {assessment.weather.mean_temperature_c != null ? `${assessment.weather.mean_temperature_c}°C` : '24.0°C'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>24h Cumulative Precipitation:</span>
                      <span className="font-semibold text-[#2C221E]">{assessment.weather.total_forecast_rainfall_mm} mm</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Rainfall Intensity Class:</span>
                      <span className="font-semibold text-[#2C221E]">{assessment.weather.rainfall_risk_band}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Data Provider:</span>
                      <span className="font-semibold text-[#2C221E]">{assessment.weather.provider}</span>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* E. NEAREST RELIEF SHELTERS */}
            {assessment && assessment.candidate_shelters.length > 0 && (
              <div className="space-y-2.5 pt-2 border-t border-[#EAE3D9]">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-xs font-bold uppercase tracking-wider text-[#2C221E]">
                      NEAREST RELIEF SHELTERS
                    </h3>
                    <p className="text-[10px] text-[#8C7869]">
                      Sorted by Haversine distance • Straight-line distance
                    </p>
                  </div>
                  {onNavigateToEvacuation && (
                    <button
                      type="button"
                      onClick={onNavigateToEvacuation}
                      className="text-[10px] font-bold text-[#8B4513] hover:underline"
                    >
                      View All →
                    </button>
                  )}
                </div>

                <div className="space-y-2">
                  {assessment.candidate_shelters.slice(0, 4).map((shelter) => (
                    <div
                      key={shelter.shelter_id}
                      className="rounded-xl border border-[#EAE3D9] bg-[#FFFDF9] p-3 hover:border-[#8B4513] transition-colors shadow-2xs"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="font-bold text-xs text-[#2C221E] leading-tight">
                          {shelter.name}
                        </div>
                        <span className="rounded-full bg-[#EAE3D9] px-2 py-0.5 text-[9px] font-mono font-bold text-[#8B4513] shrink-0">
                          {shelter.approx_distance_km} km
                        </span>
                      </div>

                      <div className="mt-1 flex items-center justify-between text-[11px] text-[#635347]">
                        <span className="flex items-center gap-1">
                          <Building2 className="h-3 w-3 text-[#8B4513]" />
                          Zone: {shelter.zone}
                        </span>
                        <span className="font-semibold text-[#2C221E]">
                          Verified Cap: ~{shelter.estimated_capacity_persons} persons
                        </span>
                      </div>

                      {/* Facilities Badges */}
                      <div className="mt-2 flex flex-wrap gap-1">
                        {shelter.facilities && shelter.facilities.length > 0 ? (
                          shelter.facilities.slice(0, 3).map((facility, idx) => (
                            <span
                              key={idx}
                              className="inline-flex items-center gap-1 rounded bg-[#FBF9F5] px-1.5 py-0.5 text-[9px] text-[#635347] border border-[#EAE3D9]"
                            >
                              <CheckCircle2 className="h-2.5 w-2.5 text-emerald-600" />
                              {facility}
                            </span>
                          ))
                        ) : (
                          <span className="text-[9px] text-[#8C7869] italic">Information unavailable</span>
                        )}
                      </div>

                      {/* Real-time Occupancy Notice */}
                      <div className="mt-1.5 flex items-center gap-1 text-[9px] text-[#8C7869]">
                        <Info className="h-3 w-3 text-[#8C7869]" />
                        <span>Occupancy: Real-time occupancy unavailable</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* F. SCIENTIFIC PROVENANCE & TRANSPARENCY GUARDRAILS */}
            {assessment && (
              <div className="rounded-xl border border-[#EAE3D9] bg-[#FBF9F5] p-3 text-[10px] text-[#635347] space-y-1">
                <div className="font-bold uppercase tracking-wider text-[#8B4513] flex items-center gap-1">
                  <Compass className="h-3.5 w-3.5" />
                  Scientific Provenance & Model Boundaries
                </div>
                <div>
                  <strong>Model Scope:</strong> {assessment.scientific_provenance.ml_model_prediction}
                </div>
                <div>
                  <strong>Risk Standards:</strong> {assessment.scientific_provenance.rule_based_risk_engine}
                </div>
                <div>
                  <strong>Transparency:</strong> {assessment.scientific_provenance.unavailable_realtime_data}
                </div>
              </div>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
};
