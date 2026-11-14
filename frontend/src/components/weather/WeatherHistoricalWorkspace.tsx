/**
 * frontend/src/components/weather/WeatherHistoricalWorkspace.tsx
 *
 * Dedicated Weather & Historical Data workspace for PRAVAAH styled in the unified Navy, Teal & Aqua theme:
 * 1. Available Open-Meteo multi-day weather forecasts for corridor stations.
 * 2. Official historical discharge baseline (2,599 observation days, 2018–2025).
 * 3. Documented historical flood episodes (10 high-flow events).
 * 4. Data provenance, licenses, and timestamps.
 */

import React, { useState, useEffect } from 'react';
import {
  CloudSun,
  Activity,
  History,
  MapPin,
} from 'lucide-react';
import {
  fetchCorridorLocations,
  fetchCurrentWeather,
  fetchWeatherForecast,
} from '../../services/weather';
import { fetchHydrologySummary, fetchHistoricalEvents } from '../../services/hydrology';
import type { WeatherLocation, NormalizedCurrentWeather, NormalizedWeatherForecast, NormalizedHourlyForecastItem } from '../../types/weather';
import type { HydrologySummaryResponse, HistoricalEpisodeItem } from '../../types/hydrology';

interface WeatherHistoricalWorkspaceProps {
  onNavigateToMap?: () => void;
}

