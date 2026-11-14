# Phase 3D.3 — Drainage Network Extraction Report

**Project**: PRAVAAH (Predictive Risk Assessment and Vulnerability Analysis for Adaptive Assistance & Humanitarian Response)  
**Scope**: Contributing Drainage Network & Flow Pathways Upstream of Hathnikund Barrage  
**Status**: VERIFIED & VECTORIZED

---

## 1. Drainage Extraction Methodology

Drainage networks were extracted using two complementary approaches:
1. **DEM Flow Accumulation Thresholding**:
   Stream channels are defined where the contributing flow accumulation exceeds a threshold of contributing cells:
   $$A_{\text{cell}} \ge T_{\text{stream}} = 500\text{ cells}$$
   Raster channel segments are converted to vector LineString geometries via `rasterio.features.shapes()`.
2. **Authoritative Hydrologic Network Verification**:
   Extracted channels are cross-checked and harmonized with OpenStreetMap waterways and Survey of India river hydrography to guarantee topological continuity across deep mountain gorges where DEM interpolation artifacts may occur.

---

## 2. Contributing Tributary Classification & Attributes

The primary drainage arteries contributing to Hathnikund are stored in `data/processed/spatial/catchment/hathnikund_drainage_network.geojson`:

| River Trunk | Inflow Share | Stream Order | Elevation Drop | Headwater Origin | Key Confluences |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Upper Yamuna Main Stem** | ~15% | Order 5 | 6,287m $\to$ 295m | Yamunotri Glacier (31.01°N, 78.46°E) | Naugaon, Barkot, Dakpathar |
| **Tons River** | ~60% | Order 5 | 5,800m $\to$ 450m | Supin/Rupin (Har-ki-Dun) | Tiuni (Pabbar confluence), Dakpathar |
| **Pabbar River** | Part of Tons | Order 4 | 3,750m $\to$ 1,050m | Chanshal Pass (31.35°N, 77.70°E) | Rohru, Tiuni |
| **Giri River** | ~20% | Order 4 | 2,250m $\to$ 390m | Chail/Kufri Ridge (31.05°N, 77.25°E) | Renuka, Paonta Sahib |
| **Asan River** | ~5% | Order 3 | 640m $\to$ 460m | Dehradun Valley (30.38°N, 77.98°E) | Dakpathar Barrage apron |

---

## 3. Separation Between Upstream Drainage and Downstream Corridor

A fundamental scientific distinction maintained in PRAVAAH:

- **Upstream Drainage Network**: High-gradient, steep bedrock mountain channels generating rapid hydrological runoff. Subject to flash flooding, cloudbursts, and debris flows. Governed by kinematic wave runoff routing.
- **Downstream Yamuna Corridor**: Low-gradient alluvial plain river (slope < 0.05%) from Hathnikund towards Delhi Old Railway Bridge. Governed by channel storage, overbank flood inundation, embankment bunds, and diffusive wave routing (Muskingum).

**Guardrail Policy**: Upstream DEM drainage lines are strictly kept separate from downstream flood hazard boundaries and must never be conflated.

