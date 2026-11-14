import React, { useEffect, useState } from 'react';
import {
  ShieldAlert,
  AlertTriangle,
  Building2,
  Users,
  Navigation,
  CheckCircle2,
  Info,
  Waves,
  RefreshCw,
  MapPin,
} from 'lucide-react';
import type { DisasterRiskSummaryResponse } from '../../types/disaster';
import { fetchDisasterRiskSummary } from '../../services/disaster';

interface DisasterIntelligencePanelProps {
  onNavigateToMap?: () => void;
}

export const DisasterIntelligencePanel: React.FC<DisasterIntelligencePanelProps> = ({
  onNavigateToMap,
}) => {
  const [data, setData] = useState<DisasterRiskSummaryResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [inflowTestValue, setInflowTestValue] = useState<number>(650.0);

  const loadData = async (inflow?: number) => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetchDisasterRiskSummary(inflow);
      setData(res);
    } catch (err) {
      setError((err as Error).message || 'Failed to load disaster risk summary.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData(inflowTestValue);
  }, []);

  const handleSimulateDischarge = (val: number) => {
    setInflowTestValue(val);
    loadData(val);
  };

  const getAlertBadge = (level: string) => {
    switch (level) {
      case 'SEVERE':
        return {
          bg: 'bg-red-100 text-red-800 border-red-300',
          dot: 'bg-red-600',
          label: 'CRITICAL SEVERE FLOOD SURGE',
        };
      case 'WARNING':
        return {
          bg: 'bg-amber-100 text-amber-900 border-amber-300',
          dot: 'bg-amber-600',
          label: 'FLOOD WARNING STAGE (DANGER BREACHED)',
        };
      case 'ALERT':
        return {
          bg: 'bg-yellow-100 text-yellow-800 border-yellow-300',
          dot: 'bg-yellow-600',
          label: 'ALERT STAGE (APPROACHING WARNING)',
        };
      default:
        return {
          bg: 'bg-emerald-100 text-emerald-800 border-emerald-300',
          dot: 'bg-emerald-600',
          label: 'NORMAL CHANNEL CAPACITY (SAFE)',
        };
    }
  };

  const badge = data ? getAlertBadge(data.overall_alert_level) : getAlertBadge('NORMAL');

  return (
    <div className="space-y-6 text-[#2B3A4A]">
      {/* Top Banner */}
      <div className="rounded-xl border border-[#D8ECEC] bg-[#FFFFFF] p-5 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-semibold ${badge.bg}`}>
                <span className={`h-2 w-2 rounded-full ${badge.dot}`} />
                {badge.label}
              </span>
              <span className="text-xs text-[#5A6A7E]">
                Updated: {data ? new Date(data.timestamp_iso).toLocaleTimeString() : '...'}
              </span>
            </div>
            <h1 className="mt-2 text-xl font-bold tracking-tight text-[#182746] sm:text-2xl">
              Disaster Risk & Humanitarian Response Intelligence
            </h1>
            <p className="mt-1 text-xs text-[#5A6A7E]">
              Operational flood stage classification, authenticated CWC thresholds, municipal relief shelters, and evacuation corridors along the Yamuna corridor.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => loadData(inflowTestValue)}
              disabled={isLoading}
              className="inline-flex items-center gap-1.5 rounded-lg border border-[#D8ECEC] bg-[#E6F5F5] px-3 py-2 text-xs font-medium text-[#182746] hover:bg-[#D8ECEC] transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
            {onNavigateToMap && (
              <button
                onClick={onNavigateToMap}
                className="inline-flex items-center gap-1.5 rounded-lg bg-[#119E9A] px-3 py-2 text-xs font-medium text-white hover:bg-[#0E8582] transition-colors shadow-sm"
              >
                <MapPin className="h-3.5 w-3.5" />
                View on Map
              </button>
            )}
          </div>
        </div>

        {/* Quick Simulator Discharge Selector */}
        <div className="mt-4 border-t border-[#D8ECEC] pt-3 flex flex-wrap items-center gap-2 text-xs">
          <span className="font-semibold text-[#182746]">Simulate Hathnikund Discharge:</span>
          <button
            onClick={() => handleSimulateDischarge(650.0)}
            className={`rounded px-2.5 py-1 font-mono transition-colors ${
              inflowTestValue === 650.0 ? 'bg-[#119E9A] text-white' : 'bg-[#E6F5F5] text-[#182746] hover:bg-[#D8ECEC]'
            }`}
          >
            650 m³/s (Baseline)
          </button>
          <button
            onClick={() => handleSimulateDischarge(2500.0)}
            className={`rounded px-2.5 py-1 font-mono transition-colors ${
              inflowTestValue === 2500.0 ? 'bg-yellow-700 text-white' : 'bg-[#E6F5F5] text-[#182746] hover:bg-[#D8ECEC]'
            }`}
          >
            2,500 m³/s (~88k cfs, Low Flood)
          </button>
          <button
            onClick={() => handleSimulateDischarge(5000.0)}
            className={`rounded px-2.5 py-1 font-mono transition-colors ${
              inflowTestValue === 5000.0 ? 'bg-amber-700 text-white' : 'bg-[#E6F5F5] text-[#182746] hover:bg-[#D8ECEC]'
            }`}
          >
            5,000 m³/s (~176k cfs, High Flood)
          </button>
          <button
            onClick={() => handleSimulateDischarge(8342.9)}
            className={`rounded px-2.5 py-1 font-mono transition-colors ${
              inflowTestValue === 8342.9 ? 'bg-red-700 text-white' : 'bg-[#E6F5F5] text-[#182746] hover:bg-[#D8ECEC]'
            }`}
          >
            8,342.9 m³/s (July 2023 Daily Peak)
          </button>
          <button
            onClick={() => handleSimulateDischarge(10194.0)}
            className={`rounded px-2.5 py-1 font-mono transition-colors ${
              inflowTestValue === 10194.0 ? 'bg-purple-800 text-white' : 'bg-[#E6F5F5] text-[#182746] hover:bg-[#D8ECEC]'
            }`}
          >
            10,194 m³/s (July 2023 Instantaneous Crest)
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-xl border border-red-300 bg-red-50 p-4 text-xs text-red-800 flex items-start gap-2">
          <AlertTriangle className="h-4 w-4 shrink-0 text-red-600 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* Main 2-Column Gauge & Inflow Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* CWC Gauge Card */}
        <div className="rounded-xl border border-[#D8ECEC] bg-[#FFFFFF] p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-[#D8ECEC] pb-3">
            <div className="flex items-center gap-2">
              <Waves className="h-4 w-4 text-[#119E9A]" />
              <h2 className="text-sm font-bold text-[#182746]">
                CWC Downstream Flood Stage
              </h2>
            </div>
            <span className="text-[11px] font-mono text-[#5A6A7E]">
              Station: 028-MDD (Delhi ORB)
            </span>
          </div>

          <div className="grid grid-cols-3 gap-2 text-center text-xs">
            <div className="rounded-lg bg-[#F5F9F9] p-2 border border-[#D8ECEC]">
              <div className="text-[11px] text-[#5A6A7E]">Warning Mark</div>
              <div className="mt-1 font-mono text-sm font-bold text-amber-700">204.50 m</div>
              <div className="text-[10px] text-[#119E9A]">MSL</div>
            </div>
            <div className="rounded-lg bg-[#F5F9F9] p-2 border border-[#D8ECEC]">
              <div className="text-[11px] text-[#5A6A7E]">Danger Mark</div>
              <div className="mt-1 font-mono text-sm font-bold text-red-700">205.33 m</div>
              <div className="text-[10px] text-[#119E9A]">MSL</div>
            </div>
            <div className="rounded-lg bg-[#F5F9F9] p-2 border border-[#D8ECEC]">
              <div className="text-[11px] text-[#5A6A7E]">All-Time HFL (2023)</div>
              <div className="mt-1 font-mono text-sm font-bold text-purple-800">208.66 m</div>
              <div className="text-[10px] text-[#119E9A]">13-Jul-2023</div>
            </div>
          </div>

          {/* Reference Level Visualizer */}
          {data && (
            <div className="space-y-2 rounded-lg bg-[#F5F9F9] p-3 border border-[#D8ECEC]">
              <div className="flex justify-between text-xs font-medium">
                <span className="text-[#182746]">Projected / Reference Water Level:</span>
                <span className="font-mono font-bold text-[#182746]">
                  {data.cwc_gauge.current_reference_level_msl.toFixed(2)} m MSL
                </span>
              </div>
              <div className="relative h-3 w-full rounded-full bg-[#D8ECEC] overflow-hidden">
                <div
                  className={`h-full transition-all duration-500 ${
                    data.cwc_gauge.current_reference_level_msl >= 205.33
                      ? 'bg-red-600'
                      : data.cwc_gauge.current_reference_level_msl >= 204.50
                      ? 'bg-amber-500'
                      : 'bg-emerald-600'
                  }`}
                  style={{
                    width: `${Math.min(
                      100,
                      Math.max(
                        5,
                        ((data.cwc_gauge.current_reference_level_msl - 201.25) / (208.66 - 201.25)) * 100
                      )
                    )}%`,
                  }}
                />
              </div>
              <div className="flex justify-between text-[10px] text-[#5A6A7E] font-mono">
                <span>Bed: 201.25 m</span>
                <span className="text-amber-700">Warn: 204.50 m</span>
                <span className="text-red-700">Dang: 205.33 m</span>
                <span className="text-purple-800">HFL: 208.66 m</span>
              </div>
            </div>
          )}
        </div>

        {/* Hathnikund Inflow Thresholds Card */}
        <div className="rounded-xl border border-[#D8ECEC] bg-[#FFFFFF] p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-[#D8ECEC] pb-3">
            <div className="flex items-center gap-2">
              <ShieldAlert className="h-4 w-4 text-[#119E9A]" />
              <h2 className="text-sm font-bold text-[#182746]">
                Upstream Release Thresholds (Hathnikund)
              </h2>
            </div>
            <span className="text-[11px] font-mono text-[#5A6A7E]">
              Chainage: 0.00 km (Yamunanagar)
            </span>
          </div>

          <div className="space-y-2 text-xs">
            <div className="flex items-center justify-between p-2 rounded bg-[#F5F9F9] border border-[#D8ECEC]">
              <span className="font-medium text-[#2B3A4A]">Normal Channel Flow:</span>
              <span className="font-mono text-[#5A6A7E]">&lt; 70,000 cfs (&lt; 1,982 m³/s)</span>
            </div>
            <div className="flex items-center justify-between p-2 rounded bg-[#F5F9F9] border border-[#D8ECEC]">
              <span className="font-medium text-yellow-800">Low Flood Category:</span>
              <span className="font-mono text-[#5A6A7E]">70,000 – 150,000 cfs (1,982 – 4,248 m³/s)</span>
            </div>
            <div className="flex items-center justify-between p-2 rounded bg-[#F5F9F9] border border-[#D8ECEC]">
              <span className="font-medium text-amber-800">High Flood Category:</span>
              <span className="font-mono text-[#5A6A7E]">150,000 – 250,000 cfs (4,248 – 7,079 m³/s)</span>
            </div>
            <div className="flex items-center justify-between p-2 rounded bg-[#F5F9F9] border border-[#D8ECEC]">
              <span className="font-medium text-red-800">Extreme Surge Category:</span>
              <span className="font-mono text-[#5A6A7E]">&gt; 250,000 cfs (&gt; 7,079 m³/s)</span>
            </div>
          </div>

          {data && (
            <div className="rounded-lg bg-[#E6F5F5] border border-[#C8E5E5] p-3 text-xs text-[#182746]">
              <div className="flex items-center justify-between">
                <span>Current Simulated Discharge:</span>
                <span className="font-mono font-bold text-[#182746]">
                  {data.discharge_status.current_inflow_cumecs.toLocaleString()} m³/s (
                  {Math.round(data.discharge_status.current_inflow_cumecs / 0.0283168).toLocaleString()} cfs)
                </span>
              </div>
              <div className="mt-1 text-[11px] text-[#5A6A7E]">
                Estimated travel time to Delhi: <strong>36 to 48 hours</strong> (Muskingum K=36h, x=0.20).
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Active Advisories Card */}
      {data && data.active_advisories.length > 0 && (
        <div className="rounded-xl border border-[#D8ECEC] bg-[#FFFFFF] p-5 shadow-sm space-y-3">
          <div className="flex items-center gap-2 border-b border-[#D8ECEC] pb-2 text-sm font-bold text-[#182746]">
            <AlertTriangle className="h-4 w-4 text-amber-600" />
            <span>Active Flood Advisories & Standard Operating Procedures (SOPs)</span>
          </div>
          <div className="space-y-2">
            {data.active_advisories.map((adv, idx) => (
              <div
                key={idx}
                className="flex items-start gap-2.5 rounded-lg bg-[#F5F9F9] p-2.5 text-xs text-[#2B3A4A] border border-[#D8ECEC]"
              >
                <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-[#119E9A] mt-0.5" />
                <span>{adv}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Disclaimer / Unvalidated Status Notice */}
      <div className="rounded-xl border border-amber-300 bg-amber-50 p-4 text-xs text-amber-950 flex items-start gap-2.5">
        <Info className="h-4 w-4 shrink-0 text-amber-700 mt-0.5" />
        <div className="space-y-1">
          <div className="font-bold text-amber-900">
            SCIENTIFIC STATUS NOTICE — ILLUSTRATIVE PLANNING PROTOTYPE ONLY
          </div>
          <div className="text-[11px] leading-relaxed text-amber-900">
            The five relief shelters, four evacuation corridors, and demographic exposure figures shown below are 
            <strong> illustrative planning prototypes</strong> derived from public municipal flood guidelines (DDMA/MCD). 
            Corridor geometries and elevations have <strong>NOT been ground-surveyed or hydraulically validated for submergence safety</strong>. 
            This information must NOT be treated as operational life-safety routing without formal municipal certification.
          </div>
        </div>
      </div>

      {/* Illustrative Shelters & Evacuation Routes Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Designated Shelters (2 cols) */}
        <div className="lg:col-span-2 rounded-xl border border-[#D8ECEC] bg-[#FFFFFF] p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-[#D8ECEC] pb-3">
            <div className="flex items-center gap-2">
              <Building2 className="h-4 w-4 text-[#119E9A]" />
              <h2 className="text-sm font-bold text-[#182746]">
                Illustrative Flood Relief Shelters (Planning Prototype)
              </h2>
            </div>
            <span className="text-xs text-[#5A6A7E]">
              Planning Capacity: <strong>{data?.total_shelter_capacity.toLocaleString() ?? '4,950'}</strong> persons
            </span>
          </div>

          <div className="space-y-3">
            {[
              {
                id: 'SHELTER_PALLA_01',
                name: 'Palla Community Disaster Relief Centre',
                zone: 'North Delhi (Palla - Alipur)',
                capacity: 600,
                elevation: 212.5,
                distance: 850,
                agency: 'DM North Delhi / DDMA',
                facilities: ['Water Tanker', 'First Aid Post', 'Sanitation', 'Genset'],
              },
              {
                id: 'SHELTER_WAZIRABAD_02',
                name: 'Wazirabad Water Works Relief Station',
                zone: 'North-East Delhi (Wazirabad)',
                capacity: 1200,
                elevation: 208.0,
                distance: 450,
                agency: 'Delhi Jal Board & DDMA Central',
                facilities: ['Medical Station', 'Boat Launch Access', 'Community Kitchen'],
              },
              {
                id: 'SHELTER_KASHMERE_03',
                name: 'ISBT Kashmere Gate Municipal Relief School',
                zone: 'Central Delhi (Civil Lines / Yamuna Bazar)',
                capacity: 1500,
                elevation: 209.5,
                distance: 700,
                agency: 'MCD & Civil Defence',
                facilities: ['Bedding Dormitories', 'NDRF Sub-Post', 'Ambulance Unit'],
              },
              {
                id: 'SHELTER_MAYUR_04',
                name: 'Mayur Vihar Phase-1 Flood Relief Camp',
                zone: 'East Delhi (Mayur Vihar Khadar)',
                capacity: 900,
                elevation: 207.2,
                distance: 600,
                agency: 'DM East Delhi',
                facilities: ['Cattle Holding Area', 'Clean Water', 'Mobile Health Van'],
              },
              {
                id: 'SHELTER_OKHLA_05',
                name: 'Okhla Barrage Relief Centre',
                zone: 'South-East Delhi (Jamia / Okhla)',
                capacity: 750,
                elevation: 205.8,
                distance: 500,
                agency: 'UP Irrigation & Delhi Police',
                facilities: ['Community Hall', 'Stockpile', 'First Aid Clinic'],
              },
            ].map((s) => (
              <div
                key={s.id}
                className="rounded-lg border border-[#D8ECEC] bg-[#F5F9F9] p-3 text-xs space-y-2"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                  <div className="font-semibold text-[#182746] flex items-center gap-1.5">
                    <Building2 className="h-3.5 w-3.5 text-[#119E9A]" />
                    {s.name}
                  </div>
                  <span className="text-[11px] font-mono text-[#5A6A7E]">
                    Zone: {s.zone}
                  </span>
                </div>

                <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] text-[#5A6A7E]">
                  <span>Capacity: <strong>{s.capacity} persons</strong></span>
                  <span>Elevation: <strong>{s.elevation} m MSL</strong></span>
                  <span>River Offset: <strong>{s.distance} m</strong></span>
                  <span>Agency: <strong>{s.agency}</strong></span>
                </div>

                <div className="flex flex-wrap items-center gap-1.5 pt-1">
                  {s.facilities.map((fac, idx) => (
                    <span
                      key={idx}
                      className="rounded bg-[#E6F5F5] px-2 py-0.5 text-[10px] font-medium text-[#182746]"
                    >
                      {fac}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Population & Evacuation Column (1 col) */}
        <div className="space-y-5">
          {/* Population Exposure Card */}
          <div className="rounded-xl border border-[#D8ECEC] bg-[#FFFFFF] p-5 shadow-sm space-y-3">
            <div className="flex items-center gap-2 border-b border-[#D8ECEC] pb-2">
              <Users className="h-4 w-4 text-[#119E9A]" />
              <h2 className="text-sm font-bold text-[#182746]">
                Population Exposure Summary
              </h2>
            </div>

            <div className="space-y-2 text-xs">
              <div className="flex justify-between p-2 rounded bg-[#F5F9F9] border border-[#D8ECEC]">
                <span className="text-[#5A6A7E]">Low-lying Villages / Settlements:</span>
                <span className="font-mono font-bold text-[#182746]">14</span>
              </div>
              <div className="flex justify-between p-2 rounded bg-[#F5F9F9] border border-[#D8ECEC]">
                <span className="text-[#5A6A7E]">Estimated Floodplain Residents:</span>
                <span className="font-mono font-bold text-[#182746]">37,500</span>
              </div>
              <div className="flex justify-between p-2 rounded bg-[#F5F9F9] border border-[#D8ECEC]">
                <span className="text-[#5A6A7E]">Livestock at Risk:</span>
                <span className="font-mono font-bold text-[#182746]">12,400</span>
              </div>
            </div>

            <div className="rounded-lg bg-amber-50 p-2.5 border border-amber-200 text-[11px] text-amber-900 flex items-start gap-1.5">
              <Info className="h-3.5 w-3.5 shrink-0 text-amber-700 mt-0.5" />
              <span>
                <strong>Illustrative Attribution:</strong> Cell-level raster grids (WorldPop/LandScan) and detailed demographics are not in repository. Figures reflect unvalidated administrative estimates derived from DDMA public reports.
              </span>
            </div>
          </div>

          {/* Evacuation Corridors Card */}
          <div className="rounded-xl border border-[#D8ECEC] bg-[#FFFFFF] p-5 shadow-sm space-y-3">
            <div className="flex items-center gap-2 border-b border-[#D8ECEC] pb-2">
              <Navigation className="h-4 w-4 text-[#119E9A]" />
              <h2 className="text-sm font-bold text-[#182746]">
                Illustrative Evacuation Corridors (Unvalidated Vectors)
              </h2>
            </div>

            <div className="space-y-2 text-xs">
              {[
                { name: 'Palla Khadar → Alipur Highland', dist: '2.4 km', mode: 'Tractor / Embankment', prio: 'PRIMARY' },
                { name: 'Monastery Market → Ring Road', dist: '1.8 km', mode: 'Pedestrian / Shuttle', prio: 'CRITICAL' },
                { name: 'Chilla Khadar → Noida Link Road', dist: '2.1 km', mode: 'DDMA Corridor Route', prio: 'PRIMARY' },
                { name: 'Yamuna Bazar → Nigambodh Arterial', dist: '1.2 km', mode: 'Footpath / Bus Shuttle', prio: 'HIGH' },
              ].map((c, idx) => (
                <div key={idx} className="p-2 rounded bg-[#F5F9F9] border border-[#D8ECEC] space-y-1">
                  <div className="flex justify-between font-semibold text-[#182746]">
                    <span>{c.name}</span>
                    <span className="font-mono text-[10px] text-[#119E9A]">{c.prio}</span>
                  </div>
                  <div className="flex justify-between text-[11px] text-[#5A6A7E]">
                    <span>{c.mode}</span>
                    <span className="font-mono">{c.dist}</span>
                  </div>
                </div>
              ))}
            </div>

            <div className="text-[11px] text-[#5A6A7E] italic">
              Illustrative arterial vectors only. Route elevations have NOT been ground-surveyed or hydraulically validated for submergence safety.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
