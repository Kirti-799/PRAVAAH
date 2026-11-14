import React, { useEffect, useState } from 'react';
import {
  Sliders,
  Play,
  RotateCcw,
  CheckCircle2,
  AlertTriangle,
  Info,
  ShieldAlert,
  MapPin,
} from 'lucide-react';
import type {
  TabletopPresetItem,
  TabletopScenarioResponse,
  TabletopScenarioRequest,
} from '../../types/routing';
import { fetchTabletopPresets, runTabletopScenario } from '../../services/routing';

interface TabletopScenarioWorkstationProps {
  onNavigateToMap?: () => void;
}

export const TabletopScenarioWorkstation: React.FC<TabletopScenarioWorkstationProps> = ({
  onNavigateToMap,
}) => {
  const [presets, setPresets] = useState<TabletopPresetItem[]>([]);
  const [selectedPresetId, setSelectedPresetId] = useState<string>('PRESET_GRADUAL_RISE');


  // Hydrograph state
  const [inflowString, setInflowString] = useState<string>('500, 900, 2200, 4500, 3100, 1800, 950, 500');
  const [scenarioName, setScenarioName] = useState<string>('Gradually Rising Monsoon Wave');
  const [scenarioDesc, setScenarioDesc] = useState<string>('Hypothetical smooth wave propagation test');

  // Routing parameter state
  const [kHours, setKHours] = useState<number>(36.0);
  const [xWeight, setXWeight] = useState<number>(0.20);
  const [dtHours] = useState<number>(24.0);
  const [subreaches] = useState<number>(1);

  // Simulation execution & comparison state
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [simulationResult, setSimulationResult] = useState<TabletopScenarioResponse | null>(null);
  const [comparisonResult, setComparisonResult] = useState<TabletopScenarioResponse | null>(null);
  const [showComparison, setShowComparison] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Compute live coefficients & stability
  const lowerStabilityBound = 2.0 * kHours * xWeight;
  const upperStabilityBound = 2.0 * kHours * (1.0 - xWeight);
  const isStable = dtHours >= lowerStabilityBound - 1e-6 && dtHours <= upperStabilityBound + 1e-6;

  const denom = 2.0 * kHours * (1.0 - xWeight) + dtHours;
  const liveC0 = denom > 0 ? (dtHours - 2.0 * kHours * xWeight) / denom : 0;
  const liveC1 = denom > 0 ? (dtHours + 2.0 * kHours * xWeight) / denom : 0;
  const liveC2 = denom > 0 ? (2.0 * kHours * (1.0 - xWeight) - dtHours) / denom : 0;

  // Load presets on mount
  useEffect(() => {
    let isMounted = true;
    fetchTabletopPresets()
      .then((data) => {
        if (isMounted) {
          setPresets(data.presets);
        }
      })

      .catch((err) => {
        console.error('Failed to load tabletop presets:', err);
      });
    return () => {
      isMounted = false;
    };
  }, []);

  // Handle Preset Selection
  const handlePresetChange = (presetId: string) => {
    setSelectedPresetId(presetId);
    setErrorMessage(null);
    const found = presets.find((p) => p.preset_id === presetId);
    if (found) {
      setInflowString(found.inflow_hydrograph.join(', '));
      setScenarioName(found.name);
      setScenarioDesc(found.description);
      setKHours(found.recommended_K_hours);
      setXWeight(found.recommended_x);
    }
  };

  // Run Simulation Handler
  const handleRunSimulation = async () => {
    setErrorMessage(null);
    const parsedInflows = inflowString
      .split(',')
      .map((s) => parseFloat(s.trim()))
      .filter((n) => !isNaN(n));

    if (parsedInflows.length < 2) {
      setErrorMessage('Please enter at least 2 comma-separated numeric discharge values.');
      return;
    }

    if (parsedInflows.some((n) => n < 0)) {
      setErrorMessage('Physical violation: All discharge values must be non-negative (>= 0 m³/s).');
      return;
    }

    if (!isStable) {
      setErrorMessage(
        `Numerical instability: dt (${dtHours}h) is outside [2Kx (${lowerStabilityBound.toFixed(
          1
        )}h), 2K(1-x) (${upperStabilityBound.toFixed(1)}h)]. Please adjust K or x.`
      );
      return;
    }

    setIsRunning(true);
    try {
      const req: TabletopScenarioRequest = {
        scenario_id: `SCENARIO_${Date.now()}`,
        scenario_name: scenarioName,
        scenario_type: selectedPresetId.startsWith('PRESET_') ? selectedPresetId : 'CUSTOM',
        scenario_description: scenarioDesc,
        inflow_hydrograph: parsedInflows,
        K_hours: kHours,
        x: xWeight,
        dt_hours: dtHours,
        subreaches,
      };

      const primary = await runTabletopScenario(req);
      setSimulationResult(primary);

      // If comparison mode is enabled, run alternative config (K=48, x=0.25 or vice versa)
      if (showComparison) {
        const altK = kHours === 36.0 ? 48.0 : 36.0;
        const altX = kHours === 36.0 ? 0.25 : 0.20;
        const compReq: TabletopScenarioRequest = {
          ...req,
          scenario_id: `SCENARIO_COMP_${Date.now()}`,
          scenario_name: `${scenarioName} (Sensitivity K=${altK}h, x=${altX})`,
          K_hours: altK,
          x: altX,
        };
        const comp = await runTabletopScenario(compReq);
        setComparisonResult(comp);
      } else {
        setComparisonResult(null);
      }
    } catch (err: unknown) {
      if (err instanceof Error) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage('Failed to simulate scenario.');
      }
    } finally {
      setIsRunning(false);
    }
  };

  // Run initial simulation once presets are loaded or on first render
  useEffect(() => {
    handleRunSimulation();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedPresetId]);

  return (
    <div className="rounded-xl border border-[#D8ECEC] bg-[#FFFFFF] p-4 text-xs text-[#2B3A4A] space-y-3 shadow-xs">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#D8ECEC] pb-2">
        <div className="flex items-center gap-1.5 font-semibold text-[#182746]">
          <Sliders className="h-4 w-4 text-[#119E9A]" />
          <span>Tabletop Flood-Wave Scenario Workstation</span>
        </div>
        <span className="rounded-full bg-[#E6F5F5] border border-[#C8E5E5] px-2 py-0.5 text-[9px] font-mono font-medium text-[#182746]">
          Phase 2C-B Validated
        </span>
      </div>

      {/* Prominent Scientific Status Notice */}
      <div className="rounded-lg border border-[#C8E5E5] bg-[#E6F5F5] p-2.5 space-y-1">
        <div className="flex items-center gap-1.5 font-semibold text-[10px] text-[#182746]">
          <ShieldAlert className="h-3.5 w-3.5 text-[#119E9A]" />
          <span>SCIENTIFIC DISCIPLINE & STATUS REGISTER</span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-1 text-[9px] text-[#2B3A4A]">
          <div>
            <strong className="text-[#5A6A7E]">MODE:</strong> TABLETOP SCENARIO SIMULATION
          </div>
          <div>
            <strong className="text-[#5A6A7E]">DATA:</strong> Hypothetical (unless historical replay)
          </div>
          <div>
            <strong className="text-[#5A6A7E]">ROUTING:</strong> Muskingum Reach Storage Model
          </div>
          <div>
            <strong className="text-[#5A6A7E]">CALIBRATION:</strong>{' '}
            <span className="font-semibold text-rose-700">UNCALIBRATED (Assumed Parameters)</span>
          </div>
          <div className="sm:col-span-2">
            <strong className="text-[#5A6A7E]">DELHI FORECAST:</strong>{' '}
            <span className="text-rose-700 font-semibold">
              UNAVAILABLE (Continuous 028-MDD Stage Telemetry Missing)
            </span>
          </div>
        </div>
        <p className="pt-0.5 text-[8.5px] text-[#5A6A7E] leading-tight">
          Simulated downstream discharge represents mathematical wave routing across the 220 km corridor. It does
          not establish water surface levels, flood probabilities, or emergency evacuation directives.
        </p>
      </div>

      {/* Preset Selector */}
      <div className="space-y-1">
        <label className="block text-[10px] font-medium text-[#5A6A7E]">
          Select Tabletop Inflow Stress-Test:
        </label>
        <select
          value={selectedPresetId}
          onChange={(e) => handlePresetChange(e.target.value)}
          className="w-full rounded-lg border border-[#D8ECEC] bg-[#FFFFFF] px-2.5 py-1.5 text-[11px] text-[#2B3A4A] focus:border-[#119E9A] focus:outline-hidden"
        >
          {presets.map((p) => (
            <option key={p.preset_id} value={p.preset_id}>
              {p.name}
            </option>
          ))}
          <option value="CUSTOM">User Custom Hydrograph</option>
        </select>
        {selectedPresetId !== 'CUSTOM' && (
          <div className="rounded-lg bg-[#F5F9F9] p-2 text-[9px] text-[#5A6A7E] leading-tight border border-[#D8ECEC]">
            {presets.find((p) => p.preset_id === selectedPresetId)?.purpose_and_expected_behavior}
          </div>
        )}
      </div>

      {/* Inflow Series Input */}
      <div className="space-y-1">
        <div className="flex items-center justify-between text-[10px]">
          <span className="font-medium text-[#5A6A7E]">Upstream Inflow Sequence (m³/s, dt=24h):</span>
          <span className="text-[9px] text-[#119E9A] font-semibold">
            {inflowString.split(',').filter((s) => s.trim().length > 0).length} steps
          </span>
        </div>
        <input
          type="text"
          value={inflowString}
          onChange={(e) => {
            setInflowString(e.target.value);
            if (selectedPresetId !== 'CUSTOM') setSelectedPresetId('CUSTOM');
          }}
          className="w-full rounded-lg border border-[#D8ECEC] bg-[#FFFFFF] px-2.5 py-1.5 font-mono text-[10px] text-[#2B3A4A] focus:border-[#119E9A] focus:outline-hidden"
          placeholder="e.g. 500, 1200, 4500, 2500, 800"
        />
      </div>

      {/* Parameter Configuration & Stability Inspector */}
      <div className="rounded-lg border border-[#D8ECEC] bg-[#F5F9F9] p-2.5 space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-[10px] font-semibold text-[#182746]">Muskingum Routing Parameters</span>
          <span
            className={`rounded-full px-2 py-0.5 text-[8px] font-mono font-medium ${
              isStable
                ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                : 'bg-rose-100 text-rose-800 border border-rose-300'
            }`}
          >
            {isStable ? 'STABLE (2Kx <= dt <= 2K(1-x))' : 'UNSTABLE'}
          </span>
        </div>

        {/* Quick Config Presets */}
        <div className="grid grid-cols-2 gap-1.5 text-[9px]">
          <button
            type="button"
            onClick={() => {
              setKHours(36.0);
              setXWeight(0.20);
            }}
            className={`rounded-lg border p-1.5 text-left transition-colors ${
              kHours === 36.0 && xWeight === 0.20
                ? 'border-[#119E9A] bg-[#E6F5F5] text-[#182746] font-semibold'
                : 'border-[#D8ECEC] bg-[#FFFFFF] text-[#5A6A7E] hover:bg-[#E6F5F5]/60'
            }`}
          >
            <div>Authoritative Baseline</div>
            <div className="font-mono text-[8px] text-[#119E9A]">K=36.0h, x=0.20 (C0=0.12)</div>
          </button>

          <button
            type="button"
            onClick={() => {
              setKHours(48.0);
              setXWeight(0.25);
            }}
            className={`rounded-lg border p-1.5 text-left transition-colors ${
              kHours === 48.0 && xWeight === 0.25
                ? 'border-[#119E9A] bg-[#E6F5F5] text-[#182746] font-semibold'
                : 'border-[#D8ECEC] bg-[#FFFFFF] text-[#5A6A7E] hover:bg-[#E6F5F5]/60'
            }`}
          >
            <div>Upper-Bound Heuristic</div>
            <div className="font-mono text-[8px] text-[#119E9A]">K=48.0h, x=0.25 (C0=0.00)</div>
          </button>
        </div>

        {/* Slider Controls */}
        <div className="grid grid-cols-2 gap-2 text-[10px]">
          <div>
            <div className="flex justify-between text-[#5A6A7E]">
              <span>Transit Time K:</span>
              <span className="font-mono font-medium text-[#182746]">{kHours} h</span>
            </div>
            <input
              type="range"
              min="12"
              max="72"
              step="2"
              value={kHours}
              onChange={(e) => setKHours(parseFloat(e.target.value))}
              className="w-full accent-[#119E9A]"
            />
          </div>

          <div>
            <div className="flex justify-between text-[#5A6A7E]">
              <span>Weighting Factor x:</span>
              <span className="font-mono font-medium text-[#182746]">{xWeight.toFixed(2)}</span>
            </div>
            <input
              type="range"
              min="0.05"
              max="0.45"
              step="0.01"
              value={xWeight}
              onChange={(e) => setXWeight(parseFloat(e.target.value))}
              className="w-full accent-[#119E9A]"
            />
          </div>
        </div>

        {/* Mathematical Coefficients Feedback */}
        <div className="rounded-lg bg-[#FFFFFF] p-1.5 border border-[#D8ECEC] text-[9px] font-mono text-[#182746] flex items-center justify-between">
          <span>
            C0: <strong>{liveC0.toFixed(4)}</strong>
          </span>
          <span>
            C1: <strong>{liveC1.toFixed(4)}</strong>
          </span>
          <span>
            C2: <strong>{liveC2.toFixed(4)}</strong>
          </span>
          <span>
            Sum: <strong>{(liveC0 + liveC1 + liveC2).toFixed(4)}</strong>
          </span>
        </div>

        {/* Parameter Provenance Rationale */}
        <div className="text-[8.5px] text-[#5A6A7E] leading-tight">
          <strong>Provenance:</strong>{' '}
          {kHours === 36.0 && xWeight === 0.20
            ? 'Phase 1F baseline: 220 km corridor / 6 km/h mean celerity; x=0.20 for natural alluvial channel.'
            : kHours === 48.0 && xWeight === 0.25
            ? 'Phase 2C-A narrative: 48h moderate wave lag heuristic. dt=2Kx forces C0 to exactly zero.'
            : 'Custom sensitivity configuration. Note: altering parameters explores model sensitivity, NOT calibrated river dynamics.'}
        </div>
      </div>

      {/* Comparison Toggle & Run Button */}
      <div className="flex items-center justify-between pt-1">
        <label className="flex items-center gap-1.5 text-[10px] text-[#182746] cursor-pointer font-medium">
          <input
            type="checkbox"
            checked={showComparison}
            onChange={(e) => setShowComparison(e.target.checked)}
            className="accent-[#119E9A]"
          />
          <span>Compare with alternate parameter set</span>
        </label>

        <button
          type="button"
          onClick={handleRunSimulation}
          disabled={isRunning || !isStable}
          className="flex items-center gap-1.5 rounded-lg bg-[#119E9A] hover:bg-[#0E8582] text-white px-3 py-1.5 text-[11px] font-medium transition-colors disabled:opacity-50 shadow-xs"
        >
          {isRunning ? (
            <>
              <RotateCcw className="h-3 w-3 animate-spin" />
              <span>Simulating...</span>
            </>
          ) : (
            <>
              <Play className="h-3 w-3" />
              <span>Run Scenario</span>
            </>
          )}
        </button>
      </div>

      {errorMessage && (
        <div className="rounded-lg border border-rose-300 bg-rose-50 p-2 text-[10px] text-rose-800 flex items-start gap-1.5">
          <AlertTriangle className="h-3.5 w-3.5 shrink-0 mt-0.5 text-rose-600" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Simulation Results Section */}
      {simulationResult && (
        <div className="space-y-2 pt-1 border-t border-[#D8ECEC]">
          <div className="flex items-center justify-between text-[11px] font-semibold text-[#182746]">
            <div className="flex items-center gap-2">
              <span>Simulation Quantitative Metrics:</span>
              {onNavigateToMap && (
                <button
                  type="button"
                  onClick={onNavigateToMap}
                  className="inline-flex items-center gap-1 rounded-md bg-[#182746] px-2 py-0.5 text-[10px] font-medium text-white hover:bg-[#25345B] transition-colors"
                >
                  <MapPin className="h-2.5 w-2.5 text-[#119E9A]" />
                  <span>View Wave on Map</span>
                </button>
              )}
            </div>
            <span className="font-mono text-[9px] text-[#5A6A7E]">
              Hash: {simulationResult.reproducibility_hash}
            </span>
          </div>

          {/* Metrics Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-1.5 text-center text-[9px]">
            <div className="rounded-lg border border-[#D8ECEC] bg-[#F5F9F9] p-1.5">
              <div className="text-[#5A6A7E]">Peak Inflow</div>
              <div className="font-semibold text-xs text-[#182746]">
                {simulationResult.peak_inflow_discharge_cumecs.toLocaleString()} <span className="text-[8px]">m³/s</span>
              </div>
              <div className="text-[8px] text-[#5A6A7E]">{simulationResult.peak_inflow_time_label}</div>
            </div>

            <div className="rounded-lg border border-[#D8ECEC] bg-[#F5F9F9] p-1.5">
              <div className="text-[#5A6A7E]">Simulated Outflow</div>
              <div className="font-semibold text-xs text-[#119E9A]">
                {simulationResult.peak_simulated_outflow_discharge_cumecs.toLocaleString()} <span className="text-[8px]">m³/s</span>
              </div>
              <div className="text-[8px] text-[#5A6A7E]">{simulationResult.peak_simulated_outflow_time_label}</div>
            </div>

            <div className="rounded-lg border border-[#D8ECEC] bg-[#F5F9F9] p-1.5">
              <div className="text-[#5A6A7E]">Peak Attenuation</div>
              <div className="font-semibold text-xs text-emerald-700">
                {simulationResult.peak_attenuation_percent.toFixed(1)}%
              </div>
              <div className="text-[8px] text-[#5A6A7E]">
                -{simulationResult.peak_attenuation_cumecs.toLocaleString()} m³/s
              </div>
            </div>

            <div className="rounded-lg border border-[#D8ECEC] bg-[#F5F9F9] p-1.5">
              <div className="text-[#5A6A7E]">Wave Transit Lag</div>
              <div className="font-semibold text-xs text-[#182746]">
                {simulationResult.apparent_lag_hours} h
              </div>
              <div className="text-[8px] text-[#5A6A7E]">
                ({simulationResult.apparent_lag_steps} time steps)
              </div>
            </div>
          </div>

          {/* Mass Continuity Verification */}
          <div className="rounded-lg bg-[#FFFFFF] border border-[#D8ECEC] p-1.5 flex items-center justify-between text-[9px] text-[#5A6A7E]">
            <span className="flex items-center gap-1 text-emerald-700 font-medium">
              <CheckCircle2 className="h-3 w-3" />
              Mass Conservation Error:
            </span>
            <span className="font-mono font-medium text-[#182746]">
              {simulationResult.mass_conservation_error_percent.toFixed(4)}% (Inflow: {(simulationResult.total_inflow_volume_m3 / 1e6).toFixed(1)}M m³, Outflow: {(simulationResult.total_outflow_volume_m3 / 1e6).toFixed(1)}M m³)
            </span>
          </div>

          {/* Visual Hydrograph Comparison Table/Bars */}
          <div className="rounded-lg border border-[#D8ECEC] bg-[#FFFFFF] p-2.5 space-y-1.5">
            <div className="flex items-center justify-between text-[10px] font-semibold text-[#182746] pb-1 border-b border-[#D8ECEC]">
              <span>Hydrograph Evolution (Inflow vs Simulated Outflow):</span>
              <div className="flex items-center gap-2 text-[9px]">
                <span className="flex items-center gap-1 text-emerald-700">
                  <span className="h-2 w-2 rounded-full bg-emerald-600" /> Inflow
                </span>
                <span className="flex items-center gap-1 text-[#119E9A]">
                  <span className="h-2 w-2 rounded-full bg-[#119E9A]" /> Outflow
                </span>
                {comparisonResult && (
                  <span className="flex items-center gap-1 text-amber-700">
                    <span className="h-2 w-2 rounded-full bg-amber-600" /> Alt (K={comparisonResult.routing_parameters.K_hours}h)
                  </span>
                )}
              </div>
            </div>

            {/* Step-by-step comparative bars */}
            <div className="space-y-1 pt-1">
              {simulationResult.time_series.map((pt, idx) => {
                const maxVal = Math.max(
                  simulationResult.peak_inflow_discharge_cumecs,
                  simulationResult.peak_simulated_outflow_discharge_cumecs,
                  comparisonResult?.peak_simulated_outflow_discharge_cumecs || 0,
                  1.0
                );
                const inPct = (pt.inflow_cumecs / maxVal) * 100;
                const outPct = (pt.simulated_outflow_cumecs / maxVal) * 100;
                const altPt = comparisonResult?.time_series[idx];
                const altPct = altPt ? (altPt.simulated_outflow_cumecs / maxVal) * 100 : 0;

                return (
                  <div key={idx} className="space-y-0.5 text-[9px]">
                    <div className="flex items-center justify-between text-[#5A6A7E]">
                      <span className="font-medium text-[#182746]">{pt.time_label}</span>
                      <span className="font-mono text-[8.5px]">
                        In: {pt.inflow_cumecs.toLocaleString()} | Out: {pt.simulated_outflow_cumecs.toLocaleString()}
                        {altPt && ` | Alt: ${altPt.simulated_outflow_cumecs.toLocaleString()}`} m³/s
                      </span>
                    </div>

                    <div className="h-2 w-full bg-[#F5F9F9] rounded overflow-hidden flex flex-col justify-center gap-0.5 border border-[#D8ECEC]/40">
                      <div
                        className="h-1 bg-emerald-600 rounded-sm transition-all"
                        style={{ width: `${Math.max(2, inPct)}%` }}
                        title={`Inflow: ${pt.inflow_cumecs} m³/s`}
                      />
                      <div
                        className="h-1 bg-[#119E9A] rounded-sm transition-all"
                        style={{ width: `${Math.max(2, outPct)}%` }}
                        title={`Outflow: ${pt.simulated_outflow_cumecs} m³/s`}
                      />
                      {altPt && (
                        <div
                          className="h-0.5 bg-amber-600 rounded-sm transition-all"
                          style={{ width: `${Math.max(2, altPct)}%` }}
                          title={`Alt Outflow: ${altPt.simulated_outflow_cumecs} m³/s`}
                        />
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Scenario Comparison Summary Callout */}
          {comparisonResult && (
            <div className="rounded-lg border border-[#C8E5E5] bg-[#E6F5F5] p-2 space-y-1 text-[9px] text-[#182746]">
              <div className="font-semibold text-[#182746] flex items-center gap-1">
                <Info className="h-3 w-3 text-[#119E9A]" />
                <span>Parameter Sensitivity Analysis (K={simulationResult.routing_parameters.K_hours}h vs K={comparisonResult.routing_parameters.K_hours}h)</span>
              </div>
              <div className="grid grid-cols-2 gap-2 pt-0.5 text-[#2B3A4A]">
                <div>
                  <strong>Primary (K={simulationResult.routing_parameters.K_hours}h, x={simulationResult.routing_parameters.x}):</strong>
                  <div>Peak: {simulationResult.peak_simulated_outflow_discharge_cumecs.toLocaleString()} m³/s (Lag: {simulationResult.apparent_lag_hours}h, Atten: {simulationResult.peak_attenuation_percent.toFixed(1)}%)</div>
                </div>
                <div>
                  <strong>Alternative (K={comparisonResult.routing_parameters.K_hours}h, x={comparisonResult.routing_parameters.x}):</strong>
                  <div>Peak: {comparisonResult.peak_simulated_outflow_discharge_cumecs.toLocaleString()} m³/s (Lag: {comparisonResult.apparent_lag_hours}h, Atten: {comparisonResult.peak_attenuation_percent.toFixed(1)}%)</div>
                </div>
              </div>
              <p className="text-[8px] text-[#5A6A7E] pt-1">
                <strong>Scientific Takeaway:</strong> Increasing travel time K from 36h to 48h increases the apparent peak lag and channel storage dispersion. This is a mathematical demonstration of parameter sensitivity, NOT calibration against observed Delhi flood peaks.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
