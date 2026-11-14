/**
 * frontend/src/components/evacuation/EvacuationWorkspace.tsx
 *
 * Dedicated Evacuation Assistance workspace for PRAVAAH styled in the unified Navy, Teal & Aqua theme:
 * Displays candidate emergency relief shelters and arterial evacuation vectors
 * with explicit scientific and operational guardrails.
 */

import React, { useState, useEffect } from 'react';
import {
  AlertTriangle,
  MapPin,
  Navigation,
} from 'lucide-react';
import { fetchSheltersGeoJSON } from '../../services/disaster';
import type { ReliefShelter } from '../../types/disaster';

interface EvacuationWorkspaceProps {
  onNavigateToMap?: () => void;
}

export const EvacuationWorkspace: React.FC<EvacuationWorkspaceProps> = ({ onNavigateToMap }) => {
  const [shelters, setShelters] = useState<ReliefShelter[]>([]);
  const [selectedZone, setSelectedZone] = useState<string>('ALL');

  useEffect(() => {
    let isMounted = true;
    async function loadData() {
      try {
        const geojson = await fetchSheltersGeoJSON();
        if (isMounted && geojson?.features) {
          const list: ReliefShelter[] = geojson.features.map((f: any) => ({
            shelter_id: f.properties.shelter_id,
            name: f.properties.name,
            zone: f.properties.zone,
            latitude: f.geometry.coordinates[1],
            longitude: f.geometry.coordinates[0],
            capacity_persons: f.properties.capacity_persons,
            elevation_msl: f.properties.elevation_msl,
            distance_to_river_m: f.properties.distance_to_river_m,
            facilities: f.properties.facilities || [],
            contact_agency: f.properties.contact_agency,
            status: f.properties.status || 'ILLUSTRATIVE_PROTOTYPE',
          }));
          setShelters(list);
        }
      } catch (err) {
        console.error('Failed to load shelters:', err);
      }
    }
    loadData();
    return () => {
      isMounted = false;
    };
  }, []);

  const zones = ['ALL', ...Array.from(new Set(shelters.map((s) => s.zone)))];
  const filteredShelters =
    selectedZone === 'ALL' ? shelters : shelters.filter((s) => s.zone === selectedZone);

  return (
    <div className="h-full w-full overflow-y-auto bg-[#F5F9F9] p-4 sm:p-6 lg:p-8 text-[#2B3A4A]">
      <div className="max-w-5xl mx-auto space-y-6">
        {/* Workspace Title & Description */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-[#D8ECEC] pb-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="rounded-full bg-[#E6F5F5] px-2.5 py-0.5 text-xs font-bold text-[#119E9A]">
                Section 4
              </span>
              <h1 className="text-xl font-bold text-[#182746]">Evacuation Assistance</h1>
            </div>
            <p className="mt-1 text-xs text-[#5A6A7E]">
              Candidate flood relief shelters and arterial transit directions along the Yamuna corridor.
            </p>
          </div>

          {onNavigateToMap && (
            <button
              type="button"
              onClick={onNavigateToMap}
              className="inline-flex items-center gap-1.5 rounded-full bg-[#119E9A] px-4 py-2 text-xs font-bold text-white shadow-xs hover:bg-[#0E8582] transition-colors"
            >
              <MapPin className="h-3.5 w-3.5" />
              <span>Inspect on Risk Map</span>
            </button>
          )}
        </div>

        {/* MANDATORY SCIENTIFIC GUARDRAIL DISCLAIMER */}
        <div className="rounded-2xl border-2 border-amber-300 bg-amber-50 p-4 sm:p-5 text-xs text-amber-900 shadow-2xs">
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 shrink-0 text-amber-700 mt-0.5" />
            <div className="space-y-1">
              <span className="font-bold text-amber-950 uppercase tracking-wide">
                OPERATIONAL DISCLAIMER — CANDIDATE PLANNING FACILITIES ONLY
              </span>
              <p className="leading-relaxed">
                The evacuation locations and corridors listed below are illustrative planning references
                compiled from published municipal flood guidelines (DDMA/MCD). 
                <strong> Arterial road elevations, culvert capacities, and submergence clearances have NOT been ground-surveyed or hydraulically certified.</strong>
                Do NOT treat these candidate locations as certified safe havens without direct municipal authorization.
              </p>
            </div>
          </div>
        </div>

        {/* Zone Filter & Summary Bar */}
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-[#D8ECEC] bg-[#FFFFFF] p-3.5 shadow-2xs">
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold text-[#182746] uppercase tracking-wider">
              Filter Zone:
            </span>
            <select
              value={selectedZone}
              onChange={(e) => setSelectedZone(e.target.value)}
              className="rounded-lg border border-[#D8ECEC] bg-[#FFFFFF] px-3 py-1.5 text-xs font-semibold text-[#182746] focus:border-[#119E9A] focus:outline-hidden shadow-2xs"
              aria-label="Filter shelters by zone"
            >
              {zones.map((z) => (
                <option key={z} value={z}>
                  {z === 'ALL' ? 'All Floodplain Zones' : z}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-3 text-xs font-semibold text-[#5A6A7E]">
            <span>Candidate Facilities: <strong className="text-[#182746]">{filteredShelters.length}</strong></span>
            <span>•</span>
            <span>Est. Capacity: <strong className="text-[#182746]">~4,950 persons</strong></span>
          </div>
        </div>

        {/* Candidate Shelters Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredShelters.map((shelter) => (
            <div
              key={shelter.shelter_id}
              className="rounded-2xl border border-[#D8ECEC] bg-[#FFFFFF] p-5 shadow-2xs hover:border-[#119E9A] transition-all space-y-3"
            >
              <div className="flex items-start justify-between">
                <div>
                  <span className="inline-block rounded-full bg-[#E6F5F5] px-2.5 py-0.5 text-[10px] font-bold text-[#119E9A] mb-1">
                    {shelter.zone}
                  </span>
                  <h3 className="text-base font-bold text-[#182746]">{shelter.name}</h3>
                </div>
                <span className="rounded-full border border-amber-300 bg-amber-50 px-2.5 py-0.5 text-[9px] font-bold text-amber-800">
                  Candidate
                </span>
              </div>

              <div className="grid grid-cols-2 gap-2.5 text-xs text-[#2B3A4A] bg-[#F5F9F9] p-3 rounded-xl border border-[#D8ECEC]">
                <div>
                  <span className="text-[10px] text-[#5A6A7E] font-medium block">Est. Capacity</span>
                  <span className="font-extrabold text-sm text-[#182746]">~{shelter.capacity_persons}</span> persons
                </div>
                <div>
                  <span className="text-[10px] text-[#5A6A7E] font-medium block">River Offset</span>
                  <span className="font-extrabold text-sm text-[#182746]">{shelter.distance_to_river_m}</span> m
                </div>
                <div>
                  <span className="text-[10px] text-[#5A6A7E] font-medium block">Ground Elevation</span>
                  <span className="font-bold text-[#182746]">{shelter.elevation_msl}</span> m MSL
                </div>
                <div>
                  <span className="text-[10px] text-[#5A6A7E] font-medium block">Authority</span>
                  <span className="font-semibold text-[#182746] truncate block" title={shelter.contact_agency}>
                    {shelter.contact_agency.split('/')[0]}
                  </span>
                </div>
              </div>

              {/* Facilities tags */}
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-[#5A6A7E] block mb-1.5">
                  Available Amenities
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {shelter.facilities.map((fac) => (
                    <span
                      key={fac}
                      className="rounded-lg border border-[#D8ECEC] bg-[#F5F9F9] px-2 py-0.5 text-[10px] font-medium text-[#2B3A4A]"
                    >
                      {fac}
                    </span>
                  ))}
                </div>
              </div>

              <div className="pt-2.5 border-t border-[#D8ECEC] flex items-center justify-between text-[11px] text-[#5A6A7E]">
                <span>Coords: {shelter.latitude.toFixed(4)}°N, {shelter.longitude.toFixed(4)}°E</span>
                <span className="font-mono text-[10px] text-[#5A6A7E]">{shelter.shelter_id}</span>
              </div>
            </div>
          ))}
        </div>

        {/* 4 Arterial Evacuation Vectors Card */}
        <div className="rounded-2xl border border-[#D8ECEC] bg-[#FFFFFF] p-5 shadow-2xs space-y-3">
          <div className="flex items-center gap-2">
            <Navigation className="h-5 w-5 text-[#119E9A]" />
            <h2 className="text-base font-bold text-[#182746]">
              Arterial Floodplain Evacuation Vectors (Unvalidated)
            </h2>
          </div>
          <p className="text-xs text-[#5A6A7E]">
            Pre-designated transit corridors guiding residents from active inundation khadars to highland embankments:
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 pt-1 text-xs">
            <div className="p-3 rounded-xl bg-[#F5F9F9] border border-[#D8ECEC]">
              <span className="font-bold text-[#182746] block text-sm">1. Palla Khadar</span>
              <span className="text-[11px] text-[#5A6A7E] mt-0.5 block">Palla floodplains to Alipur Highland embankment (~2.4 km)</span>
            </div>
            <div className="p-3 rounded-xl bg-[#F5F9F9] border border-[#D8ECEC]">
              <span className="font-bold text-[#182746] block text-sm">2. Monastery / Civil Lines</span>
              <span className="text-[11px] text-[#5A6A7E] mt-0.5 block">Tibetan Market to Kashmere Gate highland (~1.8 km)</span>
            </div>
            <div className="p-3 rounded-xl bg-[#F5F9F9] border border-[#D8ECEC]">
              <span className="font-bold text-[#182746] block text-sm">3. Yamuna Bazar / Ring Road</span>
              <span className="text-[11px] text-[#5A6A7E] mt-0.5 block">Yamuna Ghats to Nigam Bodh highland (~1.5 km)</span>
            </div>
            <div className="p-3 rounded-xl bg-[#F5F9F9] border border-[#D8ECEC]">
              <span className="font-bold text-[#182746] block text-sm">4. Mayur Vihar Khadar</span>
              <span className="text-[11px] text-[#5A6A7E] mt-0.5 block">Chilla Khadar to Mayur Vihar Phase-1 highlands (~2.1 km)</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
