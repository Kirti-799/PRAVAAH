# PRAVAAH — Phase 3E.1 Geospatial Integration Audit

**Document ID:** `docs/phase_3e_1_geospatial_integration_audit.md`  
**Execution Date:** 2026-11-02  
**Target Scope:** Comprehensive integration audit across Frontend, Backend, Spatial Data, Hydrology, and External APIs.  
**Phase Context:** Pre-implementation architectural audit before beginning Phase 3E.2 unified geospatial intelligence.

---

## 1. Executive Summary

Phase 3A through Phase 3D.3.3 established individual core capabilities:
- **Phase 3A:** Spatial infrastructure, study extent bounding contracts, and DEM integrity engine.
- **Phase 3B:** Downstream river hydrography validator, NetworkX topological graph engine, and chainage stations.
- **Phase 3C:** Interactive Leaflet GIS workstation, multi-basemap catalog, and Open-Meteo weather integration.
- **Phase 3D (3D.1 – 3D.3.3):** Copernicus GLO-30 mosaic acquisition, Priority-Flood terrain conditioning, authentic Hathnikund catchment delineation ($11,366.04\text{ km}^2$), D8 drainage network extraction, and 20-node catchment spatial rainfall intelligence.

**Core Audit Finding:** While each geospatial and hydrological subsystem functions reliably in isolation, they currently operate in functional silos.
1. The **frontend map** displays catchment boundaries, drainage lines, monitoring stations, and spatial rainfall nodes, but **does not visually render the physical DEM elevation surface** or link downstream routing simulations to map features.
2. The **backend services** compute live catchment rainfall accumulations and antecedent precipitation indices, but **do not feed these spatial features into the ML discharge forecasting model**.
3. The **downstream river corridor vector layer** (`main_yamuna`) is empty on the map because `data/raw/spatial/hydrography/` lacks a vector centerline shapefile/GeoJSON.
4. **External API adapters** for IMD, NASA GPM, and CWC exist as prepared architectural shells, but only Open-Meteo is live.

---

## 2. Frontend Subsystem Audit

### 2.1 Workspace Architecture and View Switching
* **Component:** `frontend/src/components/map/GeospatialWorkspace.tsx`
* **View Modes:**
  * `map`: Displays `InteractiveGISMap.tsx` with full Leaflet canvas and floating layer controls.
  * `weather`: Displays `WeatherWorkspace.tsx` with current atmospheric metrics and 7-day hourly NWP forecast time series.
  * `spatial`: Displays `SpatialDataPanel.tsx` with tabbed controls for Upstream Catchment (Phase 3D), River Hydrography (Phase 3B), and Terrain Baseline (Phase 3A).
* **Navigation Synchrony:** The top header and sidebar (`Sidebar.tsx`) synchronize `Overview`, `Weather Intelligence`, and `Spatial Infrastructure`. Non-functional modules (`Risk Analysis`, `Impact Assessment`, `Shelters & Routes`, `Scenario Analysis`) trigger `PlannedModuleModal.tsx`.

### 2.2 Spatial Layers Inventory on Leaflet Map
Inspected in `frontend/src/components/map/InteractiveGISMap.tsx`:

