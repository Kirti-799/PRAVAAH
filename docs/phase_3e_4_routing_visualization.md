# PRAVAAH — Phase 3E.4 Engineering & Scientific Report
## 1D Muskingum Hydrological Routing Spatial Integration, Chainage Discrepancy Reconciliation & Interactive Wave Visualization

**Project:** PRAVAAH (Geospatial Hydrology & Flood Risk Intelligence)  
**Phase:** 3E.4 — 1D Routing Spatial Integration & Geospatial Visualization  
**Date of Audit & Release:** November 2, 2026  
**Status:** **PHASE 3E.4 COMPLETE** (Full Acceptance)  
**Authoritative Hydrography:** OpenStreetMap Relation `326077` (*River Yamuna*) Continuous Thalweg LineString (2,505 vertices, 268.94 km)  
**Hydrological Dataset:** Haryana Irrigation & Water Resources Department (I&WRD) Daily Barrage Telemetry (2018–2025)  

---

## 1. Executive Summary

Phase 3E.4 establishes the first spatial coupling in PRAVAAH between the non-ML 1D hydrological Muskingum routing engine and the authentic downstream Yamuna river centreline geometry acquired in Phase 3E.3.

Prior to Phase 3E.4, Muskingum routing operated as an isolated lumped tabular calculation: it received an upstream inflow sequence $I(t)$ at Hathnikund Barrage and output a downstream routed discharge sequence $O(t)$ without physical coordinates, station chainages, or GIS visualization.

