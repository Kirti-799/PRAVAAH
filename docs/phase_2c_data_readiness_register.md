# PRAVAAH Phase 2C-A: Comprehensive Data-Readiness Register

**Project:** PRAVAAH — Predictive Risk Assessment and Vulnerability Analysis for Adaptive Assistance & Humanitarian Response  
**Document:** Data-Readiness Register & Provenance Audit  
**Phase:** 2C-A  
**Date:** October 19, 2026  

---

## 1. Register Overview & Governance Principles

This register provides the definitive inventory of hydrometeorological, hydrodynamic, geospatial, exposure, and response planning datasets required across all phases of the PRAVAAH platform.

### Scientific Data Integrity Safeguards:
1. **No Data Fabrication:** Datasets not present in the repository must be explicitly marked as `UNAVAILABLE` or `BLOCKED`.
2. **Provenance Traceability:** Every dataset must record its authoritative issuing agency, physical measurement methodology, spatial bounds, and temporal resolution.
3. **Data Type Classification:** Every variable must be classified into:
   - `MEASURED`: Directly recorded by an in-situ physical instrument (e.g. staff gauge, radar, rain gauge).
   - `DERIVED`: Numerically calculated from measured observations via documented scientific formulas.
   - `ASSUMED / HEURISTIC`: Calibrated, literature-standard, or synthetic parameter values.
   - `UNAVAILABLE / BLOCKED`: Data not released, restricted under government policy, or unacquired.

---

## 2. Comprehensive Data-Readiness Register

### Category A: Downstream Delhi River Observations (Ground-Truth Target)

| Dataset Name | Primary Purpose | Current Repository Status | Source & Provenance | Resolution & Coverage | Data Classification | Acquisition Restrictions & Limitations | Dependent Capability |
| :--- | :--- | :---: | :--- | :--- | :---: | :--- | :--- |
| **CWC Station 028-MDD (Delhi ORB) Continuous Stage** | Ground-truth target for Delhi flood-stage prediction ($H_{delhi}(t)$) | **BLOCKED / UNAVAILABLE** | Central Water Commission (CWC), Ministry of Jal Shakti | Hourly or daily morning reading; Point ($28.6625^\circ\text{N}, 77.2483^\circ\text{E}$) | `UNAVAILABLE` | **Transboundary Data Policy:** Non-monsoon and non-flood water levels are restricted and not published via open APIs. Historical non-flood records withheld. | **Delhi Flood-Stage Forecasting; Danger-Mark Breach Prediction** |
| **Authoritative Stage Benchmarks (Delhi ORB)** | Hazard categorization thresholds | **VERIFIED (Documented)** | CWC Flood Forecasting Network / DDMA | Constant thresholds: Warning ($204.50\,\text{m}$), Danger ($205.33\,\text{m}$), HFL ($208.66\,\text{m}$) | `MEASURED` (Standard Benchmark) | Fixed official river datum values; verified from CWC 2023 flood bulletins. | **Flood Hazard Classification** |
| **Stage-Discharge Rating Curve (028-MDD)** | Converting routed river discharge into stage elevation | **UNAVAILABLE** | CWC Upper Yamuna Division | Seasonal rating curves $H = f(Q)$ | `UNAVAILABLE` | Aggradation and heavy siltation over decades has altered riverbed profile; rating curve shifts continuously and is unpublished. | **Hydraulic Water Level Conversion** |

---

### Category B: Upstream Hydrology & River Routing

| Dataset Name | Primary Purpose | Current Repository Status | Source & Provenance | Resolution & Coverage | Data Classification | Acquisition Restrictions & Limitations | Dependent Capability |
| :--- | :--- | :---: | :--- | :--- | :---: | :--- | :--- |
| **Hathnikund Downstream Release (`HKB D/S`)** | Upstream boundary discharge input; Phase 2 forecasting target | **VERIFIED (Active)** | Haryana Irrigation & Water Resources Dept (I&WRD) | Daily morning summary (08:00 IST); 2018–2024 ($N=2,491$) | `MEASURED` | 66 unobserved dates in 7 years; sub-daily (hourly) spillway release logs not available in public portal. | **Upstream 24h Forecasting; Downstream Flood Wave Routing** |
| **Hathnikund Upstream Inflow (`HKB U/S`)** | Runoff response predictor; canal diversion accounting | **VERIFIED (Active)** | Haryana I&WRD / NWDP | Daily morning summary (08:00 IST); 2018–2024 ($N=2,484$) | `MEASURED` | 7 unobserved dates in dry season; represents combined flow from Yamuna, Tons, Giri, and Asan rivers. | **Feature Engineering; Inflow-to-Release Accounting** |
| **Wazirabad & Okhla Barrage Operations** | Downstream backwater and water extraction boundary conditions | **UNAVAILABLE** | Delhi Jal Board (DJB) / Haryana I&WRD | Daily gate openings and pond levels in Delhi NCT reach | `UNAVAILABLE` | Gated municipal water supply logs; not available via public feeds. | **Urban Reach Hydrodynamic Simulation** |
| **Yamuna Reach Bathymetry & Cross-Sections** | 1D/2D hydrodynamic wave propagation modeling | **UNAVAILABLE** | Survey of India / CWC / CPCB river surveys | 180 km reach from Hathnikund to Delhi | `UNAVAILABLE` | Detailed bathymetric surveys are sensitive defense/hydrology assets; uncalibrated Muskingum currently assumes uniform prismatic reach. | **Physics-Based Flood Wave Routing** |
| **Channel Roughness ($n$) & Wave Speed ($K$)** | Muskingum routing parameters ($K, X$) | **EXPERIMENTAL PROTOTYPE** | Literature estimates for large alluvial sand-bed rivers | Uniform reach-averaged parameters ($K=48\,\text{h}, X=0.25$) | `ASSUMED / HEURISTIC` | Uncalibrated against real downstream discharge gauges; assumes linear storage relationship without floodway spill. | **Scenario Tabletop Routing Simulations** |

