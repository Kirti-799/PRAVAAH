/**
 * frontend/src/components/assessment/FloodRiskMapWorkspace.tsx
 *
 * SECTION 3: Flood Risk Map
 * Primary interactive workspace for PRAVAAH — Intelligent Flood Prediction & Disaster Response System.
 * Styled in the authentic Cream & Brown theme (#FBF9F5, #2C221E, #8B4513).
 *
 * Capabilities:
 * 1. Geographical Area selection (reaches and hydrometric stations).
 * 2. 24-Hour ML-based assessment coupled with Open-Meteo atmospheric forecasts.
 * 3. 3-tier geographical risk classification:
 *    - GREEN: Lower Risk
 *    - YELLOW: Moderate Risk
 *    - RED: High Risk
 * 4. Clear separation between upstream Hathnikund discharge prediction and reach geographical risk.
 * 5. Transparent audited model metrics (Test R²=0.380, RMSE=469.5 m³/s, MAE=95.8 m³/s).
 * 6. Candidate planning shelters with verified static capacities & real-time occupancy disclaimer.
 * 7. Strictly 24-hour operational horizon (no multi-day selectors or confidence decay curves).
 */

import React, { useState, useEffect } from 'react';
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
  MapPin,
  RefreshCw,
  ChevronRight,
  CloudRain,
  Activity,
  Layers,
  Clock,
} from 'lucide-react';
import { riskAssessmentApi } from '../../services/riskAssessment';
import {
  fetchRiverFeatures,
  fetchCatchmentGeometry,
} from '../../services/spatial';
import type {
  SupportedArea,
  AssessmentResponse,
  RiskLevel,
  RiskColor,
} from '../../types/riskAssessment';
import type { RiverGeoJSONResponse } from '../../types/spatial';

interface FloodRiskMapWorkspaceProps {
  onNavigateToDisaster?: () => void;
}

// Map Centering Helper
const MapController: React.FC<{ center: [number, number]; zoom: number }> = ({ center, zoom }) => {
  const map = useMap();
  useEffect(() => {
    map.setView(center, zoom, { animate: true });
  }, [center, zoom, map]);
  return null;
};