| Layer ID | Name | Category | Hardcoded Status | Actual Runtime Status | Rendering Implementation in JSX |
| :--- | :--- | :---: | :---: | :---: | :--- |
| `study_bounds` | Study Corridor Boundary | Boundary | `AVAILABLE` | Operational | Rendered as dashed `<Rectangle>` |
| `upstream_catchment` | Upstream Catchment Boundary | Boundary | `AVAILABLE` | Operational | Rendered as purple dashed `<GeoJSON>` ($11,366\text{ km}^2$) |
| `corridor_stations` | Monitoring & Barrage Stations | Boundary | `AVAILABLE` | Operational | Rendered as 7 custom circular `<Marker>` pins |
| `catchment_drainage` | Catchment Drainage Network | Hydrography | `AVAILABLE` | Operational | Rendered as blue `<GeoJSON>` (199 stream reaches) |
| `catchment_rainfall_grid` | Spatial Rainfall Grid | Meteorology | `AVAILABLE` | Operational | Rendered as 20 colored `<CircleMarker>` nodes |
| `main_yamuna` | Main Yamuna River Centerline | Hydrography | `AVAILABLE` | **UNAVAILABLE** | Gracefully disabled: backend returns `features: []` |
| `dem_elevation` | Copernicus DEM GLO-30 Mosaic | Terrain | `AVAILABLE` | **NOT RENDERED** | Layer toggle exists in drawer, but **zero JSX rendering code** |
| `terrain_slope` | Topographical Slope Map | Terrain | `AVAILABLE` | **NOT RENDERED** | Layer toggle exists in drawer, but **zero JSX rendering code** |
| `tributaries` | Tributaries (Hindon, Tons, etc.) | Hydrography | `UNAVAILABLE` | Unavailable | Disabled with guardrail badge |
| `canals` | Canals (WJC & EJC Off-takes) | Hydrography | `UNAVAILABLE` | Unavailable | Disabled with guardrail badge |
| `drains` | Drains & Minor Waterways | Hydrography | `UNAVAILABLE` | Unavailable | Disabled with guardrail badge |
| `embankments` | Embankments & Flood Bunds | Hydrography | `UNAVAILABLE` | Unavailable | Disabled with guardrail badge |
| `rainfall_obs` | Rainfall Observations (IMD) | Meteorology | `UNAVAILABLE` | Unavailable | Disabled with guardrail badge |
| `admin_bounds` | Administrative Boundaries | Exposure | `UNAVAILABLE` | Unavailable | Disabled with guardrail badge |
| `pop_exposure` | Population Exposure Grid | Exposure | `UNAVAILABLE` | Unavailable | Disabled with guardrail badge |
| `shelters` | Evacuation Shelters | Exposure | `UNAVAILABLE` | Unavailable | Disabled with guardrail badge |

### 2.3 Frontend Backend Endpoint Consumption
The frontend currently calls the following 26 backend endpoints across its services:
* **Spatial & Catchment:**
  * `GET /api/spatial/inventory`
  * `GET /api/spatial/study-area`
  * `GET /api/spatial/dem/status`
  * `GET /api/spatial/terrain/summary`
  * `GET /api/spatial/river/features`
  * `GET /api/spatial/river/status`
  * `GET /api/spatial/hydrography/status`
  * `GET /api/spatial/hydrography/chainage`
  * `GET /api/spatial/catchment/status`
  * `GET /api/spatial/catchment/summary`
  * `GET /api/spatial/catchment/geometry`
  * `GET /api/spatial/catchment/drainage`
* **Rainfall & Weather:**
  * `GET /api/rainfall/status`
  * `GET /api/rainfall/catchment/summary`
  * `GET /api/weather/status`
  * `GET /api/weather/locations`
  * `GET /api/weather/basemap/config`
  * `GET /api/weather/current`
  * `GET /api/weather/forecast`
  * `POST /api/weather/refresh`
* **Hydrology & Forecasting:**
  * `GET /api/hydrology/summary`
  * `GET /api/hydrology/events`
  * `GET /api/hydrology/routing-readiness`
  * `GET /api/hydrology/routing-simulation`
  * `GET /api/forecasting/readiness`
  * `GET /api/forecasting/model-status`
  * `GET /api/forecasting/sample-forecast`
  * `GET /api/health`

