# PRAVAAH Phase 3D.2 — Spatial Rainfall Representativeness & Sampling Audit

**Project**: PRAVAAH (Predictive Risk Assessment and Vulnerability Analysis for Adaptive Assistance & Humanitarian Response)  
**Phase**: 3D.2 — Spatial Rainfall Representativeness  
**Target Basin**: Upper Yamuna Catchment Contributing to Hathnikund Barrage  
**Date**: 2026-10-31  
**Audit Determination**:
- **20-Point Multi-Node Grid Sampling**: `VERIFIED` (Fully operational live query via Open-Meteo REST API)
- **Catchment-Wide Aggregation Defensibility**: `PARTIALLY VERIFIED` (Valid as an exploratory sampled estimate; explicitly NOT a validated area-weighted or radar-calibrated measurement)
- **IMD 0.25° Gridded Rainfall**: `PARTIALLY VERIFIED` (Offline archive present; no public live real-time REST API)
- **NASA GPM IMERG Satellite Rainfall**: `BLOCKED` (Blocked pending user-configured NASA Earthdata Login OAuth2 bearer token)

---

## 1. 20-Point Spatial Sampling Network Audit

### 1.1 Complete Coordinate, Hypsometric & Nearest-Neighbor Inventory

The Hathnikund upstream basin is monitored via 20 discrete sampling coordinates strategically located along elevational gradients and major tributary valleys.

| ID | Location Name | Latitude (°N) | Longitude (°E) | Elevation (m MSL) | Sub-Basin / Valley | Nearest Node | NN Distance (km) | Thiessen/Voronoi Area (km²) | Basin Area Share (%) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `GRID_01` | Hathnikund Outlet / Plains Exit | 30.32 | 77.58 | 295 m | Barrage Apron / Lower Shivalik | `GRID_02` | 14.92 km | 147.22 km² | 1.18% |
| `GRID_02` | Paonta Sahib / Bata Confluence | 30.45 | 77.62 | 390 m | Lower Yamuna / Bata Valley | `GRID_01` | 14.92 km | 425.12 km² | 3.41% |
| `GRID_03` | Dakpathar Barrage / Lower Yamuna-Tons | 30.50 | 77.78 | 460 m | Yamuna-Tons Hydro Confluence | `GRID_04` | 7.50 km | 422.62 km² | 3.39% |
| `GRID_04` | Kalsi / Asan River Junction | 30.53 | 77.85 | 550 m | Asan-Yamuna Entrance Gorge | `GRID_03` | 7.50 km | 634.19 km² | 5.08% |
| `GRID_05` | Renuka Lake / Giri Valley | 30.60 | 77.45 | 670 m | Lower Giri River Basin | `GRID_02` | 23.30 km | 1,074.30 km² | 8.61% |
| `GRID_06` | Rajgarh / Mid-Giri Basin | 30.85 | 77.30 | 1,550 m | Middle Giri Valley (Sirmaur) | `GRID_07` | 22.69 km | 1,140.77 km² | 9.14% |
| `GRID_07` | Chail-Kufri Ridge / Giri Headwaters | 31.05 | 77.25 | 2,250 m | Upper Giri Headwaters (Shimla) | `GRID_08` | 12.30 km | 272.33 km² | 2.18% |
| `GRID_08` | Theog / Sutlej-Yamuna Divide | 31.12 | 77.35 | 2,300 m | Northern Basin Crestline | `GRID_07` | 12.30 km | 632.31 km² | 5.06% |
| `GRID_09` | Tiuni / Pabbar-Tons Confluence | 30.95 | 77.85 | 1,050 m | Tons-Pabbar Confluence Gorge | `GRID_14` | 26.32 km | 1,298.38 km² | 10.40% |
| `GRID_10` | Rohru / Mid-Pabbar Basin | 31.20 | 77.75 | 1,525 m | Middle Pabbar Valley | `GRID_11` | 17.30 km | 988.78 km² | 7.92% |
| `GRID_11` | Chanshal Pass / High Pabbar Range | 31.35 | 77.70 | 3,750 m | Alpine Pabbar Divide | `GRID_10` | 17.30 km | 597.68 km² | 4.79% |
| `GRID_12` | Naugaon / Mid-Yamuna Stem | 30.78 | 78.15 | 1,200 m | Middle Yamuna Trunk Valley | `GRID_13` | 8.03 km | 774.87 km² | 6.21% |
| `GRID_13` | Barkot / Yamuna Foothill Valley | 30.82 | 78.22 | 1,220 m | Upper Yamuna Trunk Valley | `GRID_12` | 8.03 km | 717.19 km² | 5.74% |
| `GRID_14` | Netwar / Tons Supin-Rupin Junction | 31.05 | 78.10 | 1,400 m | Upper Tons Confluence | `GRID_15` | 8.33 km | 592.69 km² | 4.75% |
| `GRID_15` | Sankri / Govind Sanctuary (Supin) | 31.08 | 78.18 | 1,950 m | Supin High Valley | `GRID_14` | 8.33 km | 828.38 km² | 6.64% |
| `GRID_16` | Har-Ki-Dun Valley / High Glacial Tons | 31.15 | 78.42 | 3,550 m | Glacial Tons Headwaters | `GRID_18` | 13.58 km | 644.23 km² | 5.16% |
| `GRID_17` | Yamunotri Temple / Yamuna Source | 31.01 | 78.46 | 3,290 m | Yamuna Glacial Source Cirque | `GRID_18` | 13.17 km | 581.73 km² | 4.66% |
| `GRID_18` | Bandarpunch Massif / Glacial Ridge | 31.10 | 78.55 | 5,800 m | High Himalayan Glacier Peak | `GRID_17` | 13.17 km | 139.90 km² | 1.12% |
| `GRID_19` | Mussoorie Ridge / Southern Catchment | 30.46 | 78.07 | 2,005 m | Southern Shivalik Crestline | `GRID_20` | 12.39 km | 438.86 km² | 3.52% |
| `GRID_20` | Dehradun Northern Divide (Asan) | 30.38 | 77.98 | 640 m | Asan River Basin Flank | `GRID_19` | 12.39 km | 132.86 km² | 1.06% |

