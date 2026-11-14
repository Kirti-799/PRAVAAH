import React, { useEffect, useState } from 'react';
import {
  Waves,
  CloudRain,
  AlertTriangle,
  Calendar,
  ArrowUpRight,
  TrendingDown,
  RefreshCw,
  GitCommit,
  Activity,
} from 'lucide-react';
import type { HydrologySummaryResponse } from '../../types/hydrology';
import type { RoutingReadinessResponse, RoutingSimulationResponse } from '../../types/routing';
import type {
  ForecastingReadinessResponse,
  DischargeModelStatusResponse,
  ExperimentalDischargeForecastResponse,
} from '../../types/forecasting';
import { fetchHydrologySummary } from '../../services/hydrology';
import { fetchRoutingReadiness, fetchRoutingSimulation } from '../../services/routing';
import {
  fetchForecastingReadiness,
  fetchDischargeModelStatus,
  fetchSampleHistoricalForecast,
} from '../../services/forecasting';
import { TabletopScenarioWorkstation } from './TabletopScenarioWorkstation';

const KEY_EPISODES = [
  { id: 'EPISODE_2023_08', label: 'Historic July 2023 Flood (Record HFL)' },
  { id: 'EPISODE_2022_07', label: 'September 2022 Surge (Danger Mark Breached)' },
  { id: 'EPISODE_2019_04', label: 'August 2019 Inflow Surge (6.22 Lakh Cusecs)' },
];

