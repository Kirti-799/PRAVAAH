# PRAVAAH Phase 2C-A: Operational Readiness & Capability Roadmap

**Project:** PRAVAAH — Predictive Risk Assessment and Vulnerability Analysis for Adaptive Assistance & Humanitarian Response  
**Document:** Operational Readiness & Capability Roadmap  
**Phase:** 2C-A  
**Date:** October 19, 2026  

---

## 1. Executive Capability Classification

Based on empirical data availability, physical telemetry constraints, and algorithm validation, the capabilities of PRAVAAH are classified into four strict operational tiers:

```
TIER A: Supported by Verified Observations & Reproducible Pipelines
TIER B: Suitable for Research & Tabletop Simulation Only (Explicitly Labeled)
TIER C: Strictly Blocked by Missing In-Situ Telemetry
TIER D: Requires Advanced Scientific & Hydrodynamic Validation
```

### Comprehensive Capability Status Table

| Capability | Current Readiness Tier | Operational Verdict | Immediate Implementation Scope |
| :--- | :---: | :---: | :--- |
| **1. Upstream 24h Discharge Forecasting (Hathnikund Barrage)** | **TIER B** | **EXPERIMENTAL BENCHMARK ONLY (Not Promoted)** | Research-grade baseline comparison and tabular prediction given manual feature vectors. Structural underprediction during extreme surges (> $4,100\,\text{m}^3/\text{s}$). |
| **2. Downstream River Stage Prediction (Delhi ORB Station 028-MDD)** | **TIER C** | **STRICTLY BLOCKED** | **NO-GO.** Under CWC transboundary policies, continuous non-flood water levels are withheld. Stage prediction cannot be trained or issued. |
| **3. Flood Hazard & Risk Assessment** | **TIER B / D** | **SCENARIO DEMONSTRATION ONLY** | Synthetic flood reach categorization based on user-defined discharge scenarios; operational real-time risk assessment is blocked. |
| **4. Candidate Safe-Zone Identification** | **TIER B** | **RESEARCH / TOPOGRAPHIC SCREENING ONLY** | Topographic elevation screening from DEM rasters; strictly barred from claiming candidate locations are "certified shelters". |
| **5. Evacuation Route Analysis** | **TIER C** | **BLOCKED PENDING ROAD GRAPH** | **NO-GO.** Road network graph and depth-dependent vehicle passability models not yet ingested or validated. |
| **6. Population & Infrastructure Exposure Assessment** | **TIER C / D** | **BLOCKED PENDING GEODATABASE INGESTION** | **NO-GO.** Requires ingestion of high-resolution population rasters and OpenStreetMap infrastructure layers. |
| **7. What-If Disaster Scenario Simulation** | **TIER A / B** | **GO FOR TABLETOP EXERCISES** | Emergency managers can inject hypothetical discharge hydrographs (e.g., $100\text{k}, 300\text{k}, 800\text{k}$ cusecs) to observe simulated flood wave travel times. |

---

## 2. In-Depth Operational Assessment of Eventual Capabilities

### Capability 1: Flood-Risk Assessment

#### What Can Be Built Now
- Tabular, scenario-based flood hazard index based on upstream discharge brackets ($Q < 1,500\,\text{m}^3/\text{s} \to$ Normal; $1,500 \le Q < 4,000 \to$ Alert; $Q \ge 4,000 \to$ Extreme Surge).
- Historical event playback comparing the 2019, 2022, and 2023 flood episodes.

#### Real Data Required for Operational Promotion
- Continuous stage records at CWC Station 028-MDD.
- Stage-discharge rating curve or 2D hydrodynamic floodway model for the Delhi NCT reach.
- High-resolution river cross-sections from Wazirabad to Okhla Barrage.

#### Crucial Assumptions & Caveats
- Upstream discharge release does not linearly translate to downstream flood depth due to channel attenuation, floodway embankment overtopping, and bridge constriction backwaters (e.g. Old Railway Bridge piers).
- **Prohibited Claims:** Must NEVER display predicted water levels (m MSL) or probabilistic danger-mark breach percentages without CWC telemetry.

#### Mandatory UI Terminology
- *"Hypothetical Hazard Level (Scenario Mode)"*
- *"Upstream Flood Index (HKB D/S Release Indicator)"*
- Never use: *"Current Real-Time Flood Risk"*, *"Official CWC Warning Level"*.

---

### Capability 2: Candidate Safe-Zone Identification & Route Analysis

#### What Can Be Built Now
- Static geospatial overlay identifying land parcels with elevation $\ge 5\,\text{m}$ above the active Yamuna riverbed using open DEMs (SRTM 30m).
- Bounding-box proximity analysis for community awareness.

#### Real Data Required for Operational Promotion
- Authoritative inventory of designated relief shelters from the Delhi Disaster Management Authority (DDMA), including shelter capacity, sanitation, emergency power, and potable water.
- Routable OpenStreetMap vector road graph with accurate bridge elevations, underpass drainage flags, and culvert locations.
- Real-time road waterlogging sensors or traffic speed telemetry.