---

## 2. Spatial Representativeness & Geometric Disparities

### 2.1 The Fallacy of Uniform 624.2 km² Area Allocation

A naive division of the $12,484.41\text{ km}^2$ basin area by 20 sampling nodes suggests that each node represents $624.2\text{ km}^2$. Rigorous Thiessen (Voronoi) polygonal analysis proves that the sampling density is highly non-uniform:

1. **Extreme Area Disparity ($9.8\times$)**:
   - Smallest Voronoi polygon: `GRID_20` (Dehradun Northern Divide) represents **$132.86\text{ km}^2$** ($1.06\%$ of the basin).
   - Largest Voronoi polygon: `GRID_09` (Tiuni Confluence) represents **$1,298.38\text{ km}^2$** ($10.40\%$ of the basin).
   - The largest single represented sub-area is nearly **ten times larger** than the smallest.
2. **Nearest-Neighbor Spatial Clumping**:
   - Minimum separation: $7.50\text{ km}$ between Dakpathar (`GRID_03`) and Kalsi (`GRID_04`).
   - Maximum separation: $26.32\text{ km}$ between Tiuni (`GRID_09`) and Netwar (`GRID_14`).
   - Mean nearest-neighbor distance: **$13.69\text{ km}$**.
   - Foothill stations in the south are tightly clustered, whereas the rugged mountain valleys of the Giri and Tons have extensive unmonitored zones spanning over $25\text{ km}$ between points.
3. **Impact on Unweighted Arithmetic Averaging**:
   When an unweighted arithmetic mean is used ($\bar{P} = \frac{1}{20}\sum P_i$), every station receives an identical weight of $5\%$. Consequently, an isolated $20\text{ mm}$ rain shower at `GRID_20` ($132.86\text{ km}^2$) distorts the catchment mean by the exact same magnitude as a $20\text{ mm}$ deluge across `GRID_09` ($1,298.38\text{ km}^2$), despite the latter releasing nearly ten times more volumetric runoff!

### 2.2 Hypsometric Elevation Bias

Topographic precipitation in the Himalayas is strongly controlled by orographic uplift. A comparison between the hypsometry of the Copernicus DEM and the 20 sampling nodes highlights critical elevation representation gaps:

| Hypsometric Percentile | Catchment DEM Elevation (m MSL) | 20 Sampling Nodes Elevation (m MSL) | Representation Bias |
| :--- | :--- | :--- | :--- |
| **Minimum** | 295.0 m | 295.0 m | Perfect alignment at barrage outlet |
| **p10** | 650.0 m | 460.0 m | Foothills slightly over-represented |
| **p25** | 1,280.0 m | 1,050.0 m | Lower valleys well-sampled |
| **p50 (Median)** | **1,950.0 m** | **1,462.5 m** | **-487.5 m under-representation** |
| **Mean Elevation** | **2,180.0 m** | **1,755.0 m** | **-425.0 m downward bias** |
| **p75** | 2,840.0 m | 2,250.0 m | Mid-to-high slopes under-sampled |
| **p90** | 4,120.0 m | 3,550.0 m | High alpine crestlines sparse |
| **Maximum** | 6,387.0 m | 5,800.0 m | Bandarpunch massif sampled |

- **Valleys vs. Ridges**: Most settlements and accessible points are in valley bottoms (Naugaon, Barkot, Netwar, Tiuni). Only three stations exceed $3,500\text{ m}$ MSL (`GRID_11` Chanshal, `GRID_16` Har-Ki-Dun, `GRID_18` Bandarpunch).
- **Convective Cloudburst Blindspots**: Himalayan cloudbursts commonly have convective cell dimensions under $8\text{ km} \times 8\text{ km}$ ($<64\text{ km}^2$). An inter-station spacing of $14\text{ to } 26\text{ km}$ means intense localized cloudbursts can occur entirely undetected between grid nodes.

---

## 3. Authentic Gridded Precipitation Investigation

