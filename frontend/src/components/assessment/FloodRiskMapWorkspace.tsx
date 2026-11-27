/**
 * frontend/src/components/assessment/FloodRiskMapWorkspace.tsx
 *
 * Primary interactive workspace for PRAVAAH — AI-Powered Flood Risk Assessment & Management System.
 * Styled in the unified Deep Navy, Teal, and Aqua theme matching the landing page.
 * Enables first-time users to:
 * 1. Select a geographical area (dropdown or map click).
 * 2. Select forecast horizon between 2 and 10 days.
 * 3. Assess flood risk via live backend ML & meteorological coupling.
 * 4. Visualize Green / Orange / Red risk zones on the interactive Leaflet map.
 * 5. Inspect contributing factors, forecast confidence decay, and candidate evacuation shelters.
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
  Calendar,
  MapPin,
  RefreshCw,
  ChevronRight,
  Info,
  CloudRain,
  Activity,
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
  onNavigateToEvacuation?: () => void;
  onNavigateToWeather?: () => void;
}

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
      return '#16a34a'; // Emerald 600
    case 'ORANGE':
      return '#ea580c'; // Orange 600
    case 'RED':
      return '#dc2626'; // Red 600
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
  onNavigateToWeather,
}) => {
  // Areas and Assessment State
  const [areas, setAreas] = useState<SupportedArea[]>([]);
  const [selectedAreaId, setSelectedAreaId] = useState<string>('DELHI_CENTRAL');
  const [forecastDays, setForecastDays] = useState<number>(3);
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

  // Initial assessment trigger when areas load
  useEffect(() => {
    if (selectedAreaId) {
      runAssessment(selectedAreaId, forecastDays);
    }
  }, [selectedAreaId]);

  const runAssessment = async (areaId: string, days: number) => {
    setIsAssessing(true);
    setErrorMessage(null);
    try {
      const res = await riskAssessmentApi.assessRisk({
        area_id: areaId,
        forecast_days: days,
      });
      setAssessment(res);
    } catch (err: any) {
      setErrorMessage(err?.message || 'Failed to complete risk assessment.');
    } finally {
      setIsAssessing(false);
    }
  };

  const handleAreaChange = (newAreaId: string) => {
    setSelectedAreaId(newAreaId);
  };

  const handleHorizonChange = (newDays: number) => {
    setForecastDays(newDays);
    if (selectedAreaId) {
      runAssessment(selectedAreaId, newDays);
    }
  };

  // Find currently selected area object
  const currentArea = areas.find((a) => a.id === selectedAreaId);
  const centerCoord: [number, number] = currentArea?.representative_coord || [28.66, 77.25];
  const zoomLevel = currentArea?.area_type === 'CORRIDOR_ALL' ? 8 : currentArea?.area_type === 'BASIN' ? 8 : 10;

  // Determine reach color styling based on assessment reach_risks
  const getWayColor = (wayId?: number): string => {
    if (!assessment || !wayId) return '#16a34a';
    const match = assessment.reach_risks.find((r) => r.osm_way_id === wayId);
    return match ? getRiskColorCode(match.risk_color) : '#16a34a';
  };

  return (
    <div className="flex h-full w-full flex-col overflow-hidden bg-[#F5F9F9] text-[#2B3A4A]">
      {/* 1. TOP CONTROL BAR: AREA & FORECAST HORIZON SELECTOR */}
      <div className="shrink-0 border-b border-[#D8ECEC] bg-[#FFFFFF] px-4 py-2.5 shadow-2xs">
        <div className="flex flex-wrap items-center justify-between gap-3">
          {/* Area Selector Dropdown */}
          <div className="flex items-center gap-2">
            <span className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-[#182746]">
              <MapPin className="h-4 w-4 text-[#119E9A]" />
              Area:
            </span>
            <select
              value={selectedAreaId}
              onChange={(e) => handleAreaChange(e.target.value)}
              className="rounded-lg border border-[#D8ECEC] bg-[#FFFFFF] px-3 py-1.5 text-xs font-semibold text-[#182746] focus:border-[#119E9A] focus:outline-hidden shadow-2xs"
              aria-label="Select geographical area"
            >
              {areas.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name} ({a.area_type})
                </option>
              ))}
            </select>
          </div>

          {/* Forecast Horizon Selector (2 to 10 Days) */}
          <div className="flex items-center gap-2">
            <span className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-[#182746]">
              <Calendar className="h-4 w-4 text-[#119E9A]" />
              Horizon:
            </span>
            <div className="flex items-center rounded-lg border border-[#D8ECEC] bg-[#F5F9F9] p-0.5">
              {[2, 3, 4, 5, 6, 7, 8, 9, 10].map((d) => (
                <button
                  key={d}
                  type="button"
                  onClick={() => handleHorizonChange(d)}
                  className={`px-2.5 py-1 text-xs font-medium rounded-md transition-all ${
                    forecastDays === d
                      ? 'bg-[#119E9A] text-white font-bold shadow-2xs'
                      : 'text-[#2B3A4A] hover:bg-[#E6F5F5] hover:text-[#182746]'
                  }`}
                  title={`${d} Days Forecast Horizon`}
                >
                  {d}d
                </button>
              ))}
            </div>

            {/* Assessment Confidence Tag */}
            {assessment && (
              <span
                className={`hidden sm:inline-flex items-center rounded-full px-2.5 py-0.5 text-[11px] font-semibold border ${
                  assessment.confidence.confidence_level === 'HIGH'
                    ? 'bg-emerald-50 text-emerald-800 border-emerald-300'
                    : assessment.confidence.confidence_level === 'MODERATE'
                    ? 'bg-amber-50 text-amber-800 border-amber-300'
                    : 'bg-slate-100 text-slate-700 border-slate-300'
                }`}
              >
                {assessment.confidence.confidence_score_pct}% Conf. ({assessment.confidence.confidence_level})
              </span>
            )}
          </div>

          {/* Action Button: Re-Assess */}
          <button
            type="button"
            onClick={() => runAssessment(selectedAreaId, forecastDays)}
            disabled={isAssessing}
            className="flex items-center gap-1.5 rounded-full bg-[#119E9A] px-4 py-2 text-xs font-bold text-white shadow-xs hover:bg-[#0E8582] active:scale-98 disabled:opacity-60 transition-all"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isAssessing ? 'animate-spin' : ''}`} />
            <span>{isAssessing ? 'Assessing...' : 'Assess Flood Risk'}</span>
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
                    color: assessment?.risk_color === 'RED' ? '#dc2626' : '#25345B',
                    weight: 2,
                    fillColor: assessment?.risk_color === 'RED' ? '#dc2626' : '#119E9A',
                    fillOpacity: 0.12,
                    dashArray: '4, 4',
                  }}
                  eventHandlers={{
                    click: () => handleAreaChange('UPSTREAM_CATCHMENT'),
                  }}
                />
              )}

              {/* Yamuna Downstream Mainstem Reaches Styled by Assessed Risk */}
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
                    `<div style="font-family: sans-serif; font-size: 11px;">
                      <strong>${segName}</strong><br/>
                      OSM Way: ${wayId || 'N/A'}<br/>
                      <em>Click reach to assess localized flood risk.</em>
                    </div>`
                  );
                }}
              />
            )}

            {/* 7 Corridor Monitoring Stations with Risk Colored Markers */}
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
                        <div className="font-semibold text-slate-900">{station.station_name}</div>
                        <div className="text-[11px] text-slate-600">Chainage: {station.chainage_km} km</div>
                        <div className="mt-1 flex items-center gap-1 font-medium">
                          Status: <span style={{ color: markerColor }}>{station.risk_level} RISK</span>
                        </div>
                        <div className="text-[10px] text-slate-500 mt-0.5">
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
                    html: `<div style="background-color: #119E9A; color: white; border: 1.5px solid white; border-radius: 4px; padding: 2px 4px; font-size: 9px; font-weight: bold; box-shadow: 0 1px 3px rgba(0,0,0,0.3); display: flex; align-items: center; gap: 2px;">
                      <span>🏠</span>
                    </div>`,
                    iconSize: [22, 22],
                    iconAnchor: [11, 11],
                  })}
                >
                  <Popup>
                    <div className="text-xs p-1 max-w-[200px]">
                      <div className="font-semibold text-slate-900">{shelter.name}</div>
                      <div className="text-[10px] text-amber-700 font-medium">
                        Candidate Shelter ({shelter.validation_status.split(' ')[0]})
                      </div>
                      <div className="mt-1 text-[11px] text-slate-600">
                        Cap: ~{shelter.estimated_capacity_persons} persons • Dist: {shelter.approx_distance_km} km
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
            <div className="rounded-xl border border-[#D8ECEC] bg-[#FFFFFF]/95 backdrop-blur-xs p-3 shadow-sm text-xs">
              <span className="block text-[10px] font-bold uppercase tracking-wider text-[#182746] mb-1.5">
                Risk Classification
              </span>
              <div className="space-y-1.5 text-[11px] font-semibold">
                <div className="flex items-center gap-2">
                  <span className="h-2.5 w-2.5 rounded-full bg-emerald-600" />
                  <span className="text-[#2B3A4A]">GREEN — Low Risk</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="h-2.5 w-2.5 rounded-full bg-amber-500" />
                  <span className="text-[#2B3A4A]">ORANGE — Moderate Risk</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="h-2.5 w-2.5 rounded-full bg-red-600" />
                  <span className="text-[#2B3A4A]">RED — High Risk</span>
                </div>
              </div>
            </div>

            {/* Quick Layer Visibility Toggles */}
            <div className="rounded-xl border border-[#D8ECEC] bg-[#FFFFFF]/95 backdrop-blur-xs p-3 shadow-sm text-[11px]">
              <span className="block text-[10px] font-bold uppercase tracking-wider text-[#182746] mb-1.5">
                Map Layers
              </span>
              <div className="space-y-1.5">
                <label className="flex items-center gap-2 cursor-pointer font-medium text-[#2B3A4A]">
                  <input
                    type="checkbox"
                    checked={showRiver}
                    onChange={(e) => setShowRiver(e.target.checked)}
                    className="rounded border-[#D8ECEC] text-[#119E9A] focus:ring-[#119E9A]"
                  />
                  <span>River Centerline</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer font-medium text-[#2B3A4A]">
                  <input
                    type="checkbox"
                    checked={showCatchment}
                    onChange={(e) => setShowCatchment(e.target.checked)}
                    className="rounded border-[#D8ECEC] text-[#119E9A] focus:ring-[#119E9A]"
                  />
                  <span>Upstream Basin</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer font-medium text-[#2B3A4A]">
                  <input
                    type="checkbox"
                    checked={showStations}
                    onChange={(e) => setShowStations(e.target.checked)}
                    className="rounded border-[#D8ECEC] text-[#119E9A] focus:ring-[#119E9A]"
                  />
                  <span>Gauge Stations</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer font-medium text-[#2B3A4A]">
                  <input
                    type="checkbox"
                    checked={showShelters}
                    onChange={(e) => setShowShelters(e.target.checked)}
                    className="rounded border-[#D8ECEC] text-[#119E9A] focus:ring-[#119E9A]"
                  />
                  <span>Candidate Shelters</span>
                </label>
              </div>
            </div>
          </div>
        </div>

        {/* 3. RIGHT-SIDE ASSESSMENT RESULTS DRAWER */}
        <aside className="w-[360px] sm:w-[400px] shrink-0 border-l border-[#D8ECEC] bg-[#FFFFFF] overflow-y-auto shadow-sm">
          <div className="p-4 space-y-4 text-xs">
            {/* Drawer Header & Area Overview */}
            <div className="border-b border-[#D8ECEC] pb-3">
              <span className="text-[10px] font-bold uppercase tracking-wider text-[#119E9A]">
                Assessment Result
              </span>
              <h2 className="text-base font-bold text-[#182746] leading-snug">
                {assessment?.area_name || currentArea?.name}
              </h2>
              <p className="text-[11px] text-[#5A6A7E] mt-0.5">
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

            {/* Primary Risk Status Banner */}
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
                      {assessment.risk_level} RISK
                    </span>
                  </div>
                  <span className="rounded-full bg-white/90 px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-[#182746] shadow-2xs">
                    {assessment.forecast_days}-Day Horizon
                  </span>
                </div>

                <p className="mt-2.5 text-xs leading-relaxed font-medium">
                  {assessment.summary}
                </p>

                <div className="mt-3 rounded-lg bg-white/80 p-2.5 text-[11px] text-[#182746] border border-white">
                  <span className="font-bold">Recommended Guidance:</span> {assessment.guidance_action}
                </div>
              </div>
            )}

            {/* Contributing Factors & Live Forecast Breakdown */}
            {assessment && (
              <div className="space-y-2.5">
                <span className="text-[10px] font-bold uppercase tracking-wider text-[#182746]">
                  Contributing Data Factors
                </span>

                {/* Factor 1: Upstream Inflow Forecast (ML Model) */}
                <div className="rounded-xl border border-[#D8ECEC] bg-[#F5F9F9] p-3">
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-1.5 font-bold text-[#182746]">
                      <Activity className="h-4 w-4 text-[#119E9A]" />
                      Upstream Hathnikund Inflow
                    </span>
                    <span className="rounded-full bg-[#E6F5F5] px-2 py-0.5 text-[9px] font-bold text-[#119E9A]">
                      Random Forest ML
                    </span>
                  </div>
                  <div className="mt-1.5 flex items-baseline justify-between">
                    <span className="text-base font-extrabold text-[#182746]">
                      {assessment.upstream_ml_forecast.predicted_inflow_cumecs.toFixed(1)} m³/s
                    </span>
                    <span className="text-[11px] font-semibold text-[#5A6A7E]">
                      Band: {assessment.upstream_ml_forecast.flood_band}
                    </span>
                  </div>
                  <p className="mt-1 text-[10px] text-[#5A6A7E] leading-relaxed">
                    {assessment.upstream_ml_forecast.provenance_note}
                  </p>
                </div>

                {/* Factor 2: Weather Forecast (Open-Meteo) */}
                <div className="rounded-xl border border-[#D8ECEC] bg-[#F5F9F9] p-3">
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-1.5 font-bold text-[#182746]">
                      <CloudRain className="h-4 w-4 text-[#119E9A]" />
                      Atmospheric Rainfall
                    </span>
                    <span className="rounded-full bg-[#E6F5F5] px-2 py-0.5 text-[9px] font-bold text-[#119E9A]">
                      Open-Meteo API
                    </span>
                  </div>
                  <div className="mt-1.5 flex items-baseline justify-between">
                    <span className="text-base font-extrabold text-[#182746]">
                      {assessment.weather.total_forecast_rainfall_mm} mm
                    </span>
                    <span className="text-[11px] font-semibold text-[#5A6A7E]">
                      Peak: {assessment.weather.peak_daily_rainfall_mm} mm/day
                    </span>
                  </div>
                  <div className="mt-1 flex items-center justify-between text-[10px] text-[#5A6A7E]">
                    <span>Intensity: {assessment.weather.rainfall_risk_band}</span>
                    {onNavigateToWeather && (
                      <button
                        type="button"
                        onClick={onNavigateToWeather}
                        className="font-bold text-[#119E9A] hover:underline"
                      >
                        View Weather Charts →
                      </button>
                    )}
                  </div>
                </div>

                {/* Factor 3: Forecast Horizon & Confidence Decay */}
                <div className="rounded-xl border border-[#D8ECEC] bg-[#F5F9F9] p-3">
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-1.5 font-bold text-[#182746]">
                      <Info className="h-4 w-4 text-[#119E9A]" />
                      Forecast Confidence
                    </span>
                    <span className="font-extrabold text-[#182746]">
                      {assessment.confidence.confidence_score_pct}% ({assessment.confidence.confidence_level})
                    </span>
                  </div>
                  <p className="mt-1 text-[10px] leading-relaxed text-[#5A6A7E]">
                    {assessment.confidence.decay_explanation}
                  </p>
                </div>
              </div>
            )}

            {/* Nearby Candidate Evacuation Locations */}
            {assessment && assessment.candidate_shelters.length > 0 && (
              <div className="space-y-2.5 pt-2 border-t border-[#D8ECEC]">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-[#182746]">
                    Candidate Evacuation Locations
                  </span>
                  {onNavigateToEvacuation && (
                    <button
                      type="button"
                      onClick={onNavigateToEvacuation}
                      className="text-[10px] font-bold text-[#119E9A] hover:underline flex items-center gap-0.5"
                    >
                      All Shelters <ChevronRight className="h-3 w-3" />
                    </button>
                  )}
                </div>

                <div className="space-y-2">
                  {assessment.candidate_shelters.slice(0, 3).map((shelter) => (
                    <div
                      key={shelter.shelter_id}
                      className="rounded-xl border border-[#D8ECEC] bg-[#FFFFFF] p-2.5 hover:border-[#119E9A] transition-colors shadow-2xs"
                    >
                      <div className="flex items-start justify-between">
                        <div className="font-bold text-xs text-[#182746] leading-tight">
                          {shelter.name}
                        </div>
                        <span className="rounded-full bg-[#E6F5F5] px-2 py-0.5 text-[9px] font-mono font-bold text-[#119E9A] shrink-0">
                          {shelter.approx_distance_km} km
                        </span>
                      </div>
                      <div className="mt-1 flex items-center justify-between text-[10px] text-[#5A6A7E]">
                        <span>{shelter.zone}</span>
                        <span>Cap: ~{shelter.estimated_capacity_persons}</span>
                      </div>
                    </div>
                  ))}
                </div>

                <p className="text-[9px] text-[#5A6A7E] italic leading-tight">
                  * Candidate shelters are illustrative municipal planning facilities. Road submergence clearances are unvalidated.
                </p>
              </div>
            )}

            {/* Scientific Provenance Guardrails Box */}
            {assessment && (
              <div className="rounded-xl border border-[#C8E5E5] bg-[#E6F5F5] p-3 text-[10px] text-[#182746] space-y-1">
                <div className="font-bold uppercase tracking-wider text-[#119E9A]">
                  Data Provenance & Scientific Guardrails
                </div>
                <div>
                  <strong>ML Target:</strong> Hathnikund upstream discharge (R²=0.88).
                </div>
                <div>
                  <strong>Risk Rules:</strong> Official CWC warning & danger thresholds.
                </div>
                <div>
                  <strong>Limitations:</strong> Real-time downstream stage telemetry at Delhi ORB is restricted by CWC. 2D floodplain inundation depth is not modeled.
                </div>
              </div>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
};
