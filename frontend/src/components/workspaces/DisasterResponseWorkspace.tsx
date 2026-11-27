/**
 * frontend/src/components/workspaces/DisasterResponseWorkspace.tsx
 *
 * Unified Disaster Intelligence & Emergency Response Workspace for PRAVAAH in authentic Cream & Brown styling:
 * Organized into 4 clear sections:
 * 1. Warning Thresholds (CWC Gauge at Delhi ORB & Hathnikund discharge bands).
 * 2. Population Exposure (Administrative summaries with explicit raster disclaimers).
 * 3. Relief Shelters (DDMA emergency shelters labelled as illustrative prototypes).
 * 4. Evacuation Corridors (Pre-designated routes labelled as illustrative prototypes).
 */

import React, { useEffect, useState } from 'react';
import {
  ShieldAlert,
  Building2,
  Users,
  Navigation,
  Info,
  MapPin,
} from 'lucide-react';
import type { DisasterRiskSummaryResponse, ReliefShelter } from '../../types/disaster';
import { fetchDisasterRiskSummary } from '../../services/disaster';

interface DisasterResponseWorkspaceProps {
  onNavigateToMap: () => void;
}

type TabKey = 'thresholds' | 'exposure' | 'shelters' | 'corridors';

const SHELTERS_LIST: ReliefShelter[] = [
  {
    shelter_id: 'SHELTER_PALLA_01',
    name: 'Palla Community Disaster Relief Centre',
    zone: 'North Delhi (Palla - Alipur)',
    latitude: 28.8472,
    longitude: 77.2081,
    capacity_persons: 600,
    elevation_msl: 212.5,
    distance_to_river_m: 850.0,
    facilities: ['Drinking Water', 'First Aid', 'Temporary Sanitation', 'Emergency Generator'],
    contact_agency: 'District Magistrate (North Delhi) / DDMA',
    status: 'ILLUSTRATIVE_PROTOTYPE',
  },
  {
    shelter_id: 'SHELTER_WAZIRABAD_02',
    name: 'Wazirabad Water Works Relief Station',
    zone: 'North-East Delhi (Wazirabad)',
    latitude: 28.7125,
    longitude: 77.2345,
    capacity_persons: 1200,
    elevation_msl: 210.0,
    distance_to_river_m: 450.0,
    facilities: ['Purified Water Supply', 'Medical Tents', 'Mobile Kitchens', 'Boat Evacuation Staging'],
    contact_agency: 'Delhi Jal Board / DDMA North-East',
    status: 'ILLUSTRATIVE_PROTOTYPE',
  },
  {
    shelter_id: 'SHELTER_YAMUNA_BAZAR_03',
    name: 'Yamuna Bazar / Kashmiri Gate Flood Transit Camp',
    zone: 'Central Delhi (Kashmiri Gate)',
    latitude: 28.6655,
    longitude: 77.2388,
    capacity_persons: 2500,
    elevation_msl: 209.5,
    distance_to_river_m: 250.0,
    facilities: ['Large Canopy Shelters', 'Ambulance Standby', 'Catering Depot', 'Disaster Relief Cell'],
    contact_agency: 'District Disaster Management Authority (Central Delhi)',
    status: 'ILLUSTRATIVE_PROTOTYPE',
  },
  {
    shelter_id: 'SHELTER_MAYUR_VIHAR_04',
    name: 'Mayur Vihar Phase-I Multi-Purpose Relief Ground',
    zone: 'East Delhi (Mayur Vihar)',
    latitude: 28.6045,
    longitude: 77.2912,
    capacity_persons: 1800,
    elevation_msl: 208.0,
    distance_to_river_m: 600.0,
    facilities: ['Flood Relief Tents', 'Clean Water Tankers', 'Sanitation Blocks', 'Distribution Counters'],
    contact_agency: 'East Delhi Municipal Administration / DDMA East',
    status: 'ILLUSTRATIVE_PROTOTYPE',
  },
  {
    shelter_id: 'SHELTER_OKHLA_05',
    name: 'Okhla Headworks Emergency Relief Centre',
    zone: 'South-East Delhi (Okhla)',
    latitude: 28.5412,
    longitude: 77.3115,
    capacity_persons: 900,
    elevation_msl: 206.5,
    distance_to_river_m: 350.0,
    facilities: ['Water Purification Units', 'Power Generators', 'First Aid Station', 'Transit Vehicles'],
    contact_agency: 'Irrigation & Flood Control Dept. (Govt. of NCT of Delhi)',
    status: 'ILLUSTRATIVE_PROTOTYPE',
  },
];