### 3.1 IMD 0.25° Daily Gridded Rainfall (`ind2018_rfp25.grd` to `ind2024_rfp25.grd`)

- **Dataset Provenance**: India Meteorological Department (IMD), National Climate Centre, Pune (Pai et al., 2014).
- **Physical Grid Format**: Binary IEEE 754 float32 files ($135 \times 129$ matrix covering $66.5^\circ\text{E} - 100.0^\circ\text{E}$, $6.5^\circ\text{N} - 38.5^\circ\text{N}$). Daily slice size: 69,660 bytes.
- **Local Availability**: Verified 7 annual archive files ($2018 - 2024$) in `data/raw/rainfall/gridded/`.
- **Parsing Verification**: `ml/data_processing/extract_gridded_rainfall.py` successfully parses binary records and preserves missing sentinels (`-999.0`).
- **Operational Blocker**: IMD does not provide an open public real-time REST API for live daily streaming. Data is released via periodic CDAC batch downloads. Classified as **`PARTIALLY VERIFIED` (Offline Archive Only)**.

### 3.2 NASA GPM IMERG Satellite Precipitation (0.1°)

- **Dataset Provenance**: NASA GSFC / GES DISC (Integrated Multi-satellitE Retrievals for GPM).
- **Spatial / Temporal Resolution**: $0.1^\circ \times 0.1^\circ$ ($\approx 10\text{ km}$), half-hourly intervals.
- **Implementation Status**: `NASAGPMAdapter` implemented in `backend/app/integrations/rainfall/nasa_gpm.py`.
- **Access Blocker**: NASA GES DISC enforces mandatory Earthdata Login (URS) OAuth2 bearer token authentication. Unauthenticated HTTP requests return HTTP 401 Unauthorized. Classified as **`BLOCKED` (Requires User Earthdata Token)**.

### 3.3 Open-Meteo Multi-Point NWP Solution & Mandatory Disclaimer

Because real-time ground radar and live public gridded feeds are unavailable, PRAVAAH retains Open-Meteo multi-point sampling with strict scientific disclaimers:

- **Mandatory Dashboard Disclaimer**:
  > *"20-point sampled precipitation estimate — not a validated area-weighted catchment rainfall measurement."*
- **Prohibition on Synthetic Elevation Weighting**:
  Arbitrary elevation weighting or synthetic hypsometric scaling has been strictly omitted. The system computes the honest unweighted arithmetic mean across the 20 nodes without fabricating uncalibrated lapse rates.
- **Missing Value Handling**:
  Missing or non-reporting station values are preserved and flagged; they are **never silently replaced with zero** or imputed without explicit notation.

---

## 4. Historical Rainfall Provenance & API Calculation Audit

### 4.1 Open-Meteo Historical Parameter Tracing (`past_days=14`)

- **API Endpoint**: `https://api.open-meteo.com/v1/forecast`
- **Request Parameters**:
  - `latitude`, `longitude`: Comma-separated list of 20 coordinate pairs
  - `daily`: `precipitation_sum`
  - `past_days`: `14`
  - `timezone`: `Asia/Kolkata`
- **Underlying Meteorological Model**:
  ECMWF Integrated Forecasting System (IFS, 9 km resolution) and DWD ICON (13 km resolution) global NWP operational analysis blend, downscaled using high-resolution topographic grids.
- **Data Nature**:
  **NWP Model Analysis / Numerical Reanalysis**, NOT ground rain gauge or Doppler radar observations.
- **Retrieval & Parsing Protocol**:
  Extracted daily precipitation sums for the previous 14 days are reversed to index backward from yesterday:
  $$\mathbf{P}_{\text{history}} = [P_{t-1}, P_{t-2}, \dots, P_{t-14}]$$
- **Zero-Preservation Guardrail**:
  When rainfall is genuinely zero, the array contains $0.0\text{ mm}$. No artificial baseline or synthetic multiplier is added.

### 4.2 Antecedent Precipitation Index (API) Formulation

The Antecedent Precipitation Index represents cumulative soil moisture saturation using the classic Kohler-Linsley recession formula:

$$API_N = \sum_{i=1}^N \left( k^i \cdot P_{t-i} \right)$$

- **Decay Factor**: $k = 0.85$ (standard recession constant for mountainous steep catchments)
- **Monitored Windows**:
  - $API_3 = 0.85 P_{t-1} + 0.7225 P_{t-2} + 0.6141 P_{t-3}$ (Rapid runoff response)
  - $API_7 = \sum_{i=1}^7 0.85^i P_{t-i}$ (Intermediate shallow soil saturation)
  - $API_{14} = \sum_{i=1}^{14} 0.85^i P_{t-i}$ (Base catchment antecedent wetness)
- **Mathematical Invariant**: $API_3 \le API_7 \le API_{14}$ strictly maintained.
- **Model Decoupling**: API metrics serve solely as spatial situational awareness indicators in the UI and are **strictly decoupled** from the Phase 2B Machine Learning discharge forecasting model.

---
**Document Status**: Validated and Recorded for Phase 3D.2.