### 2.4 Frontend Disconnections & Missing Module Connections
1. **Routing Simulation Isolated in Sidebar:** `TabletopScenarioWorkstation.tsx` runs Muskingum routing simulations, but its outputs (peak travel time, downstream hydrographs, warning thresholds) are confined to the sidebar. They are **not projected onto the map** or linked to the corridor stations.
2. **Click-to-Inspect Limited to Weather:** Clicking anywhere on the map or on monitoring stations dispatches coordinates strictly to `WeatherWorkspace.tsx`. There is no mechanism to query local terrain elevation, slope, or upstream contributing area at clicked points.
3. **Missing Raster Tile Server:** Although authentic Copernicus DEM rasters and slope matrices exist on disk, Leaflet cannot render them because no backend XYZ tile server or WMS/COG endpoint exists.

---

## 3. Backend Subsystem Audit

### 3.1 Spatial Services
* **`app/services/spatial.py` (`SpatialService`):**
  * Provides catalog inventory, rectangular study extent definitions, DEM validation reports, and terrain slope calculations.
  * Scans `data/raw/spatial/dem/` and `data/raw/spatial/hydrography/`.
  * Implements strict path-traversal sanitization.
* **`app/services/catchment_service.py` (`CatchmentService`):**
  * Exposes the delineated Hathnikund catchment boundary GeoJSON (`hathnikund_upstream_catchment.geojson`) and stream network (`hathnikund_drainage_network.geojson`).
  * Employs lazy on-disk artifact loading with fallback to `CatchmentDelineator`.
  * Caches metadata in memory after initial read.

### 3.2 Weather & Rainfall Services
* **`app/services/weather_service.py` (`WeatherService`):**
  * Ingests Open-Meteo forecasts for single coordinates.
  * Implements in-memory dictionary TTL caching (`DEFAULT_TTL_SECONDS = 900.0` / 15 minutes).
  * Enforces coordinate bounding box validation around the Yamuna corridor ($28.25^\circ\text{ N} - 30.65^\circ\text{ N}, 76.60^\circ\text{ E} - 77.85^\circ\text{ E}$).
* **`app/services/rainfall_service.py` (`RainfallService`):**
  * Coordinates concurrent multi-point queries across 20 elevational sampling nodes in the Hathnikund basin.
  * Ingests 14-day antecedent daily precipitation sums and computes API-3, API-7, and API-14 moisture decay indices ($k=0.85$).
  * Implements in-memory TTL caching (15 minutes).

### 3.3 Hydrological & Routing Services
* **`app/services/hydrology.py` (`HydrologyService`):**
  * Reads processed historical daily discharge CSV (`haryana_hathnikund_discharge_daily_2018_2025.csv`).
  * Computes distribution percentiles (p50, p90, p95, p99, max) and audits data completeness.
* **`app/services/routing.py` (`RoutingService`):**
  * Audits 8 physical hydraulic criteria (reach slope, cross-sections, roughness, lateral inflows, barrage operations, etc.) and correctly reports hydrodynamic modeling as blocked.
  * Implements parameter-explicit experimental Muskingum routing ($K=18.0\text{ h}, X=0.25$) across 3 sub-reaches for tabletop historical scenario exploration.

---

## 4. Spatial Data Inventory & Provenance