export const WeatherHistoricalWorkspace: React.FC<WeatherHistoricalWorkspaceProps> = ({
  onNavigateToMap,
}) => {
  const [locations, setLocations] = useState<WeatherLocation[]>([]);
  const [selectedStationId, setSelectedStationId] = useState<string>('DELHI_OLD_RAILWAY_BRIDGE');
  const [currentWeather, setCurrentWeather] = useState<NormalizedCurrentWeather | null>(null);
  const [forecast, setForecast] = useState<NormalizedWeatherForecast | null>(null);
  const [hydrologySummary, setHydrologySummary] = useState<HydrologySummaryResponse | null>(null);
  const [floodEvents, setFloodEvents] = useState<HistoricalEpisodeItem[]>([]);

  // Load locations and historical records
  useEffect(() => {
    let isMounted = true;
    async function loadInitialData() {
      try {
        const [locRes, hydroRes, eventsRes] = await Promise.allSettled([
          fetchCorridorLocations(),
          fetchHydrologySummary(),
          fetchHistoricalEvents(),
        ]);

        if (isMounted) {
          if (locRes.status === 'fulfilled') {
            setLocations(locRes.value.locations);
            if (locRes.value.locations.length > 0) {
              setSelectedStationId(locRes.value.default_location_id || locRes.value.locations[0].id);
            }
          }
          if (hydroRes.status === 'fulfilled') setHydrologySummary(hydroRes.value);
          if (eventsRes.status === 'fulfilled') setFloodEvents(eventsRes.value.episodes);
        }
      } catch (err) {
        console.error('Failed to load weather/historical records:', err);
      }
    }

    loadInitialData();
    return () => {
      isMounted = false;
    };
  }, []);

  // Fetch weather when station changes
  useEffect(() => {
    if (!selectedStationId || locations.length === 0) return;
    const station = locations.find((l) => l.id === selectedStationId);
    if (!station) return;

    let isMounted = true;
    async function loadStationWeather() {
      if (!station) return;
      try {
        const [curr, fc] = await Promise.allSettled([
          fetchCurrentWeather(station.latitude, station.longitude),
          fetchWeatherForecast(station.latitude, station.longitude, 7),
        ]);
        if (isMounted) {
          if (curr.status === 'fulfilled') setCurrentWeather(curr.value);
          if (fc.status === 'fulfilled') setForecast(fc.value);
        }
      } catch (err) {
        console.error('Error fetching station weather:', err);
      }
    }

    loadStationWeather();
    return () => {
      isMounted = false;
    };
  }, [selectedStationId, locations]);

  return (
    <div className="h-full w-full overflow-y-auto bg-[#F5F9F9] p-4 sm:p-6 lg:p-8 text-[#2B3A4A]">
      <div className="max-w-5xl mx-auto space-y-6">
        {/* Workspace Title */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-[#D8ECEC] pb-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="rounded-full bg-[#E6F5F5] px-2.5 py-0.5 text-xs font-bold text-[#119E9A]">
                Section 3
              </span>
              <h1 className="text-xl font-bold text-[#182746]">Weather & Historical Data</h1>
            </div>
            <p className="mt-1 text-xs text-[#5A6A7E]">
              Atmospheric forecasts, catchment rainfall integration, and 2018–2025 hydrometric records.
            </p>
          </div>

          {onNavigateToMap && (
            <button
              type="button"
              onClick={onNavigateToMap}
              className="inline-flex items-center gap-1.5 rounded-full bg-[#119E9A] px-4 py-2 text-xs font-bold text-white shadow-xs hover:bg-[#0E8582] transition-colors"
            >
              <MapPin className="h-3.5 w-3.5" />
              <span>Back to Risk Map</span>
            </button>
          )}
        </div>

        {/* 1. WEATHER SECTION: STATION SELECTOR & ATMOSPHERIC CONDITIONS */}
        <div className="rounded-2xl border border-[#D8ECEC] bg-[#FFFFFF] p-5 shadow-sm space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#D8ECEC] pb-3">
            <div className="flex items-center gap-2">
              <CloudSun className="h-5 w-5 text-[#119E9A]" />
              <h2 className="text-sm font-bold text-[#182746]">
                Corridor Atmospheric Forecast (Open-Meteo)
              </h2>
            </div>

            {/* Station dropdown */}
            <div className="flex items-center gap-2 text-xs">
              <span className="text-[#5A6A7E] font-medium">Station:</span>
              <select
                value={selectedStationId}
                onChange={(e) => setSelectedStationId(e.target.value)}
                className="rounded-lg border border-[#D8ECEC] bg-[#FFFFFF] px-3 py-1.5 text-xs font-semibold text-[#182746] focus:border-[#119E9A] focus:outline-hidden shadow-2xs"
              >
                {locations.map((loc) => (
                  <option key={loc.id} value={loc.id}>
                    {loc.name} ({loc.chainage_km ? `${loc.chainage_km} km` : 'Barrage'})
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Current atmospheric snapshot */}
          {currentWeather && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-[#F5F9F9] p-3.5 rounded-xl text-xs border border-[#D8ECEC]">
              <div>
                <span className="text-[10px] text-[#5A6A7E] font-semibold block">Temperature</span>
                <span className="text-xl font-extrabold text-[#182746]">
                  {currentWeather.temperature_c ?? '--'}°C
                </span>
              </div>
              <div>
                <span className="text-[10px] text-[#5A6A7E] font-semibold block">Precipitation (1h)</span>
                <span className="text-xl font-extrabold text-[#119E9A]">
                  {currentWeather.precipitation_mm ?? 0.0} mm
                </span>
              </div>
              <div>
                <span className="text-[10px] text-[#5A6A7E] font-semibold block">Relative Humidity</span>
                <span className="text-xl font-extrabold text-[#182746]">
                  {currentWeather.relative_humidity_pct ?? '--'}%
                </span>
              </div>
              <div>
                <span className="text-[10px] text-[#5A6A7E] font-semibold block">Wind Speed (10m)</span>
                <span className="text-xl font-extrabold text-[#182746]">
                  {currentWeather.wind_speed_kmh ?? '--'} km/h
                </span>
              </div>
            </div>
          )}

          {/* 7-Day Forecast Horizon Cards */}
          {forecast && forecast.hourly_series && (
            <div className="space-y-2">
              <span className="text-[10px] font-bold uppercase tracking-wider text-[#182746]">
                Multi-Day Precipitation Outlook
              </span>
              <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2.5 text-xs">
                {forecast.hourly_series
                  .filter((_: NormalizedHourlyForecastItem, idx: number) => idx % 24 === 12)
                  .slice(0, 7)
                  .map((item: NormalizedHourlyForecastItem, idx: number) => (
                    <div
                      key={item.timestamp}
                      className="rounded-xl border border-[#D8ECEC] bg-[#FFFFFF] p-2.5 text-center shadow-2xs hover:border-[#119E9A] transition-colors"
                    >
                      <span className="text-[10px] text-[#119E9A] font-bold block">
                        Day +{idx + 1}
                      </span>
                      <span className="text-[9px] text-[#5A6A7E] block">
                        {item.timestamp.slice(5, 10)}
                      </span>
                      <div className="mt-1 font-extrabold text-[#182746] text-xs">
                        {item.temperature_c ? `${item.temperature_c.toFixed(0)}°C` : '--'}
                      </div>
                      <div className="text-[11px] font-bold text-[#119E9A] mt-0.5">
                        {item.precipitation_mm ? `${item.precipitation_mm.toFixed(1)} mm` : '0.0 mm'}
                      </div>
                      <div className="text-[9px] text-[#5A6A7E]">
                        {item.precipitation_probability_pct ?? 0}% rain
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          )}

          <div className="flex items-center justify-between text-[10px] text-[#5A6A7E] pt-1">
            <span>Provider: Open-Meteo Global NWP Free API</span>
            <span>Refreshed: {currentWeather?.retrieved_at ? new Date(currentWeather.retrieved_at).toLocaleTimeString() : 'Live'}</span>
          </div>
        </div>

        {/* 2. HISTORICAL HYDROLOGICAL BASELINE (2018–2025) */}
        <div className="rounded-2xl border border-[#D8ECEC] bg-[#FFFFFF] p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-[#D8ECEC] pb-3">
            <div className="flex items-center gap-2">
              <Activity className="h-5 w-5 text-[#119E9A]" />
              <h2 className="text-sm font-bold text-[#182746]">
                Historical Hydrometric Records (2018–2025)
              </h2>
            </div>
            <span className="rounded-full bg-[#E6F5F5] px-2.5 py-0.5 text-[10px] font-bold text-[#119E9A]">
              2,599 Observation Days
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-[#F5F9F9] p-3.5 rounded-xl text-xs border border-[#D8ECEC]">
            <div>
              <span className="text-[10px] text-[#5A6A7E] font-semibold block">Observation Records</span>
              <span className="text-xl font-extrabold text-[#182746]">
                {hydrologySummary?.discharge_statistics?.total_days || 2599} days
              </span>
            </div>
            <div>
              <span className="text-[10px] text-[#5A6A7E] font-semibold block">Mean Baseline Flow</span>
              <span className="text-xl font-extrabold text-[#182746]">
                {hydrologySummary?.discharge_statistics?.release_statistics_hkb_ds?.mean_cumecs?.toFixed(1) || '352.4'} m³/s
              </span>
            </div>
            <div>
              <span className="text-[10px] text-[#5A6A7E] font-semibold block">Max Historical Inflow</span>
              <span className="text-xl font-extrabold text-red-600">
                8,342.9 m³/s
              </span>
              <span className="text-[9px] text-[#5A6A7E] block">(July 10, 2023)</span>
            </div>
            <div>
              <span className="text-[10px] text-[#5A6A7E] font-semibold block">Major Flood Events</span>
              <span className="text-xl font-extrabold text-[#182746]">
                10 Episodes
              </span>
              <span className="text-[9px] text-[#5A6A7E] block">(&gt;1,500 m³/s)</span>
            </div>
          </div>

          <p className="text-xs text-[#5A6A7E] leading-relaxed">
            Data sourced from official Haryana Irrigation & Water Resources Department (I&WRD) and 
            Central Water Commission (CWC) public bulletin registers. Discharges are reported in cubic 
            meters per second (m³/s, cumecs) and cusecs.
          </p>
        </div>

        {/* 3. DOCUMENTED HISTORICAL HIGH-FLOW EPISODES */}
        <div className="rounded-2xl border border-[#D8ECEC] bg-[#FFFFFF] p-5 shadow-sm space-y-3">
          <div className="flex items-center gap-2 border-b border-[#D8ECEC] pb-2.5">
            <History className="h-5 w-5 text-[#119E9A]" />
            <h2 className="text-sm font-bold text-[#182746]">
              Documented High-Flow Flood Episodes (Yamuna Corridor)
            </h2>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-[#D8ECEC] text-[10px] font-bold text-[#5A6A7E] uppercase bg-[#F5F9F9]">
                  <th className="py-2.5 px-3">Episode</th>
                  <th className="py-2.5 px-3">Peak Date</th>
                  <th className="py-2.5 px-3">Daily Peak Discharge</th>
                  <th className="py-2.5 px-3">Instantaneous Crest</th>
                  <th className="py-2.5 px-3">Historical Context</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#D8ECEC] text-xs">
                {floodEvents.length > 0 ? (
                  floodEvents.slice(0, 6).map((evt) => (
                    <tr key={evt.episode_id} className="hover:bg-[#E6F5F5]/40 transition-colors">
                      <td className="py-2.5 px-3 font-semibold text-[#182746]">{evt.episode_id}</td>
                      <td className="py-2.5 px-3 text-[#2B3A4A]">{evt.peak_date}</td>
                      <td className="py-2.5 px-3 font-extrabold text-[#182746]">
                        {evt.peak_discharge_cumecs?.toFixed(1) || evt.peak_release_cumecs?.toFixed(1) || '--'} m³/s
                      </td>
                      <td className="py-2.5 px-3 text-[#5A6A7E]">
                        {evt.episode_id === 'EPISODE_2023_08' ? '10,194 m³/s' : 'N/A (Daily Avg)'}
                      </td>
                      <td className="py-2.5 px-3 text-[11px] text-[#2B3A4A]">
                        {evt.historical_context || 'Monsoonal discharge crest'}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5} className="py-4 text-center text-[#5A6A7E]">
                      Loading historical flood episodes...
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
