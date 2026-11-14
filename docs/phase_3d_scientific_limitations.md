# Phase 3D.6 — Scientific Limitations & Operational Governance Register

**Project**: PRAVAAH (Predictive Risk Assessment and Vulnerability Analysis for Adaptive Assistance & Humanitarian Response)  
**Document**: Scientific Limitations, Data Constraints, and Regulatory Disclaimers for Phase 3D  
**Effective Date**: 2026-10-31

---

## 1. Domain Separation Guardrail

### Upstream Catchment vs. Downstream Corridor

| Dimension | Upstream Catchment (Phase 3D Focus) | Downstream Corridor (Phase 0–3C Focus) |
| :--- | :--- | :--- |
| **Geographic Scope** | Hathnikund upstream basin (11,112 km² across UK, HP, HR) | Hathnikund to Delhi ORB / Okhla (~220 km river reach) |
| **Primary Process** | Orographic precipitation, runoff generation, tributary inflow | Flood wave attenuation, channel routing, overbank inundation |
| **Dominant Rivers** | Tons, Giri, Pabbar, Yamunotri glaciated headwaters | Lower Yamuna trunk, Hindon confluence, storm drains |
| **Governing Equations**| Water balance, infiltration, D8 kinematic flow routing | 1D Saint-Venant, diffusive wave / Muskingum routing |
| **Danger Indicators** | Cloudburst rates, catchment mean rainfall, API saturation | River stage at Delhi ORB, embankment breach thresholds |

**Mandatory Guardrail**: Catchment boundaries MUST NOT be rendered or interpreted as downstream flood hazard polygons.

---

## 2. Terrain Data Limitations (Copernicus DEM GLO-30)

1. **Digital Surface Model (DSM) vs. Digital Terrain Model (DTM)**:
   Copernicus GLO-30 represents a Digital Surface Model derived from TanDEM-X interferometric radar (2011–2015). It includes tree canopy tops and buildings. In heavily forested valleys (e.g., Tons and Giri river gorges), the elevation surface may be 10–25 m higher than the true river bed.
2. **Channel Bathymetry Absence**:
   Interferometric radar does not penetrate water. The DEM contains no underwater channel bed geometry.
3. **Engineered Structures**:
   Small culverts, mountain road tunnels, and diversions are not automatically burned into the DEM without specialized hydro-enforcing.
4. **Static Elevation**:
   The DEM does not reflect ongoing post-2015 geomorphic alterations, landslide dam breaches, or recent debris deposition from extreme monsoon events (e.g., July 2023 disaster).

---

## 3. Hydrological Delineation Limitations

1. **Topographic Approximation**:
   A DEM-derived watershed reflects surface topography. It does not account for sub-surface karst conduits, groundwater aquifers, or seasonal springs.
2. **Artificial Off-Takes & Barrage Operations**:
   At Hathnikund Barrage, operational water allocation directs flow into the Western Yamuna Canal (WJC, capacity ~600 cumecs) and Eastern Yamuna Canal (EJC, capacity ~200 cumecs). The topographic watershed delineates natural runoff; operational gate rules are hydraulic controls outside the DEM domain.
3. **Snow & Glacier Dynamics**:
   Runoff from high-elevation glaciated peaks (>4,000 m MSL around Yamunotri and Bandarpunch) involves snowpack accumulation, temperature index ablation, and glacial melt, requiring dedicated cryospheric modules (scheduled for Phase 3E).

---

## 4. Meteorological & Precipitation Limitations

1. **Forecast vs. Observation Separation**:
   Open-Meteo multi-point values represent numerical weather prediction (NWP) model forecasts. They are **not** real-time radar or ground rain gauge observations.
2. **IMD Data Availability Gating**:
   IMD 0.25° gridded rainfall data is an official ground-gauge interpolated observational product. Because IMD does not provide an open real-time unauthenticated REST API, this product operates strictly in offline batch ingestion mode.
3. **NASA GPM IMERG Token Authentication**:
   NASA GPM IMERG satellite precipitation estimates require Earthdata Login OAuth2 bearer tokens. Unauthenticated public querying is blocked by NASA GES DISC.
4. **Spatial Representativeness**:
   20 sampling nodes provide elevational coverage across the 11,112 km² basin, but local convective cloudbursts occurring between nodes may be underestimated without radar coverage.

---

## 5. Model Isolation & Governance Safeguards

1. **Zero Model Parameter Drift**:
   Phase 2B Random Forest model weights, hyperparameters, and the 23-feature operational allowlist were **strictly unaltered** in Phase 3D.
2. **Zero Muskingum Parameter Drift**:
   Downstream routing parameters ($K = 18.5\text{ h}$, $X = 0.25$) were **strictly unaltered**.
3. **Operational Prohibitions**:
   - PRAVAAH discharge forecasts must NEVER be deployed as the sole basis for mandatory civilian evacuation without CWC and IMD operational bulletin verification.
   - Downstream water level predictions at Delhi Old Railway Bridge remain strictly blocked pending authentic CWC stage dataset acquisition.