| Dataset Category | File Path | Format | Dimensions / Features | CRS | Coverage / Extent | Provenance | Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Raw DEM Tile 1** | `data/raw/spatial/dem/Copernicus_DSM_COG_10_N30_00_E077_00_DEM.tif` | GeoTIFF | 3,600 × 3,600 | EPSG:4326 | $30^\circ-31^\circ\text{ N}, 77^\circ-78^\circ\text{ E}$ | Copernicus GLO-30 (ESA/Airbus) | **Verified** |
| **Raw DEM Tile 2** | `data/raw/spatial/dem/Copernicus_DSM_COG_10_N30_00_E078_00_DEM.tif` | GeoTIFF | 3,600 × 3,600 | EPSG:4326 | $30^\circ-31^\circ\text{ N}, 78^\circ-79^\circ\text{ E}$ | Copernicus GLO-30 (ESA/Airbus) | **Verified** |
| **Raw DEM Tile 3** | `data/raw/spatial/dem/Copernicus_DSM_COG_10_N31_00_E077_00_DEM.tif` | GeoTIFF | 3,600 × 3,600 | EPSG:4326 | $31^\circ-32^\circ\text{ N}, 77^\circ-78^\circ\text{ E}$ | Copernicus GLO-30 (ESA/Airbus) | **Verified** |
| **Raw DEM Tile 4** | `data/raw/spatial/dem/Copernicus_DSM_COG_10_N31_00_E078_00_DEM.tif` | GeoTIFF | 3,600 × 3,600 | EPSG:4326 | $31^\circ-32^\circ\text{ N}, 78^\circ-79^\circ\text{ E}$ | Copernicus GLO-30 (ESA/Airbus) | **Verified** |
| **Processed DEM Mosaic** | `data/processed/spatial/dem/upstream_yamuna_dem_mosaic.tif` | GeoTIFF | 7,200 × 7,200 | EPSG:4326 | $30^\circ-32^\circ\text{ N}, 77^\circ-79^\circ\text{ E}$ | Mosaicked Copernicus GLO-30 | **Verified** |
| **Conditioned DEM** | `data/processed/spatial/catchment/hathnikund_conditioned_dem.tif` | GeoTIFF | 1,200 × 1,200 | EPSG:4326 | $30^\circ-32^\circ\text{ N}, 77^\circ-79^\circ\text{ E}$ | Priority-Flood conditioned 6" grid | **Verified** |
| **D8 Flow Direction** | `data/processed/spatial/catchment/hathnikund_flow_direction.tif` | GeoTIFF | 1,200 × 1,200 | EPSG:4326 | $30^\circ-32^\circ\text{ N}, 77^\circ-79^\circ\text{ E}$ | D8 + BFS Flat Routed raster | **Verified** |
| **Flow Accumulation** | `data/processed/spatial/catchment/hathnikund_flow_accumulation.tif` | GeoTIFF | 1,200 × 1,200 | EPSG:4326 | $30^\circ-32^\circ\text{ N}, 77^\circ-79^\circ\text{ E}$ | Topological DAG accumulation | **Verified** |
| **Watershed Polygon** | `data/processed/spatial/catchment/hathnikund_upstream_catchment.geojson` | GeoJSON | 1 Polygon, 2,217 pts | EPSG:4326 | Area: $11,366.04\text{ km}^2$ | Delineated D8 Watershed Boundary | **Verified** |
| **Drainage Network** | `data/processed/spatial/catchment/hathnikund_drainage_network.geojson` | GeoJSON | 199 LineStrings | EPSG:4326 | Length: $1,521.87\text{ km}$ | Extracted Contributing Streams | **Verified** |
| **Raw Downstream River**| `data/raw/spatial/hydrography/` | Directory | Empty (`.gitkeep`) | N/A | Hathnikund to Delhi ORB reach | Awaiting CWC / OSM Ingestion | **MISSING** |
| **Raw IMD Gridded Rainfall**| `data/raw/rainfall/gridded/ind2018_rfp25.grd` to `ind2024_rfp25.grd` | Binary float32 | 135 × 129 daily grids | EPSG:4326 | National India Coverage (0.25°) | IMD National Climate Centre | **Offline Archive** |
| **Processed Discharge** | `data/processed/hydrological/haryana_hathnikund_discharge_daily_2018_2025.csv` | CSV | 2,781 rows | Tabular | Hathnikund Barrage U/S & D/S | Haryana Irrigation Department | **Verified** |

---

## 5. Hydrological Integration & Data Schema Alignment

### 5.1 Common Spatial Interface
* **Spatial Reference Alignment:** All spatial vectors and rasters currently in the repository (catchment boundary, stream network, monitoring stations, rainfall grid, and study corridor bounding box) strictly adhere to **EPSG:4326 (WGS 84)**. No datum mismatches exist.
* **Projection Contracts:** Metric distance and area calculations consistently project to **EPSG:32643 (UTM Zone 43N)** for reach lengths or **Albers Equal-Area (`+proj=aea +lat_1=30.0 +lat_2=32.0 +lat_0=31.0 +lon_0=77.8`)** for watershed areas.