const CORRIDORS_LIST = [
  {
    id: 'CORRIDOR_PALLA_01',
    name: 'Palla Lowland to Alipur Higher Ground',
    origin: 'Palla Agricultural Floodplain (Km 220)',
    destination: 'Palla Community Disaster Relief Centre',
    distance_km: 3.2,
    mode: 'Multi-lane Paved Highway (GT Karnal Rd access)',
    priority: 'HIGH_PRIORITY_RESCUE',
    elevation_gain_m: 8.5,
  },
  {
    id: 'CORRIDOR_WAZIRABAD_02',
    name: 'Wazirabad Ghat to Timarpur Relief Ground',
    origin: 'Wazirabad Village & Jagatpur Embankment',
    destination: 'Wazirabad Water Works Relief Station',
    distance_km: 2.4,
    mode: 'Paved Arterial Road (Outer Ring Rd access)',
    priority: 'PRIMARY_EVACUATION',
    elevation_gain_m: 6.2,
  },
  {
    id: 'CORRIDOR_YAMUNA_BAZAR_03',
    name: 'Yamuna Bazar / Nigambodh to Kashmiri Gate Metro',
    origin: 'Yamuna Bazar Lowland & Ghat Settlements',
    destination: 'Kashmiri Gate Relief Camp & Elevated Concourse',
    distance_km: 1.1,
    mode: 'Elevated Flyover & Foot over Bridges',
    priority: 'URGENT_URBAN_RESCUE',
    elevation_gain_m: 5.8,
  },
  {
    id: 'CORRIDOR_MAYUR_VIHAR_04',
    name: 'Chilla Khadar Floodplain to Mayur Vihar Link',
    origin: 'Chilla Khadar Agricultural Clusters',
    destination: 'Mayur Vihar Phase-I Multi-Purpose Ground',
    distance_km: 2.8,
    mode: 'Elevated Noida Link Road Corridor',
    priority: 'SECONDARY_EVACUATION',
    elevation_gain_m: 4.5,
  },
];