// 3-Tier Risk Color Palette: GREEN / YELLOW / RED
const getRiskColorCode = (color: RiskColor): string => {
  switch (color) {
    case 'GREEN':
      return '#16a34a'; // Emerald 600 - Lower Risk
    case 'YELLOW':
      return '#ca8a04'; // Dark Amber/Yellow - Moderate Risk
    case 'RED':
      return '#dc2626'; // Red 600 - High Risk
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
  onNavigateToDisaster,
}) => {
  // Areas and Assessment State
  const [areas, setAreas] = useState<SupportedArea[]>([]);
  const [selectedAreaId, setSelectedAreaId] = useState<string>('DELHI_CENTRAL');
  const [assessment, setAssessment] = useState<AssessmentResponse | null>(null);
  const [isAssessing, setIsAssessing] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Spatial Data Layers
  const [riverData, setRiverData] = useState<RiverGeoJSONResponse | null>(null);
  const [catchmentData, setCatchmentData] = useState<any>(null);

  // Layer Toggles
  const [showRiver, setShowRiver] = useState<boolean>(true);
  const [showCatchment, setShowCatchment] = useState<boolean>(true);
  const [showStations, setShowStations] = useState<boolean>(true);
  const [showShelters, setShowShelters] = useState<boolean>(true);

  // Load supported areas & initial spatial layers
  useEffect(() => {
    let isMounted = true;

    async function init() {
      try {
        const areasRes = await riskAssessmentApi.getSupportedAreas();
        if (isMounted) {
          setAreas(areasRes.areas);
          if (areasRes.areas.length > 0) {
            setSelectedAreaId(areasRes.default_area_id || areasRes.areas[0].id);
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
          if (riverRes.status === 'fulfilled' && isValidGeoJSON(riverRes.value)) setRiverData(riverRes.value);
          if (catchRes.status === 'fulfilled' && isValidGeoJSON(catchRes.value)) setCatchmentData(catchRes.value);
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

  const run24HourAssessment = async (areaId: string) => {
    setIsAssessing(true);
    setErrorMessage(null);
    try {
      const res = await riskAssessmentApi.assessRisk({
        area_id: areaId,
        forecast_days: 1,
        horizon_hours: 24,
      });
      setAssessment(res);
    } catch (err: any) {
      setErrorMessage(err?.message || 'Failed to complete 24-hour risk assessment.');
    } finally {
      setIsAssessing(false);
    }
  };

  // Run 24-Hour Assessment when area selection changes
  useEffect(() => {
    if (selectedAreaId) {
      run24HourAssessment(selectedAreaId);
    }
  }, [selectedAreaId]);

  const handleAreaChange = (newAreaId: string) => {
    setSelectedAreaId(newAreaId);
  };

  // Find currently selected area object
  const currentArea = areas.find((a) => a.id === selectedAreaId);
  const centerCoord: [number, number] = currentArea?.representative_coord || [28.66, 77.25];
  const zoomLevel = currentArea?.area_type === 'CORRIDOR_ALL' ? 8 : currentArea?.area_type === 'BASIN' ? 8 : 10;

  // Determine reach color styling based on assessment reach_risks (Green / Yellow / Red)
  const getWayColor = (wayId?: number): string => {
    if (!assessment || !wayId) return '#16a34a';
    const match = assessment.reach_risks.find((r) => r.osm_way_id === wayId);
    return match ? getRiskColorCode(match.risk_color) : '#16a34a';
  };

  return (
    <div className="flex h-full w-full flex-col overflow-hidden bg-[#FBF9F5] text-[#2C221E]">
      {/* 1. TOP CONTROL BAR: AREA SELECTOR & 24-HOUR HORIZON BADGE */}
      <div className="shrink-0 border-b border-[#EAE3D9] bg-[#FFFDF9] px-4 py-2.5 shadow-2xs z-10">
        <div className="flex flex-wrap items-center justify-between gap-3">
          {/* Area Selector Dropdown */}
          <div className="flex items-center gap-2">
            <span className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-[#2C221E]">
              <MapPin className="h-4 w-4 text-[#8B4513]" />
              Select Geographical Area:
            </span>
            <select
              value={selectedAreaId}
              onChange={(e) => handleAreaChange(e.target.value)}
              className="rounded-lg border border-[#D9CEBF] bg-[#FFFFFF] px-3 py-1.5 text-xs font-semibold text-[#2C221E] focus:border-[#8B4513] focus:outline-hidden shadow-2xs"
              aria-label="Select geographical area"
            >
              {areas.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name} ({a.area_type})
                </option>
              ))}
            </select>
          </div>

          {/* Strict 24-Hour Horizon Badge */}
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1.5 rounded-full border border-[#D9CEBF] bg-[#F5EFEB] px-3 py-1 text-xs font-bold text-[#8B4513] shadow-2xs">
              <Clock className="h-3.5 w-3.5 text-[#8B4513]" />
              <span>PREDICTION HORIZON: NEXT 24 HOURS</span>
            </div>
            <span className="hidden md:inline-flex items-center rounded-full bg-emerald-50 border border-emerald-300 px-2.5 py-0.5 text-[11px] font-semibold text-emerald-900">
              Operational Window
            </span>
          </div>

          {/* Action Button: Re-Assess */}
          <button
            type="button"
            onClick={() => run24HourAssessment(selectedAreaId)}
            disabled={isAssessing}
            className="flex items-center gap-1.5 rounded-full bg-[#8B4513] px-4 py-2 text-xs font-bold text-white shadow-xs hover:bg-[#6D340E] active:scale-98 disabled:opacity-60 transition-all cursor-pointer"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isAssessing ? 'animate-spin' : ''}`} />
            <span>{isAssessing ? 'Evaluating...' : 'Run 24h Assessment'}</span>
          </button>
        </div>
      </div>

      {/* 2. MAIN MAP VIEWPORT & ASSESSMENT DRAWER */}
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

              {/* Upstream Watershed Basin Polygon */}
              {showCatchment && isValidGeoJSON(catchmentData) && (
                <GeoJSON
                  key={`catchment-${assessment?.risk_color || 'default'}`}
                  data={catchmentData}
                  style={{
                    color: assessment?.risk_color === 'RED' ? '#dc2626' : '#8B4513',
                    weight: 2,
                    fillColor: assessment?.risk_color === 'RED' ? '#dc2626' : '#C49A45',
                    fillOpacity: 0.12,
                    dashArray: '4, 4',
                  }}
                  eventHandlers={{
                    click: () => handleAreaChange('UPSTREAM_CATCHMENT'),
                  }}
                />
              )}

              {/* Yamuna Downstream Mainstem Reaches Styled by Assessed Risk (Green / Yellow / Red) */}
              {showRiver && isValidGeoJSON(riverData) && (
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
                      `<div style="font-family: sans-serif; font-size: 11px; color: #2C221E;">
                        <strong>${segName}</strong><br/>
                        OSM Way: ${wayId || 'N/A'}<br/>
                        <em>Click reach to assess localized 24h flood risk.</em>
                      </div>`
                    );
                  }}
                />
              )}

              {/* Corridor Monitoring Stations with Risk Colored Markers */}
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
                        <div className="text-xs p-1 text-[#2C221E]">
                          <div className="font-bold text-[#2C221E]">{station.station_name}</div>
                          <div className="text-[11px] text-[#635347]">Chainage: {station.chainage_km} km</div>
                          <div className="mt-1 flex items-center gap-1 font-semibold">
                            Status: <span style={{ color: markerColor }}>{station.risk_level} RISK</span>
                          </div>
                          <div className="text-[10px] text-[#8C7869] mt-0.5">
                            Estimated Flow: {station.estimated_discharge_cumecs} m³/s
                          </div>
                          {station.warning_level_m && (
                            <div className="text-[10px] text-[#8B4513] mt-0.5">
                              Warning Level: {station.warning_level_m} m MSL
                            </div>
                          )}
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
                      <div className="text-xs p-1 max-w-[220px] text-[#2C221E]">
                        <div className="font-bold text-[#2C221E]">{shelter.name}</div>
                        <div className="text-[10px] text-[#8B4513] font-semibold mt-0.5">
                          Candidate Planning Shelter
                        </div>
                        <div className="mt-1 text-[11px] text-[#635347]">
                          Static Capacity: ~{shelter.estimated_capacity_persons} persons
                        </div>
                        <div className="text-[10px] text-[#8C7869]">
                          Distance: {shelter.approx_distance_km} km • Zone: {shelter.zone}
                        </div>
                        <div className="mt-1 text-[9px] text-[#8C7869] italic border-t border-[#EAE3D9] pt-1">
                          Static capacity benchmark. Real-time occupancy tracking is unavailable.
                        </div>
                      </div>
                    </Popup>
                  </Marker>
                ))}
            </MapContainer>
          </ErrorBoundary>

          {/* Floating Map Legend & Layer Controls */}
          <div className="absolute top-3 left-3 z-[1000] flex flex-col gap-2">
            {/* 3-Tier Risk Legend: GREEN / YELLOW / RED */}
            <div className="rounded-xl border border-[#EAE3D9] bg-[#FFFFFF]/95 backdrop-blur-xs p-3 shadow-sm text-xs">
              <span className="block text-[10px] font-bold uppercase tracking-wider text-[#2C221E] mb-1.5">
                Risk Classification (3 Tiers)
              </span>
              <div className="space-y-1.5 text-[11px] font-semibold">
                <div className="flex items-center gap-2">
                  <span className="h-2.5 w-2.5 rounded-full bg-emerald-600" />
                  <span className="text-[#2C221E]">GREEN — Lower Risk</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="h-2.5 w-2.5 rounded-full bg-yellow-600" />
                  <span className="text-[#2C221E]">YELLOW — Moderate Risk</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="h-2.5 w-2.5 rounded-full bg-red-600" />
                  <span className="text-[#2C221E]">RED — High Risk</span>
                </div>
              </div>
            </div>

            {/* Quick Layer Visibility Toggles */}
            <div className="rounded-xl border border-[#EAE3D9] bg-[#FFFFFF]/95 backdrop-blur-xs p-3 shadow-sm text-[11px]">
              <span className="flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider text-[#2C221E] mb-1.5">
                <Layers className="h-3 w-3 text-[#8B4513]" />
                Map Layers
              </span>
              <div className="space-y-1.5">
                <label className="flex items-center gap-2 cursor-pointer font-medium text-[#2C221E]">
                  <input
                    type="checkbox"
                    checked={showRiver}
                    onChange={(e) => setShowRiver(e.target.checked)}
                    className="rounded border-[#D9CEBF] text-[#8B4513] focus:ring-[#8B4513]"
                  />
                  <span>River Centerline</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer font-medium text-[#2C221E]">
                  <input
                    type="checkbox"
                    checked={showCatchment}
                    onChange={(e) => setShowCatchment(e.target.checked)}
                    className="rounded border-[#D9CEBF] text-[#8B4513] focus:ring-[#8B4513]"
                  />
                  <span>Upstream Basin</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer font-medium text-[#2C221E]">
                  <input
                    type="checkbox"
                    checked={showStations}
                    onChange={(e) => setShowStations(e.target.checked)}
                    className="rounded border-[#D9CEBF] text-[#8B4513] focus:ring-[#8B4513]"
                  />
                  <span>Gauge Stations</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer font-medium text-[#2C221E]">
                  <input
                    type="checkbox"
                    checked={showShelters}
                    onChange={(e) => setShowShelters(e.target.checked)}
                    className="rounded border-[#D9CEBF] text-[#8B4513] focus:ring-[#8B4513]"
                  />
                  <span>Candidate Shelters</span>
                </label>
              </div>
            </div>
          </div>
        </div>

        {/* 3. RIGHT-SIDE 24-HOUR ASSESSMENT RESULTS DRAWER */}
        <aside className="w-[360px] sm:w-[420px] shrink-0 border-l border-[#EAE3D9] bg-[#FFFFFF] overflow-y-auto shadow-sm">
          <div className="p-4 space-y-4 text-xs">
            {/* Drawer Header & Area Overview */}
            <div className="border-b border-[#EAE3D9] pb-3">
              <span className="text-[10px] font-bold uppercase tracking-wider text-[#8B4513]">
                24-Hour Assessment Result
              </span>
              <h2 className="text-base font-bold text-[#2C221E] leading-snug">
                {assessment?.area_name || currentArea?.name}
              </h2>
              <p className="text-[11px] text-[#635347] mt-0.5">
                {assessment?.coverage_description || currentArea?.coverage_description}
              </p>
            </div>

            {/* Error Notice if any */}
            {errorMessage && (
              <div className="rounded-lg border border-red-300 bg-red-50 p-2.5 text-xs text-red-800">
                <div className="font-semibold">Assessment Notice</div>
                <div>{errorMessage}</div>
              </div>
            )}

            {/* Primary Risk Status Banner: GREEN / YELLOW / RED */}
            {assessment && (
              <div
                className={`rounded-xl border p-4 shadow-2xs transition-colors ${getRiskBadgeClasses(
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
                      {assessment.risk_level === 'LOW'
                        ? 'GREEN — LOWER RISK'
                        : assessment.risk_level === 'MODERATE'
                        ? 'YELLOW — MODERATE RISK'
                        : 'RED — HIGH RISK'}
                    </span>
                  </div>
                  <span className="rounded-full bg-white/90 px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-[#2C221E] shadow-2xs">
                    Next 24 Hours
                  </span>
                </div>

                <p className="mt-2.5 text-xs leading-relaxed font-medium">
                  {assessment.summary}
                </p>

                <div className="mt-3 rounded-lg bg-white/90 p-2.5 text-[11px] text-[#2C221E] border border-white">
                  <span className="font-bold">Operational Guidance:</span> {assessment.guidance_action}
                </div>
              </div>
            )}

            {/* Contributing Factors & Live Forecast Breakdown */}
            {assessment && (
              <div className="space-y-3">
                <span className="text-[10px] font-bold uppercase tracking-wider text-[#2C221E]">
                  Contributing Assessment Factors
                </span>

                {/* Factor 1: Upstream Inflow Forecast (ML Model - Hathnikund Barrage) */}
                <div className="rounded-xl border border-[#EAE3D9] bg-[#FBF9F5] p-3">
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-1.5 font-bold text-[#2C221E]">
                      <Activity className="h-4 w-4 text-[#8B4513]" />
                      Upstream Hathnikund Discharge
                    </span>
                    <span className="rounded-full bg-[#EAE3D9] px-2 py-0.5 text-[9px] font-bold text-[#635347]">
                      ML Inflow Forecast
                    </span>
                  </div>

                  <div className="mt-2 flex items-baseline justify-between">
                    <div>
                      <span className="text-lg font-extrabold text-[#2C221E]">
                        {assessment.upstream_ml_forecast.predicted_inflow_cumecs.toFixed(1)} m³/s
                      </span>
                      <div className="text-[10px] text-[#635347]">
                        ~{(assessment.upstream_ml_forecast.predicted_inflow_cumecs * 35.315).toLocaleString(undefined, { maximumFractionDigits: 0 })} cfs
                      </div>
                    </div>
                    <span className="rounded-md bg-white border border-[#EAE3D9] px-2 py-1 text-[11px] font-semibold text-[#8B4513]">
                      Flow Band: {assessment.upstream_ml_forecast.flood_band}
                    </span>
                  </div>

                  {/* Audited Model Metrics Box */}
                  <div className="mt-2 rounded-lg bg-[#FFFFFF] border border-[#EAE3D9] p-2 text-[10px] text-[#635347] space-y-1">
                    <div className="font-semibold text-[#2C221E] flex items-center justify-between">
                      <span>Model: Random Forest Regressor v1</span>
                      <span className="text-[9px] text-[#8B4513]">Audited Test Set</span>
                    </div>
                    <div className="grid grid-cols-3 gap-1 text-center pt-1 border-t border-[#EAE3D9]">
                      <div>
                        <span className="text-[#8C7869] block">Test R²</span>
                        <strong className="text-[#2C221E] font-mono">0.380</strong>
                      </div>
                      <div>
                        <span className="text-[#8C7869] block">Test RMSE</span>
                        <strong className="text-[#2C221E] font-mono">469.5 m³/s</strong>
                      </div>
                      <div>
                        <span className="text-[#8C7869] block">Test MAE</span>
                        <strong className="text-[#2C221E] font-mono">95.8 m³/s</strong>
                      </div>
                    </div>
                    <div className="text-[9px] text-[#8C7869] pt-1 leading-tight">
                      * Inflow is predicted strictly at Hathnikund Barrage (upstream). Tree models cannot extrapolate beyond the training maximum (3,524 m³/s). Downstream reach risk is computed via hydrodynamic attenuation.
                    </div>
                  </div>
                </div>

                {/* Factor 2: 24-Hour Weather Forecast (Open-Meteo) */}
                <div className="rounded-xl border border-[#EAE3D9] bg-[#FBF9F5] p-3">
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-1.5 font-bold text-[#2C221E]">
                      <CloudRain className="h-4 w-4 text-[#8B4513]" />
                      24-Hour Catchment Rainfall
                    </span>
                    <span className="rounded-full bg-[#EAE3D9] px-2 py-0.5 text-[9px] font-bold text-[#635347]">
                      Open-Meteo API
                    </span>
                  </div>
                  <div className="mt-2 flex items-baseline justify-between">
                    <span className="text-lg font-extrabold text-[#2C221E]">
                      {assessment.weather.total_forecast_rainfall_mm} mm
                    </span>
                    <span className="text-[11px] font-semibold text-[#635347]">
                      Peak: {assessment.weather.peak_daily_rainfall_mm} mm/day
                    </span>
                  </div>
                  <div className="mt-1 flex items-center justify-between text-[10px] text-[#635347]">
                    <span>Rainfall Intensity: <strong>{assessment.weather.rainfall_risk_band}</strong></span>
                    <span>24h Synoptic Lead</span>
                  </div>
                </div>

                {/* Administrative Population Baseline Reference Card */}
                <div className="rounded-xl border border-[#EAE3D9] bg-[#FBF9F5] p-3 space-y-1.5">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-[#2C221E] block">
                    Administrative Population Baseline
                  </span>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-[#635347]">Floodplain Residents (Baseline):</span>
                    <strong className="text-[#2C221E] font-mono">~37,500</strong>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-[#635347]">Identified Low-Lying Clusters:</span>
                    <strong className="text-[#2C221E]">14 Clusters</strong>
                  </div>
                  <p className="text-[9px] text-[#8C7869] leading-tight pt-1 border-t border-[#EAE3D9]">
                    * Baseline derived from published Delhi Disaster Management Authority (DDMA) 2023 flood data. Population figures are an administrative planning benchmark and are <strong>never dynamically calculated from risk categories</strong>.
                  </p>
                </div>
              </div>
            )}

            {/* Candidate Relief Shelters */}
            {assessment && assessment.candidate_shelters.length > 0 && (
              <div className="space-y-2.5 pt-2 border-t border-[#EAE3D9]">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-[#2C221E]">
                    Candidate Relief Shelters
                  </span>
                  {onNavigateToDisaster && (
                    <button
                      type="button"
                      onClick={onNavigateToDisaster}
                      className="text-[10px] font-bold text-[#8B4513] hover:underline flex items-center gap-0.5 cursor-pointer"
                    >
                      View All in Disaster Response <ChevronRight className="h-3 w-3" />
                    </button>
                  )}
                </div>

                <div className="space-y-2">
                  {assessment.candidate_shelters.slice(0, 3).map((shelter) => (
                    <div
                      key={shelter.shelter_id}
                      className="rounded-xl border border-[#EAE3D9] bg-[#FFFFFF] p-2.5 hover:border-[#8B4513] transition-colors shadow-2xs"
                    >
                      <div className="flex items-start justify-between">
                        <div className="font-bold text-xs text-[#2C221E] leading-tight">
                          {shelter.name}
                        </div>
                        <span className="rounded-full bg-[#F5EFEB] px-2 py-0.5 text-[9px] font-mono font-bold text-[#8B4513] shrink-0">
                          {shelter.approx_distance_km} km
                        </span>
                      </div>
                      <div className="mt-1 flex items-center justify-between text-[10px] text-[#635347]">
                        <span>{shelter.zone}</span>
                        <span>Capacity: ~{shelter.estimated_capacity_persons} persons</span>
                      </div>
                      <div className="mt-1 text-[9px] text-[#8C7869] italic">
                        Candidate shelter for planning. Real-time occupancy tracking is unavailable.
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Scientific Provenance Guardrails Box */}
            {assessment && (
              <div className="rounded-xl border border-[#EAE3D9] bg-[#F5EFEB] p-3 text-[10px] text-[#2C221E] space-y-1.5">
                <div className="font-bold uppercase tracking-wider text-[#8B4513]">
                  Scientific Provenance & Limitations
                </div>
                <div>
                  <strong>ML Model:</strong> Hathnikund upstream discharge (Audited Test R²=0.380, RMSE=469.5 m³/s).
                </div>
                <div>
                  <strong>Distinction:</strong> Upstream predicted discharge is strictly separated from downstream reach flood risk and static population baseline.
                </div>
                <div>
                  <strong>Shelters & Corridors:</strong> Evacuation corridors are designated planning routes (road-network inundation is unverified; never describe as guaranteed safe).
                </div>
              </div>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
};