---

### Category C: Rainfall & Inundation Observations

| Dataset Name | Primary Purpose | Current Repository Status | Source & Provenance | Resolution & Coverage | Data Classification | Acquisition Restrictions & Limitations | Dependent Capability |
| :--- | :--- | :---: | :--- | :--- | :---: | :--- | :--- |
| **IMD 0.25° Gridded Daily Rainfall** | Antecedent basin wetness predictors; historical storm analysis | **VERIFIED (Active)** | India Meteorological Department (IMD) Pune | Daily 24h accumulation ending 08:30 IST; 91 grid cells covering Yamuna basin | `MEASURED / SPATIALLY DERIVED` | **Latency:** Published as post-processed archive with 24–48h publication latency. Cannot resolve cloudbursts occurring contemporaneously on forecast issue day. | **Antecedent Precipitation Modeling; Historical Event Audit** |
| **Real-Time Automated Weather Stations (AWS)** | Real-time rainfall telemetry for early warning | **UNAVAILABLE** | IMD Regional Meteorological Centre (RMC) New Delhi | Hourly/sub-daily station telemetry | `UNAVAILABLE` | Real-time API credentials not integrated into repository. | **Operational Early Warning; Flash Surge Detection** |
| **Doppler Weather Radar (DWR Delhi)** | High-resolution storm tracking and nowcasting | **UNAVAILABLE** | IMD DWR Mausam Portal (Palam & Lodhi Road radars) | 10-minute polar volume scans; 250 km radius | `UNAVAILABLE` | Radar reflectivity matrices ($Z-R$ relationship) not archived or ingested in project. | **1–6h Convective Rainfall Nowcasting** |
| **Satellite Flood Inundation Extent (SAR)** | Empirical validation of flood inundation maps | **UNAVAILABLE** | Sentinel-1 SAR (Copernicus) / RISAT-1 / NRSC | 10–20 m spatial resolution; 6–12 day repeat pass | `UNAVAILABLE` | Cloud-penetrating C-band SAR scenes for July 2023 catastrophe not yet downloaded or segmented in repository. | **Validation of Flood Extent & Exposure Models** |

---

### Category D: Geospatial Exposure & Emergency Response Planning

| Dataset Name | Primary Purpose | Current Repository Status | Source & Provenance | Resolution & Coverage | Data Classification | Acquisition Restrictions & Limitations | Dependent Capability |
| :--- | :--- | :---: | :--- | :--- | :---: | :--- | :--- |
| **Digital Elevation Model (DEM)** | Floodplain topography and candidate safe-zone elevation checks | **UNAVAILABLE IN REPO** | SRTM 30m / NASADEM / ALOS PALSAR 12.5m | 30m grid covering Yamuna corridor | `UNAVAILABLE` | High-resolution LiDAR (1–2m) required for urban floodwalls is unavailable; 30m DEM has vertical error of $\pm 5\,\text{m}$. | **Topographic Safe-Zone Screening** |
| **High-Resolution Population Rasters** | Quantifying population exposure in inundated zones | **UNAVAILABLE IN REPO** | WorldPop / Census of India 2011 gridded | 100m raster or ward-level aggregations for Delhi NCT | `UNAVAILABLE` | Census data is from 2011 (15 years outdated); informal Yamuna floodplain settlements (*jhuggi-jhopri* clusters) are undercounted. | **Population Exposure Assessment** |
| **Critical Infrastructure Geodatabase** | Identifying vulnerable hospitals, power stations, bridges | **UNAVAILABLE IN REPO** | OpenStreetMap (OSM) / Delhi Geo-Spatial Data Infra (GSDL) | Vector point and polygon layers | `UNAVAILABLE` | OSM vector extraction not yet executed in data pipeline. | **Infrastructure Exposure Analysis** |
| **Designated Relief Shelters & Facilities** | Authoritative destination safe zones for evacuation | **UNAVAILABLE IN REPO** | Delhi Disaster Management Authority (DDMA) | Official shelter list with capacity, food, and medical status | `UNAVAILABLE` | Authoritative DDMA GIS layer not acquired; candidate safe zones cannot be called "verified shelters". | **Safe-Zone & Evacuation Planning** |
| **Road Network Graph & Inundation Passability** | Evacuation route calculation and accessibility analysis | **UNAVAILABLE IN REPO** | OpenStreetMap (OSM) Overpass API | Vector road centerline graph with bridge elevations | `UNAVAILABLE` | Road network graph not built; dynamic road water-depth passability thresholds not modeled. | **Evacuation Route Support** |

---

## 3. Immediate Data Blockers & Mitigation Pathways

```
[Target Gauge 028-MDD Stage Missing] ──> BLOCKS: Delhi River Stage Prediction (m MSL)
                                    └──> BLOCKS: Delhi Flood Probability (%)
                                    └──> BLOCKS: Danger Mark Breach Alerting

[Riverbed Bathymetry Missing]        ──> BLOCKS: Calibrated Hydrodynamic Routing
                                    └──> LIMITS: Routing to Uncalibrated Muskingum Prototype

[Sub-Daily AWS Telemetry Missing]    ──> BLOCKS: Real-Time Early Warning (< 24h lead time)
                                    └──> LIMITS: Forecasting to Tabular Daily Models

[Shelter/Road Graph Missing]         ──> BLOCKS: Automated Evacuation Routing
                                    └──> LIMITS: Safe-Zones to Topographic Screening
```