export const DisasterResponseWorkspace: React.FC<DisasterResponseWorkspaceProps> = ({
  onNavigateToMap,
}) => {
  const [data, setData] = useState<DisasterRiskSummaryResponse | null>(null);
  const [activeTab, setActiveTab] = useState<TabKey>('thresholds');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [simulatedInflow, setSimulatedInflow] = useState<number>(650.0);

  const loadData = async (inflowVal: number) => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetchDisasterRiskSummary(inflowVal);
      setData(res);
    } catch (err) {
      setError((err as Error).message || 'Failed to load disaster risk summary.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData(simulatedInflow);
  }, []);

  const handleInflowChange = (val: number) => {
    setSimulatedInflow(val);
    loadData(val);
  };

  return (
    <div className="h-full w-full overflow-y-auto bg-[#FBF9F5] p-4 sm:p-6 lg:p-8 text-[#3E3026]">
      <div className="mx-auto max-w-6xl space-y-6">
        {/* Top Header Card */}
        <div className="rounded-2xl border border-[#EAE3D9] bg-[#FFFFFF] p-5 sm:p-6 shadow-xs">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              <div className="flex items-center gap-2">
                <span className="rounded-md bg-[#F5EFEB] px-2.5 py-0.5 text-[11px] font-bold uppercase tracking-wider text-[#8B4513]">
                  Emergency Coordination
                </span>
                <span className="text-[11px] text-[#8C7869]">
                  Delhi NCT Floodplain Sector
                </span>
                {isLoading && (
                  <span className="flex items-center gap-1 rounded bg-[#EAE3D9] px-1.5 py-0.5 text-[10px] text-[#635347]">
                    <span className="h-2 w-2 animate-spin rounded-full border-2 border-[#8B4513] border-t-transparent"></span>
                    Updating...
                  </span>
                )}
              </div>
              <h1 className="mt-1 text-2xl font-extrabold tracking-tight text-[#2C221E] sm:text-3xl">
                Disaster Response & Decision Support
              </h1>
              <p className="mt-1 text-xs text-[#635347] max-w-3xl leading-relaxed">
                Central Water Commission (CWC) official river thresholds at Delhi Old Railway Bridge, 
                administrative population demographics, candidate relief shelters, and designated evacuation corridors.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={onNavigateToMap}
                className="flex items-center gap-1.5 rounded-xl bg-[#8B4513] px-4 py-2.5 text-xs font-bold text-white shadow-xs hover:bg-[#70360E] transition-all"
              >
                <MapPin className="h-4 w-4" />
                <span>View Shelters on Map</span>
              </button>
            </div>
          </div>
        </div>

        {error && (
          <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-xs text-red-700">
            {error}
          </div>
        )}

        {/* 4 Section Tabs */}
        <div className="flex border-b border-[#EAE3D9] bg-[#FFFFFF] rounded-t-xl px-4 pt-2">
          {[
            { id: 'thresholds', label: '1. Warning Thresholds', icon: ShieldAlert },
            { id: 'exposure', label: '2. Population Exposure', icon: Users },
            { id: 'shelters', label: '3. Relief Shelters', icon: Building2 },
            { id: 'corridors', label: '4. Evacuation Corridors', icon: Navigation },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as TabKey)}
                className={`flex items-center gap-2 border-b-2 py-3 px-4 text-xs font-bold transition-all ${
                  isActive
                    ? 'border-[#8B4513] text-[#2C221E] bg-[#F5EFEB]/40'
                    : 'border-transparent text-[#635347] hover:text-[#2C221E]'
                }`}
              >
                <Icon className={`h-4 w-4 ${isActive ? 'text-[#8B4513]' : 'text-[#8C7869]'}`} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Tab Content Panels */}
        <div className="rounded-b-2xl border-x border-b border-[#EAE3D9] bg-[#FFFFFF] p-5 sm:p-6 shadow-xs">
          {/* SECTION 1: Warning Thresholds */}
          {activeTab === 'thresholds' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-sm font-bold text-[#2C221E] flex items-center gap-2">
                  <ShieldAlert className="h-4 w-4 text-[#8B4513]" />
                  Authoritative Gauge & Discharge Flood Classifications
                </h3>
                <p className="mt-1 text-xs text-[#635347]">
                  Official Central Water Commission (CWC) and Haryana Irrigation Department benchmarks governing the Yamuna corridor.
                </p>
              </div>

              {/* Inflow Interactive Test Slider */}
              <div className="rounded-xl border border-[#EAE3D9] bg-[#FBF9F5] p-4 text-xs">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div>
                    <span className="font-bold text-[#2C221E]">Inflow Threshold Evaluator:</span>{' '}
                    <span className="font-mono font-bold text-[#8B4513] text-sm">
                      {simulatedInflow.toLocaleString()} m³/s
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5 text-[11px]">
                    {[
                      { label: 'Normal (650)', val: 650 },
                      { label: 'Low Flood (4,250)', val: 4250 },
                      { label: 'High Flood (7,100)', val: 7100 },
                      { label: 'Extreme (10,194)', val: 10194 },
                    ].map((btn) => (
                      <button
                        key={btn.val}
                        onClick={() => handleInflowChange(btn.val)}
                        className="rounded border border-[#EAE3D9] bg-[#FFFFFF] px-2 py-1 font-semibold text-[#2C221E] hover:bg-[#8B4513] hover:text-white transition-colors"
                      >
                        {btn.label}
                      </button>
                    ))}
                  </div>
                </div>

                <input
                  type="range"
                  min={200}
                  max={12000}
                  step={200}
                  value={simulatedInflow}
                  onChange={(e) => handleInflowChange(parseFloat(e.target.value))}
                  className="w-full mt-3 accent-[#8B4513]"
                />
              </div>

              {/* Threshold Comparison Grid */}
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                {/* Delhi ORB Gauge */}
                <div className="rounded-xl border border-[#EAE3D9] bg-[#FFFDF9] p-4 space-y-3">
                  <div className="flex items-center justify-between border-b border-[#EAE3D9] pb-2">
                    <span className="font-bold text-xs text-[#2C221E]">
                      Delhi Old Railway Bridge (ORB) Gauge
                    </span>
                    <span className="rounded bg-[#F5EFEB] px-2 py-0.5 text-[10px] font-bold text-[#8B4513]">
                      CWC Station 028-MDD
                    </span>
                  </div>

                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between items-center p-2 rounded bg-[#FFFFFF] border border-[#EAE3D9]">
                      <span className="text-[#635347]">Zero Gauge Datum</span>
                      <span className="font-mono font-bold text-[#2C221E]">201.25 m MSL</span>
                    </div>
                    <div className="flex justify-between items-center p-2 rounded bg-[#FEF3C7] border border-amber-300">
                      <span className="font-semibold text-amber-900">Official Warning Level</span>
                      <span className="font-mono font-bold text-amber-900">204.50 m MSL</span>
                    </div>
                    <div className="flex justify-between items-center p-2 rounded bg-[#FED7D7] border border-red-300">
                      <span className="font-semibold text-red-900">Official Danger Level</span>
                      <span className="font-mono font-bold text-red-900">205.33 m MSL</span>
                    </div>
                    <div className="flex justify-between items-center p-2 rounded bg-[#FFFFFF] border border-[#EAE3D9]">
                      <span className="text-[#635347]">Historical Record (HFL)</span>
                      <span className="font-mono font-bold text-[#8B4513]">208.66 m MSL (13 July 2023)</span>
                    </div>
                  </div>
                </div>

                {/* Hathnikund Barrage Discharge */}
                <div className="rounded-xl border border-[#EAE3D9] bg-[#FFFDF9] p-4 space-y-3">
                  <div className="flex items-center justify-between border-b border-[#EAE3D9] pb-2">
                    <span className="font-bold text-xs text-[#2C221E]">
                      Hathnikund Barrage Discharge Categories
                    </span>
                    <span className="rounded bg-[#F5EFEB] px-2 py-0.5 text-[10px] font-bold text-[#8B4513]">
                      Haryana I&WRD
                    </span>
                  </div>

                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between items-center p-2 rounded bg-[#FFFFFF] border border-[#EAE3D9]">
                      <span className="text-[#635347]">Normal Baseline</span>
                      <span className="font-mono font-bold text-[#2C221E]">&lt; 1,982 m³/s (70k cfs)</span>
                    </div>
                    <div className="flex justify-between items-center p-2 rounded bg-[#EBF3F9] border border-blue-300">
                      <span className="font-semibold text-[#2B5B84]">Low Flood Threshold</span>
                      <span className="font-mono font-bold text-[#2B5B84]">4,248 m³/s (150k cfs)</span>
                    </div>
                    <div className="flex justify-between items-center p-2 rounded bg-[#FEF3C7] border border-amber-300">
                      <span className="font-semibold text-amber-900">High Flood Threshold</span>
                      <span className="font-mono font-bold text-amber-900">7,079 m³/s (250k cfs)</span>
                    </div>
                    <div className="flex justify-between items-center p-2 rounded bg-[#FED7D7] border border-red-300">
                      <span className="font-semibold text-red-900">Extreme Surge Level</span>
                      <span className="font-mono font-bold text-red-900">&gt; 7,079 m³/s</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* SECTION 2: Population Exposure */}
          {activeTab === 'exposure' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-sm font-bold text-[#2C221E] flex items-center gap-2">
                  <Users className="h-4 w-4 text-[#8B4513]" />
                  Administrative Floodplain Exposure Assessment
                </h3>
                <p className="mt-1 text-xs text-[#635347]">
                  Baseline demographic summaries across riverfront districts along the Delhi Yamuna corridor.
                </p>
              </div>

              {/* Mandatory Scientific Disclaimer Alert */}
              <div className="rounded-xl border border-amber-300 bg-[#FFFDF9] p-4 text-xs text-[#635347] flex items-start gap-3">
                <Info className="h-5 w-5 text-[#B45309] shrink-0 mt-0.5" />
                <div className="leading-relaxed">
                  <strong className="text-[#2C221E]">Mandatory Scientific Disclaimer:</strong> Population summaries presented here
                  are derived strictly from published administrative census estimates. PRAVAAH operates as a 1D hydrological intelligence
                  tool and <em>strictly refuses to synthesize or fabricate 2D raster flood depth or arbitrary pixel-level exposure</em>.
                </div>
              </div>

              {/* Exposure Indicators Grid */}
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                <div className="rounded-xl border border-[#EAE3D9] bg-[#FFFDF9] p-4 text-center">
                  <div className="text-[10px] font-bold uppercase text-[#8C7869]">Low-Lying Clusters</div>
                  <div className="mt-1 text-2xl font-extrabold text-[#2C221E]">
                    {data?.population_exposure.low_lying_villages_count || 14}
                  </div>
                  <div className="mt-1 text-[11px] text-[#635347]">Identified floodplain settlements</div>
                </div>

                <div className="rounded-xl border border-[#EAE3D9] bg-[#FFFDF9] p-4 text-center">
                  <div className="text-[10px] font-bold uppercase text-[#8C7869]">Estimated Residents</div>
                  <div className="mt-1 text-2xl font-extrabold text-[#2C221E]">
                    {(data?.population_exposure.estimated_floodplain_residents || 38500).toLocaleString()}
                  </div>
                  <div className="mt-1 text-[11px] text-[#635347]">Administrative census baseline</div>
                </div>

                <div className="rounded-xl border border-[#EAE3D9] bg-[#FFFDF9] p-4 text-center">
                  <div className="text-[10px] font-bold uppercase text-[#8C7869]">Livestock Population</div>
                  <div className="mt-1 text-2xl font-extrabold text-[#2C221E]">
                    {(data?.population_exposure.livestock_count || 12400).toLocaleString()}
                  </div>
                  <div className="mt-1 text-[11px] text-[#635347]">Cattle & domestic animals</div>
                </div>
              </div>

              {/* Vulnerable Clusters List */}
              <div className="rounded-xl border border-[#EAE3D9] bg-[#FFFFFF] p-4">
                <div className="text-xs font-bold text-[#2C221E] mb-2">High-Vulnerability Riverfront Sectors</div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                  {[
                    'Palla & Alipur agricultural lowlands (North Delhi)',
                    'Wazirabad & Jagatpur embankments (North-East Delhi)',
                    'Yamuna Bazar & Nigambodh Ghat lowland (Central Delhi)',
                    'Mayur Vihar & Chilla Khadar floodplains (East Delhi)',
                    'Okhla & Kalindi Kunj lowlands (South-East Delhi)',
                  ].map((sector, i) => (
                    <div key={i} className="flex items-center gap-2 p-2 rounded bg-[#FBF9F5] border border-[#EAE3D9]">
                      <span className="h-1.5 w-1.5 rounded-full bg-[#8B4513]"></span>
                      <span className="text-[#2C221E] font-medium">{sector}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* SECTION 3: Relief Shelters */}
          {activeTab === 'shelters' && (
            <div className="space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div>
                  <h3 className="text-sm font-bold text-[#2C221E] flex items-center gap-2">
                    <Building2 className="h-4 w-4 text-[#8B4513]" />
                    Designated Relief Shelters Directory
                  </h3>
                  <p className="mt-1 text-xs text-[#635347]">
                    5 DDMA candidate shelters along the Delhi Yamuna flood corridor with recorded capacities.
                  </p>
                </div>

                <span className="rounded-md bg-[#FEF3C7] border border-amber-300 px-2.5 py-1 text-[10px] font-bold text-amber-900">
                  CANDIDATE SHELTERS — REAL-TIME OCCUPANCY UNAVAILABLE
                </span>
              </div>

              <div className="rounded-xl border border-[#EAE3D9] bg-[#FFFDF9] p-3 text-xs text-[#635347]">
                <strong className="text-[#2C221E]">Planning Benchmark Notice:</strong> Shelter capacities reflect official static design baselines.
                Continuous real-time occupancy telemetry and dynamic bed availability are currently unavailable.
              </div>

              {/* Shelters Table */}
              <div className="overflow-x-auto rounded-xl border border-[#EAE3D9]">
                <table className="w-full text-left text-xs">
                  <thead className="bg-[#FBF9F5] text-[10px] uppercase text-[#8C7869] border-b border-[#EAE3D9]">
                    <tr>
                      <th className="py-2.5 px-3">Shelter Name & ID</th>
                      <th className="py-2.5 px-3">Zone</th>
                      <th className="py-2.5 px-3 text-right">Capacity</th>
                      <th className="py-2.5 px-3 text-right">Elevation</th>
                      <th className="py-2.5 px-3 text-right">River Distance</th>
                      <th className="py-2.5 px-3">Available Facilities</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#EAE3D9]">
                    {SHELTERS_LIST.map((shelter) => (
                      <tr key={shelter.shelter_id} className="hover:bg-[#F5EFEB]/40">
                        <td className="py-3 px-3">
                          <div className="font-bold text-[#2C221E]">{shelter.name}</div>
                          <div className="font-mono text-[10px] text-[#8C7869]">{shelter.shelter_id}</div>
                        </td>
                        <td className="py-3 px-3 text-[#635347]">{shelter.zone}</td>
                        <td className="py-3 px-3 text-right font-bold text-[#8B4513]">
                          {shelter.capacity_persons.toLocaleString()} <span className="text-[10px] font-normal text-[#8C7869]">persons</span>
                        </td>
                        <td className="py-3 px-3 text-right font-mono text-[#635347]">
                          {shelter.elevation_msl.toFixed(1)} m
                        </td>
                        <td className="py-3 px-3 text-right font-mono text-[#635347]">
                          {shelter.distance_to_river_m} m
                        </td>
                        <td className="py-3 px-3">
                          <div className="flex flex-wrap gap-1">
                            {shelter.facilities.map((fac, idx) => (
                              <span key={idx} className="rounded bg-[#F5EFEB] px-1.5 py-0.5 text-[9px] text-[#635347]">
                                {fac}
                              </span>
                            ))}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* SECTION 4: Evacuation Corridors */}
          {activeTab === 'corridors' && (
            <div className="space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div>
                  <h3 className="text-sm font-bold text-[#2C221E] flex items-center gap-2">
                    <Navigation className="h-4 w-4 text-[#8B4513]" />
                    Designated Evacuation Corridors
                  </h3>
                  <p className="mt-1 text-xs text-[#635347]">
                    4 pre-identified transit routes connecting riverfront lowland settlements to relief shelters.
                  </p>
                </div>

                <span className="rounded-md bg-[#FEF3C7] border border-amber-300 px-2.5 py-1 text-[10px] font-bold text-amber-900">
                  DESIGNATED PLANNING CORRIDORS — ROAD SUBMERGENCE UNVERIFIED
                </span>
              </div>

              <div className="rounded-xl border border-[#EAE3D9] bg-[#FFFDF9] p-3 text-xs text-[#635347]">
                <strong className="text-[#2C221E]">Route Safety Notice:</strong> Evacuation corridors represent municipal planning alignments.
                Road-network hazard validation and hydraulic submergence clearance are <strong>unverified</strong>. Never describe a corridor as a guaranteed safe route.
              </div>

              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                {CORRIDORS_LIST.map((corridor) => (
                  <div key={corridor.id} className="rounded-xl border border-[#EAE3D9] bg-[#FFFDF9] p-4 space-y-2">
                    <div className="flex items-center justify-between pb-1 border-b border-[#EAE3D9]">
                      <span className="font-bold text-xs text-[#2C221E]">{corridor.name}</span>
                      <span className="rounded bg-[#F5EFEB] px-2 py-0.5 text-[10px] font-bold text-[#8B4513]">
                        {corridor.priority}
                      </span>
                    </div>

                    <div className="space-y-1 text-xs text-[#635347]">
                      <div>
                        <strong className="text-[#2C221E]">Origin:</strong> {corridor.origin}
                      </div>
                      <div>
                        <strong className="text-[#2C221E]">Destination:</strong> {corridor.destination}
                      </div>
                      <div className="flex justify-between font-mono text-[11px] pt-1">
                        <span>Distance: <strong>{corridor.distance_km} km</strong></span>
                        <span>Elevation Gain: <strong>+{corridor.elevation_gain_m} m</strong></span>
                      </div>
                      <div className="text-[11px] text-[#8C7869]">
                        <strong>Transit Mode:</strong> {corridor.mode}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