### 5.2 Hydrological Coupling Deficits
1. **Live Rainfall to ML Forecasting Gap:**
   * The Random Forest discharge model (`hathnikund_rf_v1`) expects 11 input features derived from daily rainfall: `discharge_upstream_m3s_lag1`, `rainfall_lag1_mm`, `rainfall_lag2_mm`, `rainfall_3d_sum_mm`, `rainfall_7d_sum_mm`, etc.
   * Currently, the live spatial rainfall service (`/api/rainfall/catchment/summary`) computes 20-node basin-averaged rainfall and API indices, but **there is no adapter connecting these live values into the model inference pipeline** (`/api/forecasting/predict`).
2. **Temporal Resolution Disconnect:**
   * Open-Meteo live rainfall operates in **hourly UTC/IST** steps.
   * Historical IMD gridded rainfall operates in **24-hour accumulations ending at 08:30 IST**.
   * Hathnikund discharge records are reported as **daily morning gauge snapshots**.
   * To achieve true predictive integration, an hourly-to-daily rolling accumulator matching the 08:30 IST window is required.
3. **Absence of Catchment Inflow Transfer Function:**
   * The tabletop simulation tool routes discharge starting from Hathnikund Barrage ($Q_{in} \rightarrow Q_{out}$), but does not model the transformation of upstream catchment rainfall into barrage inflow ($P_{catchment} \rightarrow Q_{Hathnikund}$).

---

## 6. External Integrations Status

| External Integration | Provider / Source | Protocol / Format | Authentication | Operational Status | Limitations / Blockers |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Open-Meteo Weather** | Open-Meteo GmbH | HTTPS REST (JSON) | None (Public) | **OPERATIONAL** | NWP forecast downscaled; rate-limited to 10k calls/day |
| **Open-Meteo Spatial Rainfall** | Open-Meteo GmbH | Concurrent HTTPS REST | None (Public) | **OPERATIONAL** | 20 coordinates batched concurrently; 15-min TTL cache |
| **OpenStreetMap Tiles** | OSM Foundation | HTTPS Tile Server (PNG) | None (Public) | **OPERATIONAL** | Standard cartographic basemap; client-side browser caching |
| **Carto Positron Tiles** | CARTO | HTTPS Tile Server (PNG) | None (Public) | **OPERATIONAL** | Clean basemap alternative |
| **OpenTopoMap Tiles** | OpenTopoMap | HTTPS Tile Server (PNG) | None (Public) | **OPERATIONAL** | Topographical relief basemap alternative |
| **IMD Gridded Rainfall** | India Meteorological Dept | Binary `.GRD` direct read | None (Offline) | **OFFLINE ARCHIVE ONLY** | No public real-time REST API; static archives (2018–2024) |
| **NASA GPM IMERG** | NASA GES DISC / GSFC | HTTPS / OPeNDAP (HDF5) | Earthdata OAuth2 | **BLOCKED** | Prepared adapter requires `EARTHDATA_TOKEN`; unauthenticated calls return 401 |
| **CWC / India-WRIS Gauges**| Central Water Commission | Prepared class interface | Institutional | **NOT IMPLEMENTED** | No open REST API exists; raises `NotImplementedError` |

---

## 7. Integration Gap Analysis Table