export const HistoricalHydrologyPanel: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'baseline' | 'tabletop'>('tabletop');
  const [summaryData, setSummaryData] = useState<HydrologySummaryResponse | null>(null);
  const [readinessData, setReadinessData] = useState<RoutingReadinessResponse | null>(null);
  const [simulationData, setSimulationData] = useState<RoutingSimulationResponse | null>(null);
  const [forecastingData, setForecastingData] = useState<ForecastingReadinessResponse | null>(null);
  const [modelStatus, setModelStatus] = useState<DischargeModelStatusResponse | null>(null);
  const [sampleForecast, setSampleForecast] = useState<ExperimentalDischargeForecastResponse | null>(null);
  const [selectedEpisode, setSelectedEpisode] = useState<string>('EPISODE_2023_08');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isSimLoading, setIsSimLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);


  const loadInitialData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [summary, readiness, sim, forecasting, mStatus, sForecast] = await Promise.all([
        fetchHydrologySummary(),
        fetchRoutingReadiness(),
        fetchRoutingSimulation(selectedEpisode),
        fetchForecastingReadiness(),
        fetchDischargeModelStatus().catch(() => null),
        fetchSampleHistoricalForecast().catch(() => null),
      ]);
      setSummaryData(summary);
      setReadinessData(readiness);
      setSimulationData(sim);
      setForecastingData(forecasting);
      setModelStatus(mStatus);
      setSampleForecast(sForecast);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to load hydrological data.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleEpisodeChange = async (episodeId: string) => {
    setSelectedEpisode(episodeId);
    setIsSimLoading(true);
    try {
      const sim = await fetchRoutingSimulation(episodeId);
      setSimulationData(sim);
    } catch (err: unknown) {
      console.error('Failed to simulate episode:', err);
    } finally {
      setIsSimLoading(false);
    }
  };

  useEffect(() => {
    loadInitialData();
  }, []);

  if (isLoading) {
    return (
      <div className="rounded-xl border border-[#D8ECEC] bg-[#FFFFFF] p-3 text-xs text-[#5A6A7E]">
        <div className="flex items-center gap-2">
          <RefreshCw className="h-3.5 w-3.5 animate-spin text-[#119E9A]" />
          <span>Loading historical hydrological observations & forecasting audits...</span>
        </div>
      </div>
    );
  }

  if (error || !summaryData) {
    return (
      <div className="rounded-xl border border-[#D8ECEC] bg-[#F5F9F9] p-3 text-xs">
        <div className="flex items-center justify-between">
          <span className="font-semibold text-[#182746]">Hydrological Baseline</span>
          <button
            onClick={loadInitialData}
            className="flex items-center gap-1 rounded-lg border border-[#D8ECEC] bg-[#FFFFFF] px-2 py-0.5 text-[10px] text-[#5A6A7E] hover:bg-[#E6F5F5]"
          >
            <RefreshCw className="h-2.5 w-2.5" />
            Retry
          </button>
        </div>
        <p className="mt-1 text-[11px] text-rose-700">
          {error || 'Hydrology service currently offline.'}
        </p>
      </div>
    );
  }

  const { latest_observations, rainfall_accumulations, discharge_statistics } = summaryData;

  return (
    <div className="rounded-xl border border-[#D8ECEC] bg-[#FFFFFF] p-4 text-xs text-[#2B3A4A] space-y-3 shadow-xs">
      {/* Panel Header */}
      <div className="flex items-center justify-between border-b border-[#D8ECEC] pb-2">
        <div className="flex items-center gap-1.5 font-semibold text-[#182746]">
          <Waves className="h-4 w-4 text-[#119E9A]" />
          <span>Yamuna Hydrological Baseline</span>
        </div>
        <span className="rounded-full bg-[#E6F5F5] border border-[#C8E5E5] px-2 py-0.5 text-[9px] font-mono font-medium text-[#182746]">
          Non-ML Empirical
        </span>
      </div>

      {/* Tab Switcher */}
      <div className="flex rounded-lg bg-[#E6F5F5] p-0.5 text-[10px]">
        <button
          type="button"
          onClick={() => setActiveTab('tabletop')}
          className={`flex-1 rounded-md py-1 font-medium transition-colors ${
            activeTab === 'tabletop'
              ? 'bg-[#FFFFFF] text-[#182746] font-semibold shadow-xs'
              : 'text-[#5A6A7E] hover:text-[#182746]'
          }`}
        >
          Tabletop Simulation (2C-B)
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('baseline')}
          className={`flex-1 rounded-md py-1 font-medium transition-colors ${
            activeTab === 'baseline'
              ? 'bg-[#FFFFFF] text-[#182746] font-semibold shadow-xs'
              : 'text-[#5A6A7E] hover:text-[#182746]'
          }`}
        >
          Historical Baseline
        </button>
      </div>

      {activeTab === 'tabletop' ? (
        <TabletopScenarioWorkstation />
      ) : (
        <>
          {/* Section 1: Upstream Regulatory Node (Hathnikund Barrage) */}

      <div className="space-y-1.5">
        <div className="flex items-center justify-between text-[11px] font-medium text-[#182746]">
          <span className="flex items-center gap-1">
            <Calendar className="h-3 w-3 text-[#119E9A]" />
            Hathnikund Discharge ({latest_observations.date})
          </span>
          <span className="text-[10px] text-[#5A6A7E]">Verified Inflow vs Release</span>
        </div>

        <div className="grid grid-cols-2 gap-2">
          {/* Inflow Box */}
          <div className="rounded-lg border border-[#D8ECEC] bg-[#F5F9F9] p-2.5">
            <div className="text-[10px] font-medium text-[#5A6A7E] flex items-center justify-between">
              <span>Upstream Inflow (HKB U/S)</span>
              <ArrowUpRight className="h-3 w-3 text-emerald-700" />
            </div>
            <div className="mt-1 text-sm font-semibold text-[#182746]">
              {latest_observations.inflow_discharge_cumecs?.toLocaleString()} <span className="text-[10px] font-normal text-[#5A6A7E]">m³/s</span>
            </div>
            <div className="text-[10px] text-[#5A6A7E]">
              {latest_observations.inflow_discharge_cusecs?.toLocaleString()} cusecs
            </div>
          </div>

          {/* Release Box */}
          <div className="rounded-lg border border-[#D8ECEC] bg-[#F5F9F9] p-2.5">
            <div className="text-[10px] font-medium text-[#5A6A7E] flex items-center justify-between">
              <span>River Release (HKB D/S)</span>
              <TrendingDown className="h-3 w-3 text-[#119E9A]" />
            </div>
            <div className="mt-1 text-sm font-semibold text-[#182746]">
              {latest_observations.release_discharge_cumecs?.toLocaleString()} <span className="text-[10px] font-normal text-[#5A6A7E]">m³/s</span>
            </div>
            <div className="text-[10px] text-[#5A6A7E]">
              {latest_observations.release_discharge_cusecs?.toLocaleString()} cusecs
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between text-[9px] text-[#5A6A7E] px-1">
          <span>Hist. Inflow p90: {discharge_statistics.inflow_statistics_hkb_us.p90_cumecs} m³/s</span>
          <span>Hist. Release Max: {discharge_statistics.release_statistics_hkb_ds.max_cumecs.toLocaleString()} m³/s</span>
        </div>
      </div>

      {/* Section 2: Catchment Rainfall Accumulations */}
      <div className="space-y-1.5">
        <div className="flex items-center justify-between text-[11px] font-medium text-[#182746]">
          <span className="flex items-center gap-1">
            <CloudRain className="h-3 w-3 text-[#119E9A]" />
            Catchment Rainfall (IMD 0.25° Grid)
          </span>
          <span className="text-[10px] text-[#5A6A7E]">91-Cell Mean</span>
        </div>

        <div className="grid grid-cols-3 gap-1.5 text-center">
          <div className="rounded-lg border border-[#D8ECEC] bg-[#F5F9F9] p-1.5">
            <div className="text-[9px] text-[#5A6A7E]">1-Day Prior</div>
            <div className="font-semibold text-[#182746] text-xs">
              {rainfall_accumulations.accum_1d_mm ?? '—'} <span className="text-[9px] font-normal">mm</span>
            </div>
          </div>
          <div className="rounded-lg border border-[#D8ECEC] bg-[#F5F9F9] p-1.5">
            <div className="text-[9px] text-[#5A6A7E]">3-Day Accum</div>
            <div className="font-semibold text-[#182746] text-xs">
              {rainfall_accumulations.accum_3d_mm ?? '—'} <span className="text-[9px] font-normal">mm</span>
            </div>
          </div>
          <div className="rounded-lg border border-[#D8ECEC] bg-[#F5F9F9] p-1.5">
            <div className="text-[9px] text-[#5A6A7E]">7-Day Accum</div>
            <div className="font-semibold text-[#182746] text-xs">
              {rainfall_accumulations.accum_7d_mm ?? '—'} <span className="text-[9px] font-normal">mm</span>
            </div>
          </div>
        </div>
      </div>

      {/* Section 3: Downstream Routing Feasibility & Prototype */}
      <div className="rounded-lg border border-[#D8ECEC] bg-[#F5F9F9] p-2.5 space-y-2">
        <div className="flex items-center justify-between border-b border-[#D8ECEC]/60 pb-1.5">
          <div className="flex items-center gap-1.5 font-semibold text-[#182746] text-[11px]">
            <GitCommit className="h-3.5 w-3.5 text-[#119E9A]" />
            <span>Downstream Routing Prototype</span>
          </div>
          <span className="rounded-full bg-[#E6F5F5] border border-[#C8E5E5] text-[#182746] px-2 py-0.5 text-[8px] font-mono uppercase">
            {readinessData?.readiness_status === 'ROUTING_PARAMETRIC_PROTOTYPE_UNCALIBRATED'
              ? 'Uncalibrated Prototype'
              : 'Routing Not Ready'}
          </span>
        </div>

        {/* Hydraulic Parameter Status Chips */}
        <div className="grid grid-cols-2 gap-1.5 text-[9px]">
          <div className="flex items-center justify-between rounded-md bg-[#FFFFFF] px-2 py-1 border border-[#D8ECEC]">
            <span className="text-[#5A6A7E]">Thalweg Reach:</span>
            <span className="font-mono font-medium text-[#119E9A]">220 km (Derived)</span>
          </div>
          <div className="flex items-center justify-between rounded-md bg-[#FFFFFF] px-2 py-1 border border-[#D8ECEC]">
            <span className="text-[#5A6A7E]">Bed Slope (S₀):</span>
            <span className="font-mono font-medium text-[#119E9A]">0.00034 (Derived)</span>
          </div>
          <div className="flex items-center justify-between rounded-md bg-[#FFFFFF] px-2 py-1 border border-[#D8ECEC]">
            <span className="text-[#5A6A7E]">Bathymetry:</span>
            <span className="font-mono font-medium text-rose-700">UNAVAILABLE</span>
          </div>
          <div className="flex items-center justify-between rounded-md bg-[#FFFFFF] px-2 py-1 border border-[#D8ECEC]">
            <span className="text-[#5A6A7E]">Target Calibration:</span>
            <span className="font-mono font-medium text-rose-700">UNAVAILABLE</span>
          </div>
        </div>

        {/* Episode Selector for Routing Simulation */}
        <div className="space-y-1">
          <div className="flex items-center justify-between text-[10px]">
            <span className="text-[#5A6A7E] font-medium">Historical Episode Simulation:</span>
            {isSimLoading && <RefreshCw className="h-2.5 w-2.5 animate-spin text-[#119E9A]" />}
          </div>
          <select
            value={selectedEpisode}
            onChange={(e) => handleEpisodeChange(e.target.value)}
            disabled={isSimLoading}
            className="w-full rounded-md border border-[#D8ECEC] bg-[#FFFFFF] px-2 py-1 text-[10px] text-[#2B3A4A] focus:border-[#119E9A] focus:outline-hidden"
          >
            {KEY_EPISODES.map((ep) => (
              <option key={ep.id} value={ep.id}>
                {ep.label}
              </option>
            ))}
          </select>
        </div>

        {/* Simulation Output Card */}
        {simulationData && (
          <div className="space-y-1.5 pt-1">
            <div className="rounded-md bg-[#E6F5F5] border border-[#C8E5E5] p-1.5 text-[9px] text-[#182746] font-medium text-center">
              SIMULATED DOWNSTREAM DISCHARGE — NOT OBSERVED DELHI WATER LEVEL
            </div>

            <div className="grid grid-cols-2 gap-1.5">
              <div className="rounded-md bg-[#FFFFFF] p-1.5 border border-[#D8ECEC]">
                <div className="text-[9px] text-[#5A6A7E]">Hathnikund Peak Release</div>
                <div className="font-semibold text-xs text-[#182746]">
                  {simulationData.observed_hathnikund_peak_release_cumecs.toLocaleString()} <span className="text-[8px] font-normal">m³/s</span>
                </div>
                <div className="text-[8px] text-[#5A6A7E]">{simulationData.observed_hathnikund_peak_date}</div>
              </div>

              <div className="rounded-md bg-[#FFFFFF] p-1.5 border border-[#D8ECEC]">
                <div className="text-[9px] text-[#5A6A7E]">Simulated Routed Peak</div>
                <div className="font-semibold text-xs text-[#119E9A]">
                  {simulationData.simulated_peak_downstream_discharge_cumecs.toLocaleString()} <span className="text-[8px] font-normal">m³/s</span>
                </div>
                <div className="text-[8px] text-[#5A6A7E]">{simulationData.simulated_peak_downstream_date}</div>
              </div>
            </div>

            <div className="flex items-center justify-between text-[9px] text-[#5A6A7E] px-1">
              <span>Simulated Attenuation: <strong>{simulationData.simulated_attenuation_percent}%</strong></span>
              <span>Wave Transit Lag: <strong>{simulationData.simulated_lag_hours} h</strong></span>
            </div>

            {simulationData.documented_delhi_crest_stage_m && (
              <div className="rounded-md bg-[#E6F5F5] p-1 text-[9px] text-[#182746] flex items-center justify-between border border-[#C8E5E5]">
                <span>Hist. Delhi Crest Reference:</span>
                <span className="font-mono font-medium">
                  {simulationData.documented_delhi_crest_stage_m} m MSL ({simulationData.documented_delhi_crest_date})
                </span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Section 4: Upstream 24h Forecasting Research (Phase 2A Baseline) */}
      {forecastingData && (
        <div className="rounded-lg border border-[#D8ECEC] bg-[#F5F9F9] p-2.5 space-y-2">
          <div className="flex items-center justify-between border-b border-[#D8ECEC]/60 pb-1.5">
            <div className="flex items-center gap-1.5 font-semibold text-[#182746] text-[11px]">
              <Activity className="h-3.5 w-3.5 text-[#119E9A]" />
              <span>Upstream 24h Forecasting Research</span>
            </div>
            <span className="rounded-full bg-[#E6F5F5] border border-[#C8E5E5] px-2 py-0.5 text-[8px] font-mono font-medium text-[#182746]">
              Phase 2A Baseline
            </span>
          </div>

          <div className="text-[10px] text-[#5A6A7E]">
            Hathnikund downstream discharge — preliminary forecasting research
          </div>

          <div className="grid grid-cols-3 gap-1.5 text-center text-[9px]">
            <div className="rounded-md bg-[#FFFFFF] p-1 border border-[#D8ECEC]">
              <div className="text-[#5A6A7E]">Train (18–21)</div>
              <div className="font-semibold text-[#182746]">{forecastingData.partitions.TRAIN} d</div>
            </div>
            <div className="rounded-md bg-[#FFFFFF] p-1 border border-[#D8ECEC]">
              <div className="text-[#5A6A7E]">Val (2022)</div>
              <div className="font-semibold text-[#182746]">{forecastingData.partitions.VAL} d</div>
            </div>
            <div className="rounded-md bg-[#FFFFFF] p-1 border border-[#D8ECEC]">
              <div className="text-[#5A6A7E]">Test (23–24)</div>
              <div className="font-semibold text-[#182746]">{forecastingData.partitions.TEST} d</div>
            </div>
          </div>

          {/* Test Partition Benchmark Summary */}
          <div className="rounded-md bg-[#FFFFFF] p-1.5 border border-[#D8ECEC] space-y-1 text-[9px]">
            <div className="flex items-center justify-between font-semibold text-[#182746]">
              <span>Test Set Benchmark (2023–2024, N=611):</span>
              <span className="font-mono text-[8px] text-emerald-700">Linear OLS Best RMSE</span>
            </div>
            <div className="flex items-center justify-between text-[#5A6A7E]">
              <span>Linear OLS (Current Q + RF 3d):</span>
              <span className="font-mono font-medium text-[#182746]">RMSE 413.1 m³/s (R² 0.52)</span>
            </div>
            <div className="flex items-center justify-between text-[#5A6A7E]">
              <span>Persistence Baseline (Q_t):</span>
              <span className="font-mono font-medium text-[#182746]">RMSE 421.8 m³/s (R² 0.50)</span>
            </div>
          </div>

          <div className="rounded-md bg-[#E6F5F5] border border-[#C8E5E5] p-1 text-[8px] text-[#182746] leading-tight">
            <strong>Scope Boundary:</strong> Upstream discharge forecast only. Does NOT predict Delhi stage or flood probability.
          </div>
        </div>
      )}

      {/* Section 4B: Phase 2B Non-Linear Model Benchmark */}
      {modelStatus && (
        <div className="rounded-lg border border-[#D8ECEC] bg-[#F5F9F9] p-2.5 space-y-2">
          <div className="flex items-center justify-between border-b border-[#D8ECEC]/60 pb-1.5">
            <div className="flex items-center gap-1.5 font-semibold text-[#182746] text-[11px]">
              <Activity className="h-3.5 w-3.5 text-[#119E9A]" />
              <span>Experimental Hathnikund Discharge Forecast</span>
            </div>
            <span className="rounded-full bg-[#E6F5F5] border border-[#C8E5E5] px-2 py-0.5 text-[8px] font-mono font-medium text-[#182746]">
              {modelStatus.operational_status}
            </span>
          </div>

          <div className="text-[10px] text-[#5A6A7E]">
            Target: <strong>HKB D/S release</strong> (24h lead time). Model: <strong>{modelStatus.model_identifier}</strong> ({modelStatus.model_type}).
          </div>

          {/* Validation Metrics */}
          <div className="grid grid-cols-2 gap-1.5 text-center text-[9px]">
            <div className="rounded-md bg-[#FFFFFF] p-1 border border-[#D8ECEC]">
              <div className="text-[#5A6A7E]">Validation (2022) MAE</div>
              <div className="font-semibold text-[#182746]">
                {modelStatus.validation_metrics.mae_cumecs} m³/s
              </div>
              <div className="text-[8px] text-emerald-700">
                Skill vs Pers: +{((modelStatus.validation_metrics.skill_score_vs_persistence ?? 0) * 100).toFixed(1)}%
              </div>
            </div>
            <div className="rounded-md bg-[#FFFFFF] p-1 border border-[#D8ECEC]">
              <div className="text-[#5A6A7E]">Validation (2022) RMSE</div>
              <div className="font-semibold text-[#182746]">
                {modelStatus.validation_metrics.rmse_cumecs} m³/s
              </div>
              <div className="text-[8px] text-[#5A6A7E]">
                (Pers: 588.3 m³/s)
              </div>
            </div>
          </div>

          {/* Demonstration Sample Forecast if available */}
          {sampleForecast && (
            <div className="rounded-md bg-[#FFFFFF] p-1.5 border border-[#D8ECEC] space-y-1 text-[9px]">
              <div className="flex items-center justify-between font-semibold text-[#182746]">
                <span>Sample Historical Forecast:</span>
                <span className="font-mono text-[#119E9A]">
                  Q_pred: {sampleForecast.predicted_discharge_cumecs} m³/s
                </span>
              </div>
              {sampleForecast.observation_context && (
                <div className="text-[8px] text-[#5A6A7E] leading-tight">
                  {sampleForecast.observation_context}
                </div>
              )}
            </div>
          )}

          {/* Governance & Disclaimer */}
          <div className="rounded-md bg-[#E6F5F5] border border-[#C8E5E5] p-1.5 text-[8px] text-[#182746] space-y-0.5 leading-tight">
            <div>
              <strong>Operational Status: NOT PROMOTED FOR WARNING.</strong> Non-linear RF improves over persistence during moderate flows (+32.0% Val skill), but tree leaves cap at training maximum (~4,100 m³/s), underpredicting unprecedented surges (e.g. July 2023 peak 8,343 m³/s).
            </div>
            <div>
              <strong>Strict Boundary:</strong> NEVER predicts Delhi Old Railway Bridge stage or flood breach probabilities.
            </div>
          </div>
        </div>
      )}

      {/* Section 5: Downstream Target Gauge Status */}
      <div className="rounded-lg border border-[#D8ECEC] bg-[#F5F9F9] p-2 space-y-1">
        <div className="flex items-center justify-between text-[10px] font-semibold text-[#182746]">
          <span>Downstream Target: Station 028-MDD (Delhi ORB)</span>
          <span className="rounded-full bg-rose-100 text-rose-800 border border-rose-300 px-1.5 py-0.2 text-[8px] uppercase">
            Telemetry Restricted
          </span>
        </div>
        <p className="text-[10px] text-[#5A6A7E] leading-tight">
          Continuous non-flood water levels are restricted under CWC transboundary policies.
          Danger mark is <strong>205.33 m MSL</strong>. Stage is not estimated until authentic CWC telemetry is acquired.
        </p>
      </div>

      {/* Section 6: Model Status Disclaimer */}
      <div className="flex items-start gap-1.5 rounded-lg border border-[#C8E5E5] bg-[#E6F5F5] p-2 text-[10px] text-[#182746]">
        <AlertTriangle className="h-3.5 w-3.5 shrink-0 mt-0.5 text-[#119E9A]" />
        <span className="leading-tight">
          <strong>No Flood Probability Available:</strong> Supervised model training is strictly gated until continuous downstream observations are ingested.
        </span>
      </div>
        </>
      )}
    </div>
  );
};