#### Crucial Assumptions & Caveats
> [!CAUTION]
> - **A candidate safe zone is NOT a verified safe shelter.** Elevation above the riverbed does not ensure physical structural safety, road accessibility, or provision of humanitarian relief.
> - **A route recommendation is NOT a confirmed passable route.** Low-lying underpasses, localized pluvial waterlogging, electrical hazards, and structural bridge closures cannot be resolved without real-time municipal telemetry.
> - **A low predicted risk does NOT guarantee safety.**

#### Mandatory UI Terminology
- *"Topographic High-Ground Candidate (Unverified DEM Screening)"*
- *"Indicative Evacuation Corridor (Requires Local Authority Confirmation)"*
- Never use: *"Certified Safe Shelter"*, *"Guaranteed Passable Evacuation Route"*.

---

### Capability 3: Population & Infrastructure Exposure Assessment

#### What Can Be Built Now
- Static zonal vulnerability summary based on historical administrative ward boundaries.
- Tabular impact summaries from historical flood reports (e.g., DDMA 2023 post-flood damage assessments).

#### Real Data Required for Operational Promotion
- High-resolution, contemporaneous gridded population datasets (e.g., WorldPop or 2025 municipal projections).
- Geo-located inventory of critical infrastructure: hospitals, electric sub-stations, water treatment plants (WTPs at Chandrawal and Wazirabad), and schools.
- Micro-level mapping of informal riverbed settlements (*jhuggi-jhopris*), which house the most vulnerable displaced populations.

#### Crucial Assumptions & Caveats
- Census 2011 figures severely underestimate current urban population densities in Delhi's informal riverine fringe.
- Static exposure counts do not account for daytime commuter flows, seasonal migrant farming, or pre-emptive self-evacuation.

#### Mandatory UI Terminology
- *"Estimated Baseline Population in Flood-Prone Belt (Census Proxy)"*
- *"Indicative Infrastructure Exposure (Static Screening)"*
- Never use: *"Confirmed Persons Impacted"*, *"Verified Inundated Critical Facilities"*.

---

### Capability 4: What-If Disaster Scenario Simulation

#### What Can Be Built Now
- **Interactive Barrage Release Scenario Injector:** Users can select hypothetical discharge pulses ($50,000$, $150,000$, $350,000$, or $800,000$ cusecs) and simulate flood wave attenuation and arrival times at Delhi using the Muskingum routing prototype.
- Comparative timeline analysis between the July 2023 benchmark ($3.59\text{ lakh cusecs}$) and August 2019 benchmark ($8.28\text{ lakh cusecs}$).

#### Real Data Required for Operational Promotion
- Hydrodynamic model calibration using real upstream-downstream hydrographs.
- Channel cross-section geometry and Manning's roughness coefficient ($n$).

#### Mandatory UI Terminology
- *"Tabletop Disaster Scenario Simulation (Theoretical Wave Routing)"*
- *"Educational Hydrograph Demonstration"*
- Never use: *"Live Flood Wave Forecast"*, *"Certified Hydrodynamic Prediction"*.

---

## 3. Explicit Go / Conditional Go / No-Go Decisions

```
+-------------------------------------------------------------------------------+
| MODULE / CAPABILITY                   | STATUS          | REASON              |
+-------------------------------------------------------------------------------+
| Upstream 24h Discharge Forecasting    | CONDITIONAL GO  | Research benchmark; |
|                                       | (EXPERIMENTAL)  | underpredicts surges|
| Downstream Delhi Stage Prediction     | NO-GO (BLOCKED) | CWC 028-MDD missing |
| Delhi Flood Breach Probability        | NO-GO (BLOCKED) | Target stage missing|
| What-If Scenario Simulation           | GO (TABLETOP)   | Proven educational  |
|                                       |                 | planning tool       |
| Topographic Safe-Zone Screening       | CONDITIONAL GO  | Explicit disclaimer;|
|                                       | (SCREENING ONLY)| not certified       |
| Evacuation Route Optimization         | NO-GO (BLOCKED) | Road graph missing  |
| Population Exposure Calculation       | NO-GO (BLOCKED) | Geodatabase missing |
+-------------------------------------------------------------------------------+
```

---

## 4. Minimum Conditions for Operational Promotion

Before any component of PRAVAAH can transition from an experimental research benchmark to an operational decision-support system, the following three conditions must be satisfied:

1. **Sub-Daily In-Situ Telemetry Ingestion:** Transition from 24h daily retrospective archives to real-time hourly telemetry for barrage releases, AWS rainfall, and river stage.
2. **Hybrid / Physics-Informed Extrapolation:** Adoption of hydrodynamic routing or hybrid models capable of linear extrapolation beyond historical training maximums ($> 4,105\,\text{m}^3/\text{s}$).
3. **Formal Institutional CWC Data Partnership:** Access to official continuous water-level observations at CWC Station 028-MDD under formal research protocol.