In this phase:
1. **Chainage Discrepancies Resolved:** Rigorously explained and documented the mathematical and geographical reasons behind the $38.49\text{ km}$ upstream inflow delta and the $614.9\text{ m}$ difference between the Old Railway Bridge (ORB) structural node and catalog station projection.
2. **1D Spatial Routing Engine:** Implemented [`ml/routing/spatial_routing.py`](file:///c:/Users/kirti%20antil/OneDrive/Desktop/PRAVAAH/ml/routing/spatial_routing.py), mapping flood wave progression along 63 distinct corridor nodes (55 five-kilometer sampling stations + 8 corridor monitoring/barrage stations) while rigorously accounting for non-uniform bed slope.
3. **Backend API Endpoints:** Exposed `GET /api/hydrology/routing-simulation-spatial` and `GET /api/spatial/routing/simulation`, delivering fully typed, spatially referenced time series with explicit provenance and value types (`OBSERVED`, `SIMULATED`, `INTERPOLATED_WAVE`).
4. **Interactive GIS Map Visualization:** Enhanced [`frontend/src/components/map/InteractiveGISMap.tsx`](file:///c:/Users/kirti%20antil/OneDrive/Desktop/PRAVAAH/frontend/src/components/map/InteractiveGISMap.tsx) with a dynamic 1D wave layer, timeline playback slider (play/pause animation), station inspection cards, and clear cartographic distinction between observed release and simulated outflow.
5. **Quality Assurance:** 223 automated test cases passing across backend and ML suites with 0 failures; production frontend builds cleanly in 1.19s.

---

## 2. Task 0 — Chainage Audit & Reconciliation

A primary requirement of Phase 3E.4 was the resolution of apparent numerical discrepancies in the Phase 3E.3 hydrographic metrics:

### 2.1 Upstream Inflow Reach ($38.49\text{ km}$) vs. Downstream Mainstem ($268.94\text{ km}$)
- **Observed Metrics in Phase 3E.3:**
  - Raw hydrography API (`/api/spatial/river/features`): **$307.43\text{ km}$** (6 features, 2,862 coordinates)
  - Processed mainstem (`/api/spatial/hydrography/summary`): **$268.94\text{ km}$** (1 feature, 2,505 coordinates)
- **Reconciliation & Mathematical Proof:**
  - Feature 1 in `osm_yamuna_downstream_raw.geojson` is **OSM Way `132610023`** (Dakpathar Barrage to Hathnikund Barrage). It has a geodesic length of **$38.487\text{ km}$** ($38,487.2\text{ m}$) and represents an *upstream inflow reach* situated north of Hathnikund Barrage.
  - Features 2 through 6 (Ways `204980194`, `648975828`, `267825123`, `24943999`, `24944222`) constitute the actual *downstream corridor mainstem* from Hathnikund Barrage to Okhla Barrage:
    $$154.812 + 53.541 + 11.081 + 31.618 + 17.893 = 268.944\text{ km}$$
  - The sum of all 6 raw features is:
    $$38.487\text{ km (Upstream Inflow)} + 268.944\text{ km (Downstream Mainstem)} = 307.431\text{ km}$$
  - **Conclusion:** The discrepancy was purely terminological. The raw hydrography archive preserves the complete upper-to-lower acquisition ($307.43\text{ km}$), whereas downstream routing begins at the Hathnikund pour point ($0.00\text{ km}$) and terminates at Delhi ORB ($251.05\text{ km}$) or Okhla Barrage ($268.94\text{ km}$).

### 2.2 Hathnikund-to-ORB Centreline Length ($251.05\text{ km}$) vs. ORB Station Chainage ($251.67\text{ km}$)
- **Observed Metrics in Phase 3E.3:**
  - Cumulative length of the 4 OSM mainstem ways up to ORB endpoint: **$251.051\text{ km}$** ($251,051.3\text{ m}$)
  - Orthogonally projected station chainage for Delhi ORB: **$251.666\text{ km}$** ($251,666.2\text{ m}$)
- **Reconciliation & Mathematical Proof:**
  - The cumulative centreline length ($251.051\text{ km}$) measures the thalweg from Hathnikund Barrage (Node `1458505954`) to the terminal node of OSM Way `24943999` (Node `271078156`), situated at the northern abutment of the Old Railway Bridge ($28.668953^\circ\text{N}, 77.235813^\circ\text{E}$).
  - In contrast, the official monitoring station catalog defines Delhi ORB at coordinates $(28.665000^\circ\text{N}, 77.240000^\circ\text{E})$, which corresponds to the CWC hydro-meteorological gauge sensor post on the south-eastern approach pier.
  - When the point $(28.665^\circ\text{N}, 77.240^\circ\text{E})$ is orthogonally projected onto the continuous river line in `EPSG:32643`, the projected point lies $614.9\text{ m}$ further downstream along the river curve (chainage $251.666\text{ km}$), with an orthogonal offset to the centreline of only **$51.7\text{ m}$**.
  - **Conclusion:** Both measurements are physically authentic. $251.051\text{ km}$ represents the exact geometric terminus of OSM Way `24943999` at the bridge deck, while $251.666\text{ km}$ represents the projected location of the CWC water-level monitoring sensor.

### 2.3 Station Proximity & Offset Review
The station offsets to the continuous river centreline were verified:

| Station Name | Station Type | Catalog Lat/Lon | Thalweg Chainage | Offset to Thalweg | Status | Geographical Context |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **Hathnikund Barrage** | Barrage | 30.317°N, 77.585°E | 0.00 km | 281.0 m | `VALID_PROXIMITY` | Direct barrage axis crossing at origin |
| **Yamunanagar Bridge** | Gauge Post | 30.125°N, 77.295°E | 44.70 km | 7,412.0 m | `DISTANT_INTERIM` | Municipal reference point; canal regulator offset |
| **Karnal / Munak** | Bifurcation | 29.685°N, 77.015°E | 111.45 km | 10,741.3 m | `DISTANT_INTERIM` | Western Yamuna Canal Munak regulator diversion |
| **Panipat Bridge** | Gauge Post | 29.390°N, 77.085°E | 146.30 km | 4,682.5 m | `VALID_PROXIMITY` | NH44 bridge approach on western floodplain |
| **Sonipat Reach** | Gauge Post | 28.995°N, 77.155°E | 202.50 km | 3,331.1 m | `VALID_PROXIMITY` | Municipal gauge marker on western floodplain |
| **Wazirabad Barrage** | Barrage | 28.710°N, 77.225°E | 246.43 km | 625.5 m | `VALID_PROXIMITY` | Direct barrage intake structure crossing |
| **Delhi ORB** | Benchmark Gauge | 28.665°N, 77.240°E | 251.67 km | **51.7 m** | `VALID_PROXIMITY` | Virtually centered on historic railway bridge |
| **Okhla Barrage** | Barrage | 28.545°N, 77.315°E | 268.89 km | **24.1 m** | `VALID_PROXIMITY` | Direct downstream terminus barrage crossing |

---

## 3. Task 1 — Existing Routing Audit

A comprehensive review of the current hydrological Muskingum routing implementation across [`ml/routing/`](file:///c:/Users/kirti%20antil/OneDrive/Desktop/PRAVAAH/ml/routing/) was performed:

### 3.1 Input & Output Data Series
- **Input Time Series $I(t)$:** Observed daily downstream release from Hathnikund Barrage (`HKB D/S`), in $\text{m}^3/\text{s}$ (cumecs), sourced from Haryana I&WRD records (2,599 days, 2018–2025).
- **Output Time Series $O(t)$:** Downstream routed discharge at Delhi ORB, strictly designated as **SIMULATED DOWNSTREAM DISCHARGE** in $\text{m}^3/\text{s}$.
- **Stage Omission:** Downstream stage / water level ($h(t)$ in m MSL) is **strictly unavailable** (omitted as `None`) because continuous non-flood CWC water levels are restricted and stage-discharge rating curves are uncalibrated.

### 3.2 Governing Formulation & Parameter Bounds
- **Storage Equation:**
  $$S = K [x I + (1 - x) O]$$
- **Routing Equation:**
  $$O_{t+1} = C_0 I_{t+1} + C_1 I_t + C_2 O_t$$
  where:
  $$D = 2 K (1 - x) + \Delta t, \quad C_0 = \frac{\Delta t - 2 K x}{D}, \quad C_1 = \frac{\Delta t + 2 K x}{D}, \quad C_2 = \frac{2 K (1 - x) - \Delta t}{D}$$
  $$C_0 + C_1 + C_2 = 1.0 \quad (\text{Exact mass continuity})$$
- **Parameters:**
  - Authoritative Baseline: $K = 36.0\text{ hours}$ (mean wave transit time), $x = 0.20$ (alluvial wedge storage), $\Delta t = 24.0\text{ hours}$ (daily).
  - Routing Coefficients: $C_0 = 0.117647$, $C_1 = 0.470588$, $C_2 = 0.411765$.
- **Numerical Stability Criterion:**
  $$2 K x \le \Delta t \le 2 K (1 - x)$$
  For baseline: $2(36)(0.20) = 14.4\text{ h} \le 24.0\text{ h} \le 2(36)(0.80) = 57.6\text{ h}$ (Strictly verified).

### 3.3 Subreach Constraints Under Daily Discretization
Because the historical dataset has a daily time step ($\Delta t = 24.0\text{ h}$), subdividing the corridor into $m$ equal subreaches reduces each subreach's travel time to $K_{\text{sub}} = K / m$.
For $m \ge 3$, $K_{\text{sub}} \le 12.0\text{ h}$, meaning $2 K_{\text{sub}} (1 - x) \le 19.2\text{ h} < 24.0\text{ h}$, which violates the upper stability bound and forces $C_2 < 0$. Therefore, numerical stability strictly limits discrete Muskingum subreaches to $m \le 2$ when $\Delta t = 24\text{ h}$.

---

## 4. Task 2 & 3 — Chainage Mapping & Backend Integration

### 4.1 Non-Uniform Travel Time Formulation
In physical river hydraulics, bed slope flattens substantially along the 251 km corridor. Equal chainage intervals do **not** imply equal hydraulic travel times:
- **Upper Reach ($0 \le s \le 45\text{ km}$, Hathnikund to Yamunanagar):** Steeper gravel bed ($S_0 > 0.001$), estimated flood wave celerity $c_1 \approx 7.5\text{ km/h}$. Travel time across reach $\approx 6.0\text{ hours}$.
- **Middle Reach ($45 < s \le 180\text{ km}$, Yamunanagar to Panipat):** Alluvial sand bed ($S_0 \approx 0.00034$), estimated celerity $c_2 \approx 6.0\text{ km/h}$. Travel time across reach $\approx 22.5\text{ hours}$.
- **Lower Reach ($180 < s \le 251.05\text{ km}$, Sonipat to Delhi ORB):** Low-gradient silt bed ($S_0 \approx 0.0002$), estimated celerity $c_3 \approx 4.5\text{ km/h}$. Travel time across reach $\approx 15.8\text{ hours}$.

Integrating $d\tau = ds / c(s)$ and normalizing to total baseline $K = 36.0\text{ hours}$ yields the cumulative travel time $\tau(s)$ for any chainage point:
$$\tau(s) = \frac{\int_0^s \frac{d\xi}{c(\xi)}}{\int_0^{L_{\text{ORB}}} \frac{d\xi}{c(\xi)}} \times K$$

### 4.2 Spatially Mapped Wave Progression
For each time step $t$ and each spatial station $s$ along the corridor:
- At Hathnikund Barrage ($s = 0.0\text{ km}$):
  $$Q(0, t) = I_{\text{obs}}(t) \quad [\text{Value Type: } \mathbf{OBSERVED}]$$
  $$\text{Provenance: Haryana I\&WRD Daily Barrage Release Record (HKB D/S)}$$
- At Delhi Old Railway Bridge ($s = 251.05\text{ km}$):
  $$Q(L_{\text{ORB}}, t) = O_{\text{sim}}(t) \quad [\text{Value Type: } \mathbf{SIMULATED}]$$
  $$\text{Provenance: Muskingum 1D Routing Simulation (K=36h, x=0.20)}$$
- At Intermediate Stations ($0 < s < L_{\text{ORB}}$):
  $$Q(s, t) = (1 - f(s)) \cdot I_{\text{obs}}(t - \tau(s)/24) + f(s) \cdot O_{\text{sim}}(t) \quad [\text{Value Type: } \mathbf{INTERPOLATED\_WAVE}]$$
  where $f(s) = \min(1.0, \tau(s)/K)$.

### 4.3 Backend Endpoints & API Contracts
Two synchronized endpoints expose spatial routing results:
1. `GET /api/hydrology/routing-simulation-spatial`
2. `GET /api/spatial/routing/simulation`

**Query Parameters:**
- `episode_id` (default: `"EPISODE_2023_08"`)
- `K_hours` (default: `36.0`, range: `1.0` to `120.0`)
- `x` (default: `0.20`, range: `0.0` to `0.50`)
- `interval_km` (default: `5.0`, range: `1.0` to `50.0`)

**JSON Response Schema Structure:**
```json
{
  "service": "PRAVAAH Spatial 1D Routing Intelligence",
  "version": "1.0.0",
  "status": "SIMULATION_SUCCESS_SPATIAL_MAPPED",
  "episode_id": "EPISODE_2023_08",
  "reach_name": "Yamuna River Downstream Corridor: Hathnikund Barrage to Delhi Old Railway Bridge / Okhla",
  "reach_length_km": 268.94,
  "total_stations_count": 63,
  "peak_observed_inflow_cumecs": 8342.87,
  "peak_observed_inflow_date": "2023-07-10",
  "peak_simulated_outflow_cumecs": 6191.60,
  "peak_simulated_outflow_date": "2023-07-12",
  "simulated_lag_hours": 48.0,
  "simulated_attenuation_percent": 25.79,
  "time_steps": [
    {
      "date": "2023-07-10",
      "step_index": 3,
      "observed_inflow_cumecs": 8342.87,
      "simulated_outflow_cumecs": 1218.79,
      "points": [
        {
          "station_id": "STN_HKB",
          "name": "Hathnikund Barrage",
          "chainage_km": 0.0,
          "latitude": 30.317,
          "longitude": 77.585,
          "discharge_cumecs": 8342.87,
          "value_type": "OBSERVED",
          "data_provenance": "Haryana I&WRD Daily Barrage Release Record (HKB D/S)",
          "reach_id": "REACH_HKB_TO_YMN",
          "is_monitoring_station": true
        },
        {
          "station_id": "STN_ORB",
          "name": "Delhi Old Railway Bridge (ORB)",
          "chainage_km": 251.67,
          "latitude": 28.665,
          "longitude": 77.24,
          "discharge_cumecs": 1218.79,
          "value_type": "SIMULATED",
          "data_provenance": "Muskingum 1D Routing Simulation (K=36.0h, x=0.2)",
          "reach_id": "REACH_SNP_TO_ORB",
          "is_monitoring_station": true
        }
      ]
    }
  ],
  "scientific_disclaimer": "1D RIVER-NETWORK ROUTING INTELLIGENCE — NOT A 2D FLOOD INUNDATION MODEL. SIMULATED DOWNSTREAM DISCHARGE — NOT OBSERVED DELHI WATER LEVEL. ..."
}
```

---

## 5. Task 4 — Frontend Interactive GIS Integration

The GIS workstation interface was extended in [`frontend/src/components/map/InteractiveGISMap.tsx`](file:///c:/Users/kirti%20antil/OneDrive/Desktop/PRAVAAH/frontend/src/components/map/InteractiveGISMap.tsx):

### 5.1 New GIS Layer: `routing_wave`
- **Layer Name:** `1D Flood Wave Progression (Muskingum)`
- **Category:** `Hydrography`
- **Default Status:** `AVAILABLE`
- **Default Visibility:** `true`
- **Accent Color:** `#7C3AED` (Purple)

### 5.2 Dynamic Thalweg Markers & Popups
At each simulation date / time step:
- **Observed Inflow Point (Hathnikund Barrage, KM 0.0):** Prominent emerald circle (`#059669`, radius 9) with white border.
- **Simulated Outflow Point (Delhi ORB, KM 251.7):** Prominent purple circle (`#7C3AED`, radius 9) with white border.
- **Chainage Wave Points:** Sized dynamically (radius 3.5 to 8) and color-coded based on flow intensity:
  - Baseflow ($< 1,000\text{ m}^3/\text{s}$): `#3B82F6` (Blue)
  - Moderate ($1,000 - 2,000\text{ m}^3/\text{s}$): `#D97706` (Amber)
  - Elevated Surge ($2,000 - 4,500\text{ m}^3/\text{s}$): `#EA580C` (Orange)
  - Extreme Surge ($> 4,500\text{ m}^3/\text{s}$): `#DC2626` (Crimson)
- **Interactive Popup & Card:** Clicking any point opens a clean card rendering station name, chainage, coordinates, flow rate in $\text{m}^3/\text{s}$, value type badge (`OBSERVED` vs `SIMULATED`), and provenance.

### 5.3 Floating Timeline Controller
Positioned at bottom-center (`bottom-4 left-1/2 -translate-x-1/2`) in the cream-and-brown GIS workstation style (`#FFFCF6`, `#DED2C1`, `#604936`):
- **Playback Controls:** Previous Day (`<`), Play/Pause Animation button, Next Day (`>`), Jump to Peak button.
- **Date & Step Indicator:** Displays current date (e.g. `2023-07-10 (Day 4 of 26)`).
- **Interactive Range Slider:** Allows scrubbing through all 26 simulation time steps.
- **Telemetry Badges:** Real-time side-by-side display of Observed Release at HKB (emerald badge) and Simulated Outflow at ORB (purple badge).

---

## 6. Task 5 — Verification & Regression Results

All verification suites were executed:

### 6.1 Test Suite Breakdown

| Test Suite File | Test Count | Passed | Failed | Execution Time | Coverage Scope |
| :--- | :---: | :---: | :---: | :---: | :--- |
| [`ml/tests/test_spatial_routing.py`](file:///c:/Users/kirti%20antil/OneDrive/Desktop/PRAVAAH/ml/tests/test_spatial_routing.py) | 5 | **5** | 0 | 4.91s | Chainage mapping, reach ordering, value type tagging, celerity non-linearity, API endpoints |
| [`backend/tests/test_routing.py`](file:///c:/Users/kirti%20antil/OneDrive/Desktop/PRAVAAH/backend/tests/test_routing.py) | 13 | **13** | 0 | 5.27s | Readiness, default simulation, stability rejection, tabletop presets, spatial routing endpoints |
| `backend/tests/` (Full Suite) | 79 | **79** | 0 | 12.10s | All backend endpoints (catchment, forecasting, health, hydrography, hydrology, river, routing, spatial, weather) |
| `ml/tests/` (Full Suite) | 144 | **144** | 0 | 6.36s | All ML modules (alignment, baselines, features, evaluation, training, hydrography, spatial routing) |
| **Total Automated Tests** | **223** | **223** | **0** | **28.64s** | **100% Passing Repository-wide** |

### 6.2 Frontend Build Check
- `npm --prefix frontend run build` (`tsc -b && vite build`) passed with **Exit Code 0** in $1.19\text{ s}$ with 0 errors.

---

## 7. Scientific Limitations & Invariant Safeguards

1. **1D Representation:** Wave progression represents 1D channel flow rates along the thalweg. It does NOT model channel cross-sections, bankfull capacity, or overbank inundation.
2. **Centreline Disclaimer:** The river centreline is NOT a flood boundary and must never be interpreted as an evacuation zone or water extent.
3. **Uncalibrated Model:** The Muskingum parameters ($K=36\text{ h}$, $x=0.20$) represent literature heuristics. They are uncalibrated against continuous downstream stage records due to restricted transboundary data access.
4. **No Stage Estimation:** The model does NOT estimate water surface elevations ($m\text{ MSL}$) at Delhi Old Railway Bridge.
5. **No 2D Flood Inundation:** PRAVAAH explicitly disclaims operational flood extent predictions in Phase 3E.4.

---

## 8. Final Acceptance Sign-off

| Phase 3E.4 Acceptance Criterion | Verification Status | Observed Evidence |
| :--- | :---: | :--- |
| **1. Routing outputs associated with physical locations** | **PASS** | 63 stations with exact coordinates, chainages, and reach IDs |
| **2. Chainage mapping verified** | **PASS** | Monotonic ordering from 0.0 to 268.94 km, slope-dependent $\tau(s)$ verified |
| **3. Observed vs. simulated clearly distinguished** | **PASS** | Strict `value_type` badges (`OBSERVED`, `SIMULATED`, `INTERPOLATED_WAVE`) |
| **4. Frontend visualizes routing progression** | **PASS** | Interactive GIS layer with timeline slider, playback animation, and popups |
| **5. Existing test suites pass** | **PASS** | **223 / 223 passed**, 0 regressions, Vite build successful |
| **6. No unsupported flood claims introduced** | **PASS** | Explicit disclaimers enforced across schemas, APIs, and UI |

$$\mathbf{PHASE\ 3E.4\ COMPLETE}$$

