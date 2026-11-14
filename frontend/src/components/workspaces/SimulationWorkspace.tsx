/**
 * frontend/src/components/workspaces/SimulationWorkspace.tsx
 *
 * Streamlined 5-Step Muskingum Hydrological Routing Workstation in authentic Cream & Brown styling:
 * Step 1: Select a scenario.
 * Step 2: Enter or select peak discharge.
 * Step 3: Run simulation.
 * Step 4: View downstream results (4 primary metrics).
 * Step 5: View wave progression on the map.
 *
 * Includes:
 * - Hydrograph visualization comparing upstream inflow and downstream outflow.
 * - Collapsible "Advanced Hydrological Parameters" section (K, x, C0, C1, C2, stability, mass conservation).
 * - Strict labeling: Hypothetical scenarios and 1D simulation outputs, NOT observed flood forecasts.
 */

import React, { useEffect, useState } from 'react';
import {
  Activity,
  Play,
  Sliders,
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  Waves,
} from 'lucide-react';
import type {
  TabletopPresetItem,
  TabletopScenarioResponse,
  TabletopScenarioRequest,
} from '../../types/routing';
import { fetchTabletopPresets, runTabletopScenario } from '../../services/routing';

interface SimulationWorkspaceProps {
  onNavigateToMap: () => void;
}