| Component | Existing Implementation | Data Availability | API Availability | Frontend Status | Missing Work | Recommended Next Action (Phase 3E) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Catchment Boundary** | GeoJSON polygon ($11,366\text{ km}^2$) derived from Copernicus DEM | Available on disk | `GET /api/spatial/catchment/geometry` | Rendered on map | Text labels in popup still refer to 11,112 km² literature estimate | Harmonize popup metrics with verified 11,366 km² geometry |
| **Catchment Drainage** | 199 DEM-extracted reaches ($1,521\text{ km}$) | Available on disk | `GET /api/spatial/catchment/drainage` | Rendered on map | Streams lack reach naming/hierarchy in properties | Add tributary naming attributes to GeoJSON reaches |
| **Downstream River Centerline** | Schema and validator exist (`RiverNetworkValidator`) | **MISSING** in `data/raw/spatial/hydrography/` | `GET /api/spatial/river/features` returns `[]` | Disabled in layer drawer | Ingest verified OSM/CWC downstream river centerline | Generate verified centerline GeoJSON from study corridor bounds |
| **DEM Elevation Surface** | 7200×7200 GeoTIFF mosaic and 1200×1200 conditioned DEM | Available on disk | `GET /api/spatial/dem/status`, `terrain/summary` | Toggled in drawer but **not rendered** | No raster tile server exists to render DEM on Leaflet | Implement client-side Canvas DEM hypsometric renderer or XYZ tile endpoint |
| **Live Spatial Rainfall Grid** | 20-node elevational grid with 24h forecast & API-3 | Live via Open-Meteo | `GET /api/rainfall/catchment/summary` | Rendered on map with popups | Isolated from ML discharge forecasting | Build feature bridge feeding catchment rainfall into ML model |
| **ML Discharge Forecasting** | Trained Random Forest model (`hathnikund_rf_v1`) | Model artifacts on disk | `POST /api/forecasting/predict` | Sample forecast in sidebar | Not connected to live catchment rainfall | Implement real-time forecast endpoint using live spatial rainfall |
| **Routing & Tabletop Simulation** | Parameter-explicit 1D Muskingum routing | Historical episodes on disk | `POST /api/hydrology/tabletop-scenario` | Confined to sidebar panel | Simulated flood wave not visualized on map corridor | Render simulated wave arrival times on map chainage stations |
| **External Hydrometric Telemetry** | Prepared adapters for CWC, IMD, NASA GPM | Offline archives on disk | Health status endpoints only | Reflected in status disclaimers | Real-time CWC/IMD feeds require institutional access | Maintain explicit unavailability guardrails |

---

## 8. Recommended Implementation Sequence for Phase 3E.2 Onwards

```
[Phase 3E.1 Audit (Current)]
          │
          ▼
[Phase 3E.2: Hydro-Meteorological Feature Coupling]
  ├── Bridge 20-node live catchment rainfall & API-3/7/14 into ML forecasting pipeline
  ├── Implement auto-updating Hathnikund 24h discharge forecast from live spatial rainfall
  └── Align temporal accumulation windows (08:30 IST rolling sum)
          │
          ▼
[Phase 3E.3: Geospatial Map Integration & Tabletop Visualization]
  ├── Connect TabletopScenarioWorkstation to InteractiveGISMap
  ├── Animate / project downstream Muskingum flood wave along corridor chainage stations
  └── Display dynamic warning-level breach alerts at Delhi Old Railway Bridge
          │
          ▼
[Phase 3E.4: Downstream Corridor Vector Layer & DEM Hypsometry]
  ├── Ingest verified downstream Yamuna river centerline (Hathnikund to Delhi ORB)
  ├── Activate 'main_yamuna' layer on map
  └── Implement lightweight hypsometric raster overlay for the Copernicus DEM mosaic
          │
          ▼
[Phase 3E.5: Cryospheric Headwater Zoning (Transition to Phase 4)]
  ├── Extract elevation bands (>3,000m, >4,500m) for Yamunotri and Tons snowpack
  └── Prepare snowmelt runoff modeling foundation
```

---

## 9. Verification & Stop-Condition Acknowledgment

* **Source Code State:** Zero lines of existing source code modified.
* **Data State:** Zero files moved, renamed, deleted, or overwritten.
* **Git State:** All pre-existing working tree modifications and untracked files strictly preserved.
* **Next Action:** Await user review before commencing Phase 3E.2 implementation.