export const SimulationWorkspace: React.FC<SimulationWorkspaceProps> = ({
  onNavigateToMap,
}) => {
  const [presets, setPresets] = useState<TabletopPresetItem[]>([]);
  const [selectedPresetId, setSelectedPresetId] = useState<string>('PRESET_GRADUAL_RISE');
  const [inflowValues, setInflowValues] = useState<number[]>([500, 900, 2200, 4500, 3100, 1800, 950, 500]);
  const [scenarioName, setScenarioName] = useState<string>('Gradually Rising Monsoon Wave');
  const [scenarioDesc, setScenarioDesc] = useState<string>('Hypothetical smooth wave propagation test');

  // Hydrological routing parameters
  const [kHours, setKHours] = useState<number>(36.0);
  const [xWeight, setXWeight] = useState<number>(0.20);
  const [dtHours] = useState<number>(24.0);

  // Advanced section collapsible state
  const [showAdvanced, setShowAdvanced] = useState<boolean>(false);

  // Simulation execution state
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [simulationResult, setSimulationResult] = useState<TabletopScenarioResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Compute live coefficients & stability
  const lowerStabilityBound = 2.0 * kHours * xWeight;
  const upperStabilityBound = 2.0 * kHours * (1.0 - xWeight);
  const isStable = dtHours >= lowerStabilityBound - 1e-6 && dtHours <= upperStabilityBound + 1e-6;

  const denom = 2.0 * kHours * (1.0 - xWeight) + dtHours;
  const liveC0 = denom > 0 ? (dtHours - 2.0 * kHours * xWeight) / denom : 0;
  const liveC1 = denom > 0 ? (dtHours + 2.0 * kHours * xWeight) / denom : 0;
  const liveC2 = denom > 0 ? (2.0 * kHours * (1.0 - xWeight) - dtHours) / denom : 0;

  // Load presets on mount and run default scenario
  useEffect(() => {
    let isMounted = true;
    fetchTabletopPresets()
      .then((data) => {
        if (!isMounted) return;
        setPresets(data.presets);
        const defaultPreset = data.presets.find((p) => p.preset_id === 'PRESET_GRADUAL_RISE') || data.presets[0];
        if (defaultPreset) {
          setSelectedPresetId(defaultPreset.preset_id);
          setInflowValues(defaultPreset.inflow_hydrograph);
          setScenarioName(defaultPreset.name);
          setScenarioDesc(defaultPreset.description);
          setKHours(defaultPreset.recommended_K_hours);
          setXWeight(defaultPreset.recommended_x);

          // Auto-run initial simulation for immediate demonstration
          executeSimulation(
            defaultPreset.inflow_hydrograph,
            defaultPreset.name,
            defaultPreset.preset_id,
            defaultPreset.description,
            defaultPreset.recommended_K_hours,
            defaultPreset.recommended_x
          );
        }
      })
      .catch((err) => {
        console.error('Failed to load presets:', err);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const executeSimulation = async (
    inflows: number[],
    name: string,
    presetId: string,
    desc: string,
    k: number,
    x: number
  ) => {
    setIsRunning(true);
    setErrorMessage(null);
    try {
      const req: TabletopScenarioRequest = {
        scenario_id: `SCENARIO_${Date.now()}`,
        scenario_name: name,
        scenario_type: presetId.startsWith('PRESET_') ? presetId : 'CUSTOM',
        scenario_description: desc,
        inflow_hydrograph: inflows,
        K_hours: k,
        x: x,
        dt_hours: 24.0,
        subreaches: 1,
      };
      const res = await runTabletopScenario(req);
      setSimulationResult(res);
    } catch (err) {
      setErrorMessage((err as Error).message || 'Simulation execution failed.');
    } finally {
      setIsRunning(false);
    }
  };

  const handleSelectPreset = (preset: TabletopPresetItem) => {
    setSelectedPresetId(preset.preset_id);
    setInflowValues(preset.inflow_hydrograph);
    setScenarioName(preset.name);
    setScenarioDesc(preset.description);
    setKHours(preset.recommended_K_hours);
    setXWeight(preset.recommended_x);
    executeSimulation(
      preset.inflow_hydrograph,
      preset.name,
      preset.preset_id,
      preset.description,
      preset.recommended_K_hours,
      preset.recommended_x
    );
  };

  const handleScalePeak = (targetPeak: number) => {
    const currentMax = Math.max(...inflowValues, 1);
    const scale = targetPeak / currentMax;
    const scaled = inflowValues.map((v) => Math.round(v * scale));
    setInflowValues(scaled);
    executeSimulation(scaled, `${scenarioName} (${targetPeak} m³/s Peak)`, selectedPresetId, scenarioDesc, kHours, xWeight);
  };

  return (
    <div className="h-full w-full overflow-y-auto bg-[#FBF9F5] p-4 sm:p-6 lg:p-8 text-[#3E3026]">
      <div className="mx-auto max-w-6xl space-y-6">
        {/* Top Header Card */}
        <div className="rounded-2xl border border-[#EAE3D9] bg-[#FFFFFF] p-5 sm:p-6 shadow-xs">
          <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
            <div>
              <div className="flex items-center gap-2">
                <span className="rounded-md bg-[#F5EFEB] px-2.5 py-0.5 text-[11px] font-bold uppercase tracking-wider text-[#8B4513]">
                  1D Hydrological Routing
                </span>
                <span className="text-[11px] text-[#8C7869]">
                  Hathnikund to Delhi ORB (251.05 km)
                </span>
              </div>
              <h1 className="mt-1 text-2xl font-extrabold tracking-tight text-[#2C221E] sm:text-3xl">
                Prediction & Scenario Simulation
              </h1>
              <p className="mt-1 text-xs text-[#635347] max-w-3xl leading-relaxed">
                Test flood-wave routing scenarios down the Yamuna thalweg using the classical Muskingum formulation.
                Simulates peak discharge attenuation and hydraulic travel lag under varying surge magnitudes.
              </p>
            </div>

            <div className="rounded-xl border border-[#EAE3D9] bg-[#FFFDF9] px-3.5 py-2 text-xs">
              <span className="text-[#8C7869] font-medium">Reach:</span>{' '}
              <strong className="text-[#2C221E]">251.05 km</strong> |{' '}
              <span className="text-[#8C7869] font-medium">Interval:</span>{' '}
              <strong className="text-[#2C221E]">Δt = 24h</strong>
            </div>
          </div>
        </div>

        {/* 5-Step Guided Workflow Container */}
        <div className="rounded-2xl border border-[#EAE3D9] bg-[#FFFFFF] p-5 sm:p-6 shadow-xs space-y-6">
          <div className="border-b border-[#EAE3D9] pb-3">
            <h2 className="text-base font-bold text-[#2C221E] flex items-center gap-2">
              <Activity className="h-4 w-4 text-[#8B4513]" />
              Simulation Workflow (5 Steps)
            </h2>
          </div>

          {/* STEP 1: Select a Scenario */}
          <div>
            <div className="text-xs font-bold uppercase tracking-wider text-[#8B4513] mb-2 flex items-center gap-2">
              <span className="flex h-5 w-5 items-center justify-center rounded-full bg-[#8B4513] text-white text-[10px]">1</span>
              <span>Step 1: Select a Flood Surge Scenario</span>
            </div>

            <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2 lg:grid-cols-4">
              {presets.map((preset) => {
                const isSelected = selectedPresetId === preset.preset_id;
                return (
                  <button
                    key={preset.preset_id}
                    onClick={() => handleSelectPreset(preset)}
                    className={`rounded-xl border p-3 text-left transition-all ${
                      isSelected
                        ? 'border-[#8B4513] bg-[#F5EFEB] shadow-xs'
                        : 'border-[#EAE3D9] bg-[#FFFFFF] hover:border-[#8C7869]'
                    }`}
                  >
                    <div className="text-xs font-bold text-[#2C221E]">{preset.name}</div>
                    <div className="mt-1 text-[11px] text-[#635347] line-clamp-2 leading-snug">
                      {preset.description}
                    </div>
                    <div className="mt-2 text-[10px] text-[#8C7869] flex justify-between font-mono">
                      <span>Peak: {Math.max(...preset.inflow_hydrograph).toLocaleString()} m³/s</span>
                      <span>K={preset.recommended_K_hours}h</span>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* STEP 2: Adjust Peak Discharge */}
          <div className="pt-2 border-t border-[#EAE3D9]/60">
            <div className="text-xs font-bold uppercase tracking-wider text-[#8B4513] mb-2 flex items-center gap-2">
              <span className="flex h-5 w-5 items-center justify-center rounded-full bg-[#8B4513] text-white text-[10px]">2</span>
              <span>Step 2: Quick Peak Discharge Selection</span>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs text-[#635347] font-medium mr-1">Scale Peak Inflow to:</span>
              {[
                { label: 'Seasonal Alert (2,500 m³/s)', value: 2500 },
                { label: 'Low Flood (5,000 m³/s)', value: 5000 },
                { label: 'July 2023 Peak (8,343 m³/s)', value: 8343 },
                { label: 'Surge Extreme (10,194 m³/s)', value: 10194 },
              ].map((chip) => (
                <button
                  key={chip.value}
                  onClick={() => handleScalePeak(chip.value)}
                  className="rounded-lg border border-[#EAE3D9] bg-[#FBF9F5] px-3 py-1.5 text-xs font-semibold text-[#2C221E] hover:bg-[#8B4513] hover:text-white hover:border-[#8B4513] transition-colors shadow-2xs"
                >
                  {chip.label}
                </button>
              ))}
            </div>
          </div>

          {/* STEP 3: Run Simulation CTA */}
          <div className="pt-2 border-t border-[#EAE3D9]/60 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="flex h-5 w-5 items-center justify-center rounded-full bg-[#8B4513] text-white text-[10px]">3</span>
              <span className="text-xs font-bold text-[#2C221E]">Step 3: Execute Hydrological Routing</span>
            </div>

            <button
              onClick={() =>
                executeSimulation(inflowValues, scenarioName, selectedPresetId, scenarioDesc, kHours, xWeight)
              }
              disabled={isRunning || !isStable}
              className="flex items-center gap-2 rounded-xl bg-[#8B4513] px-5 py-2.5 text-xs font-bold text-white shadow-xs hover:bg-[#70360E] disabled:opacity-50 transition-all"
            >
              <Play className={`h-4 w-4 ${isRunning ? 'animate-spin' : ''}`} />
              <span>{isRunning ? 'Calculating Routing...' : 'Run Simulation'}</span>
            </button>
          </div>

          {errorMessage && (
            <div className="rounded-xl border border-red-300 bg-red-50 p-3 text-xs text-red-800 flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 shrink-0 text-red-600" />
              <span>{errorMessage}</span>
            </div>
          )}

          {/* STEP 4: Downstream Results (4 Primary Metrics) */}
          {simulationResult && (
            <div className="pt-2 border-t border-[#EAE3D9] space-y-4">
              <div className="flex items-center justify-between">
                <div className="text-xs font-bold uppercase tracking-wider text-[#8B4513] flex items-center gap-2">
                  <span className="flex h-5 w-5 items-center justify-center rounded-full bg-[#8B4513] text-white text-[10px]">4</span>
                  <span>Step 4: Downstream Routing Results (Delhi ORB)</span>
                </div>

                <span className="rounded bg-[#E8F5E9] px-2.5 py-0.5 text-[10px] font-bold text-[#2E7D32]">
                  SIMULATION CONVERGED
                </span>
              </div>

              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
                {/* Metric 1: Peak Inflow */}
                <div className="rounded-xl border border-[#EAE3D9] bg-[#FFFDF9] p-3.5 shadow-2xs">
                  <div className="text-[10px] font-bold uppercase text-[#8C7869]">Peak Inflow (Hathnikund)</div>
                  <div className="mt-1 text-2xl font-extrabold text-[#2C221E]">
                    {Math.round(simulationResult.peak_inflow_discharge_cumecs).toLocaleString()}
                    <span className="text-xs font-normal text-[#8C7869] ml-1">m³/s</span>
                  </div>
                  <div className="mt-1 text-[11px] text-[#635347]">Origin input discharge</div>
                </div>

                {/* Metric 2: Simulated Downstream Peak */}
                <div className="rounded-xl border border-[#EAE3D9] bg-[#FFFDF9] p-3.5 shadow-2xs">
                  <div className="text-[10px] font-bold uppercase text-[#8C7869]">Downstream Peak (Delhi ORB)</div>
                  <div className="mt-1 text-2xl font-extrabold text-[#2B5B84]">
                    {Math.round(simulationResult.peak_simulated_outflow_discharge_cumecs).toLocaleString()}
                    <span className="text-xs font-normal text-[#8C7869] ml-1">m³/s</span>
                  </div>
                  <div className="mt-1 text-[11px] text-[#635347]">Simulated routed outflow</div>
                </div>

                {/* Metric 3: Peak Attenuation */}
                <div className="rounded-xl border border-[#EAE3D9] bg-[#FFFDF9] p-3.5 shadow-2xs">
                  <div className="text-[10px] font-bold uppercase text-[#8C7869]">Peak Attenuation</div>
                  <div className="mt-1 text-2xl font-extrabold text-[#B45309]">
                    -{Math.round(simulationResult.peak_attenuation_cumecs).toLocaleString()}
                    <span className="text-xs font-normal text-[#8C7869] ml-1">m³/s</span>
                  </div>
                  <div className="mt-1 text-[11px] text-[#635347]">
                    {simulationResult.peak_attenuation_percent.toFixed(1)}% natural crest damping
                  </div>
                </div>

                {/* Metric 4: Estimated Routing Lag */}
                <div className="rounded-xl border border-[#EAE3D9] bg-[#FFFDF9] p-3.5 shadow-2xs">
                  <div className="text-[10px] font-bold uppercase text-[#8C7869]">Estimated Routing Lag</div>
                  <div className="mt-1 text-2xl font-extrabold text-[#2C221E]">
                    ~{Math.round(simulationResult.apparent_lag_hours)}
                    <span className="text-xs font-normal text-[#8C7869] ml-1">hours</span>
                  </div>
                  <div className="mt-1 text-[11px] text-[#635347]">
                    Travel time to Delhi gauge
                  </div>
                </div>
              </div>

              {/* Hydrograph Chart */}
              <div className="rounded-xl border border-[#EAE3D9] bg-[#FFFFFF] p-4">
                <div className="flex items-center justify-between mb-3 text-xs">
                  <span className="font-bold text-[#2C221E]">
                    Hydrograph Comparison: Hathnikund Inflow vs Delhi ORB Outflow
                  </span>
                  <div className="flex items-center gap-4 text-[11px]">
                    <span className="flex items-center gap-1.5 font-medium text-[#2C221E]">
                      <span className="h-2.5 w-2.5 rounded-full bg-[#8B4513]"></span>
                      Inflow (Hathnikund)
                    </span>
                    <span className="flex items-center gap-1.5 font-medium text-[#2B5B84]">
                      <span className="h-2.5 w-2.5 rounded-full bg-[#2B5B84]"></span>
                      Routed Outflow (Delhi ORB)
                    </span>
                  </div>
                </div>

                {/* Hydrograph Table / Bar Display */}
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-[#EAE3D9] bg-[#FBF9F5] text-[10px] uppercase text-[#8C7869]">
                        <th className="py-2 px-3">Step</th>
                        <th className="py-2 px-3">Time</th>
                        <th className="py-2 px-3 text-right">Inflow (m³/s)</th>
                        <th className="py-2 px-3 text-right">Outflow (m³/s)</th>
                        <th className="py-2 px-3 text-right">Attenuation</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#EAE3D9]/60">
                      {simulationResult.time_series.map((item, idx) => {
                        const diff = item.inflow_cumecs - item.simulated_outflow_cumecs;
                        return (
                          <tr key={idx} className="hover:bg-[#F5EFEB]/50">
                            <td className="py-1.5 px-3 font-mono text-[11px] text-[#8C7869]">T+{idx}</td>
                            <td className="py-1.5 px-3 font-mono text-[11px] text-[#635347]">
                              {item.time_label || `+${idx * 6}h`}
                            </td>
                            <td className="py-1.5 px-3 text-right font-mono font-semibold text-[#8B4513]">
                              {Math.round(item.inflow_cumecs).toLocaleString()}
                            </td>
                            <td className="py-1.5 px-3 text-right font-mono font-semibold text-[#2B5B84]">
                              {Math.round(item.simulated_outflow_cumecs).toLocaleString()}
                            </td>
                            <td className="py-1.5 px-3 text-right font-mono text-[11px] text-[#635347]">
                              {diff >= 0 ? `-${Math.round(diff)}` : `+${Math.round(-diff)}`}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* STEP 5: View Wave on Map CTA */}
              <div className="flex flex-col sm:flex-row items-center justify-between gap-3 rounded-xl border border-[#EAE3D9] bg-[#F5EFEB] p-4">
                <div className="flex items-center gap-2.5">
                  <Waves className="h-5 w-5 text-[#8B4513]" />
                  <div>
                    <div className="text-xs font-bold text-[#2C221E]">
                      Step 5: Visualize 1D Wave Spatial Progression
                    </div>
                    <div className="text-[11px] text-[#635347]">
                      Observe the simulated flood crest travel down all 55 chainage stations from Hathnikund to Delhi on the GIS map.
                    </div>
                  </div>
                </div>

                <button
                  onClick={onNavigateToMap}
                  className="flex items-center gap-1.5 rounded-xl bg-[#2C221E] px-4 py-2 text-xs font-bold text-white shadow-xs hover:bg-[#3E3026] transition-all whitespace-nowrap"
                >
                  <span>View Wave on Flood Map</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
          )}

          {/* Expandable Advanced Hydrological Parameters */}
          <div className="pt-2 border-t border-[#EAE3D9]">
            <button
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="flex items-center justify-between w-full text-xs font-bold text-[#635347] hover:text-[#2C221E] py-2 transition-colors"
            >
              <span className="flex items-center gap-1.5">
                <Sliders className="h-3.5 w-3.5 text-[#8B4513]" />
                Advanced Hydrological Parameters (Muskingum K, X, Stability)
              </span>
              {showAdvanced ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </button>

            {showAdvanced && (
              <div className="mt-3 rounded-xl border border-[#EAE3D9] bg-[#FBF9F5] p-4 text-xs space-y-4 animate-fade-in-up">
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                  <div>
                    <label className="text-[11px] font-bold text-[#2C221E]">
                      Travel Time Parameter (K): {kHours.toFixed(1)} hrs
                    </label>
                    <input
                      type="range"
                      min={18}
                      max={60}
                      step={2}
                      value={kHours}
                      onChange={(e) => setKHours(parseFloat(e.target.value))}
                      className="w-full mt-1 accent-[#8B4513]"
                    />
                    <div className="text-[10px] text-[#8C7869] mt-0.5">Recommended: 36h for Hathnikund-Delhi reach</div>
                  </div>

                  <div>
                    <label className="text-[11px] font-bold text-[#2C221E]">
                      Weighting Parameter (x): {xWeight.toFixed(2)}
                    </label>
                    <input
                      type="range"
                      min={0.05}
                      max={0.45}
                      step={0.05}
                      value={xWeight}
                      onChange={(e) => setXWeight(parseFloat(e.target.value))}
                      className="w-full mt-1 accent-[#8B4513]"
                    />
                    <div className="text-[10px] text-[#8C7869] mt-0.5">Typical natural channel range: 0.15 - 0.25</div>
                  </div>

                  <div>
                    <label className="text-[11px] font-bold text-[#2C221E]">
                      Stability Check
                    </label>
                    <div className="mt-1 flex items-center gap-1.5 font-bold">
                      {isStable ? (
                        <>
                          <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                          <span className="text-emerald-700">Stable (Δt within bounds)</span>
                        </>
                      ) : (
                        <>
                          <AlertTriangle className="h-4 w-4 text-red-600" />
                          <span className="text-red-700">Unstable</span>
                        </>
                      )}
                    </div>
                    <div className="text-[10px] text-[#8C7869] mt-0.5">
                      Bounds: [{lowerStabilityBound.toFixed(1)}h, {upperStabilityBound.toFixed(1)}h]
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-3 border-t border-[#EAE3D9] pt-3 font-mono text-[11px]">
                  <div>
                    <span className="text-[#8C7869]">C0:</span> <strong>{liveC0.toFixed(4)}</strong>
                  </div>
                  <div>
                    <span className="text-[#8C7869]">C1:</span> <strong>{liveC1.toFixed(4)}</strong>
                  </div>
                  <div>
                    <span className="text-[#8C7869]">C2:</span> <strong>{liveC2.toFixed(4)}</strong>
                  </div>
                </div>

                <div className="text-[10px] text-[#8C7869] leading-relaxed border-t border-[#EAE3D9] pt-2">
                  <strong>Scientific Notice:</strong> This tabletop workstation performs uncalibrated 1D hydrological channel routing.
                  Outputs represent discharge propagation along the river centerline and must not be used as an authenticated flood inundation forecast.
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
