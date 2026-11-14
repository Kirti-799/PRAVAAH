# PRAVAAH Phase 3D.2 — Catchment Geometry Reconstruction & Validation Report

**Project**: PRAVAAH (Predictive Risk Assessment and Vulnerability Analysis for Adaptive Assistance & Humanitarian Response)  
**Phase**: 3D.2 — Catchment Geometry Reconstruction & Validation  
**Target Basin**: Upper Yamuna Catchment Contributing to Hathnikund Barrage  
**Date**: 2026-10-31  
**Audit Determination**:
- **DEM Raster-Delineated Watershed**: `NOT VERIFIED` (Cannot be reproduced from raw D8 DEM processing without advanced depression flat-routing)
- **Authoritative Ridgeline Boundary**: `PARTIALLY VERIFIED` (Traceable to CWC literature, but simplified 16-point polygon encloses $+12.4\%$ area due to convex chord inflation)
- **Pour Point Alignment**: `VERIFIED` (Hathnikund Barrage at $30.317^\circ\text{N}, 77.585^\circ\text{E}$)
- **Drainage Network Extraction**: `PARTIALLY VERIFIED` (5 schematic macro-backbone lines representing $440.74\text{ km}$ total length; not a complete cell-by-cell raster hydrography)

---

## 1. DEM-to-Watershed Processing Pipeline Investigation

### 1.1 Inventory of Intermediate Hydrological Rasters

A comprehensive audit of the repository for persistent intermediate hydrological rasters was conducted:

| Expected Artifact | File Type | Status on Disk | Provenance & Forensic Trace |
| :--- | :--- | :--- | :--- |
| **Raw DEM Tiles** | GeoTIFF | **EXISTS** (4 tiles) | `data/raw/spatial/dem/Copernicus_DSM_COG_10_N30_00_E077_00_DEM.tif` etc. (Authenticated Copernicus GLO-30 COGs). |
| **Processed Mosaic** | GeoTIFF | **EXISTS** (1 file) | `data/processed/spatial/dem/upstream_yamuna_dem_mosaic.tif` (7200×7200, 207 MB, exact 0.0m difference from source tiles). |
| **Flow-Direction Raster** | GeoTIFF / Grid | **NEVER SAVED** | Not found on disk. Computed transiently in-memory via `D8FlowEngine.compute_flow_direction`. |
| **Flow-Accumulation Raster** | GeoTIFF / Grid | **NEVER SAVED** | Not found on disk. Computed transiently in-memory via `D8FlowEngine.compute_flow_accumulation`. |
| **Watershed Raster** | GeoTIFF / Mask | **NEVER SAVED** | Not found on disk. No binary raster mask persisted. |
| **Unsimplified Watershed Vector** | GeoJSON / Shapefile | **NEVER SAVED** | No unsimplified raster-vectorized polygon exists. |
| **Current Watershed Vector** | GeoJSON | **EXISTS** (1 file) | `data/processed/spatial/catchment/hathnikund_upstream_catchment.geojson` (16-vertex polygon). |

### 1.2 Attempted Raster Reproduction from Acquired DEM

To determine whether the original watershed raster could be reproduced from the acquired Copernicus DEM mosaic (`upstream_yamuna_dem_mosaic.tif`) using the existing `D8FlowEngine` implementation, the complete pipeline was executed:

1. **Decimation & Resolution**:
   - Source: $7200 \times 7200$ pixels ($\approx 30.8\text{ m}$ resolution).
   - Real-time decimation factor: $\text{step} = 6 \implies 1200 \times 1200$ grid ($\approx 185\text{ m}$ cell size, cell area $= 0.0293\text{ km}^2$).
2. **Sink Analysis in Raw DEM**:
   - Total grid cells: $1,440,000$.
   - Identified sinks ($\text{Slope} \le 0$ to all 8 neighbors): **22,702 cells** ($1.58\%$ of the entire raster).
   - In steep Himalayan terrain and radar surface models (DSMs), canopy noise, narrow bedrock gorges, and artificial reservoir pools form thousands of local depressions.
3. **Execution of `_delineate_from_raster`**:
   - The simple sink cleaning in `catchment.py` (`np.where(np.isnan(dem) | (dem < -100), ...)`) only handles missing/negative values; it does **not** fill depressions or breach dams.
   - Consequently, downstream flow accumulation terminates at the first encountered gorge depression.
   - Maximum flow accumulation in the entire $1200 \times 1200$ grid reached only **3,869 cells** ($\approx 113\text{ km}^2$).
   - At Hathnikund Barrage ($30.317^\circ\text{N}, 77.585^\circ\text{E}$), the snapped pour-point search captured only **373 cells**, yielding an extracted watershed area of:
     $$A_{\text{raster}} = 373 \times 0.0293\text{ km}^2 = \mathbf{10.93\text{ km}^2} \quad (\text{Max elevation } 642.97\text{ m})$$
   - Over $99.9\%$ of the true basin (the Tons, Giri, Pabbar, and Yamunotri headwaters) was severed at the Shivalik entrance gorge.
4. **Experimental Priority-Flood Test**:
   - A priority-flood depression-filling algorithm (Barnes et al., 2014) was executed on the $1200 \times 1200$ grid (completed in 6.87 s, filling depressions up to $207.4\text{ m}$).
   - However, because raw D8 flow direction assigns code `0` to flat water surfaces, the resulting horizontal lake flats (41,406 flat cells) created internal dead ends that stopped flow routing without an explicit flat-routing breadth-first solver.
5. **Definitive Conclusion**:
   The original watershed raster **cannot be reproduced** from the acquired DEM using the existing codebase's processing parameters. In accordance with strict scientific guidelines, the DEM-delineated raster watershed is classified as **`NOT VERIFIED`**.

### 1.3 True Provenance of `hathnikund_upstream_catchment.geojson`

Forensic inspection of `ml/spatial/catchment.py` (lines 402–450) confirms that the current 16-point polygon was generated by `_build_authoritative_catchment_model()`. It was manually synthesized to trace the primary Himalayan divides separating the Giri, Pabbar, Tons, and Yamuna headwaters down to Hathnikund Barrage, assigning an unverified literature area of $11,112.0\text{ km}^2$ based on CWC reports.

---

## 2. Quantitative Evaluation of Catchment Area Discrepancy

### 2.1 Rigorous Metric Area Calculations Across Equal-Area Projections

The 16-vertex polygon was quantitatively audited across standard geodetic and projected coordinate reference systems:

| Projection / Measurement Method | Code / Parameters | Area ($\text{km}^2$) | Perimeter ($\text{km}$) | Discrepancy vs. 11,112 $\text{km}^2$ |
| :--- | :--- | :--- | :--- | :--- |
| **Geodesic on WGS 84 Ellipsoid** | `pyproj.Geod(ellps='WGS84')` | **12,484.44 km²** | **409.93 km** | $+1,372.44\text{ km}^2$ (+12.35%) |
| **Custom Basin Albers Equal Area** | $\text{lat}_1=30^\circ, \text{lat}_2=32^\circ, \text{lon}_0=77.8^\circ$ | **12,484.41 km²** | **409.87 km** | $+1,372.41\text{ km}^2$ (+12.35%) |
| **UTM Zone 43N (Conformal)** | `EPSG:32643` | **12,497.65 km²** | **410.16 km** | $+1,385.65\text{ km}^2$ (+12.47%) |
| **India Albers Equal Area** | `EPSG:7755` ($\text{lat}_1=12^\circ, \text{lat}_2=28^\circ$) | **12,181.46 km²** | **404.93 km** | $+1,069.46\text{ km}^2$ (+9.62%) |
| **Unfilled Raster D8 Watershed** | Copernicus Mosaic ($1200 \times 1200$) | **10.93 km²** | **14.2 km** | $-11,101.07\text{ km}^2$ (-99.9%) |
| **Reported Metadata Value** | `catchment_metadata.json` | **11,112.00 km²** | **568.50 km** | $0.00\text{ km}^2$ (Reference Value) |

### 2.2 Mathematical Cause of the $+12.4\%$ Chord Discrepancy

The discrepancy between the $12,484.41\text{ km}^2$ polygon area and the $11,112.0\text{ km}^2$ literature benchmark is mathematically explained by **polygonal chord truncation**:

1. **Scale of Simplification**:
   A 16-point polygon representing a basin spanning $1.7^\circ$ longitude ($\approx 160\text{ km}$) and $1.15^\circ$ latitude ($\approx 130\text{ km}$) has an average edge length of $27.3\text{ km}$ (with segment lengths reaching up to $40.5\text{ km}$).
2. **Convex Over-Inclusion**:
   Natural drainage divides in the Himalayas are highly sinuous, winding inward along deeply dissected mountain valleys (e.g., between the Sutlej and Giri basins, or between the Bhagirathi and Yamuna headwaters).
   When two distant ridgeline peaks (such as Swargarohini at $78.45^\circ\text{E}, 31.30^\circ\text{N}$ and the Bhagirathi divide at $78.62^\circ\text{E}, 31.02^\circ\text{N}$) are connected by a single straight chord:
   - The chord bulges convexly outward across intervening mountain passes.
   - It captures adjacent non-contributing drainage territory.
   - On the southern boundary, chords across the Mussoorie and Shivalik foothills similarly encompass peripheral valleys.
3. **Geometry Repair & Simplification Sensitivity**:
   - Geometry validation (`geom.is_valid`) confirmed the polygon is topologically clean with zero self-intersections. Running `geom.buffer(0)` produces an identical area of $12,484.41\text{ km}^2$.
   - Applying Douglas-Peucker simplification to the 16-point polygon further degrades accuracy:
     - Tolerance $0.01^\circ$ (14 vertices): $12,159.06\text{ km}^2$ ($\Delta = -325.35\text{ km}^2$)
     - Tolerance $0.02^\circ$ (13 vertices): $12,139.36\text{ km}^2$ ($\Delta = -345.05\text{ km}^2$)
     - Tolerance $0.05^\circ$ (9 vertices): $11,597.00\text{ km}^2$ ($\Delta = -887.41\text{ km}^2$)
4. **Preservation Guardrail**:
   Strictly following scientific protocols, the polygon geometry was **not altered, warped, or clipped** to force an artificial match with $11,112\text{ km}^2$. Both values are explicitly reported and contextualized.

---

## 3. Independent Watershed Validation Against Authoritative Benchmarks

| Parameter | PRAVAAH Implementation | Authoritative Reference Benchmark | Source & Traceability |
| :--- | :--- | :--- | :--- |
| **Pour Point Outlet** | Hathnikund Barrage ($30.317^\circ\text{N}, 77.585^\circ\text{E}$) | Hathnikund Barrage ($30.317^\circ\text{N}, 77.593^\circ\text{E}$) | Haryana Irrigation Dept & CWC Upper Yamuna Division |
| **River Reach** | Yamuna exit from Shivaliks into Indo-Gangetic Plains | Same | Survey of India Topographic Sheets 53F/10, 53F/14 |
| **Drainage Area** | $12,484.41\text{ km}^2$ (Polygon) / $11,112.0\text{ km}^2$ (Lit Ref) | $11,112\text{ to } 11,391\text{ km}^2$ | Central Water Commission (CWC) *Yamuna Basin Report* (2014, 2018), Tajewala/Hathnikund Site Code `000109` |
| **National Hydrology Benchmark** | Literature range | $11,150\text{ to } 11,210\text{ km}^2$ | National Institute of Hydrology (NIH), Roorkee: *Upper Yamuna Hydrological Modelling* (Jain et al.) |
| **Global HydroSHEDS Basin** | Spatial boundary comparison | $\approx 11,200\text{ km}^2$ | HydroSHEDS / HydroATLAS (WWF/USGS) Level 6/7 Basin ID `4060017440` |
| **Major Contributing Sub-Basins** | Tons, Giri, Pabbar, Asan, Upper Yamuna Headwaters | Tons, Giri, Pabbar, Asan, Upper Yamuna Headwaters | CWC Basin Atlas of India; Wadia Institute of Himalayan Geology |
| **Glaciated Headwaters** | Bandarpunch massif ($6,387\text{ m}$), Yamunotri Glacier | Same ($6,387\text{ m}$ MSL) | Geological Survey of India (GSI) Glaciology Division |
| **Disconnected Regions** | **Zero** disconnected polygons or internal holes | Continuous catchment | Shapely topological inspection (`len(geom.interiors) == 0`) |

---

## 4. Drainage Network Extraction Audit

### 4.1 Comparison of Full Raster vs. Vector Backbone

| Drainage Metric | Value | Hydrological Classification & Interpretation |
| :--- | :--- | :--- |
| **Full Raster Stream Segments** | **0** | **Failed extraction**: Gorge sinks terminated D8 channel tracing. |
| **Vector Stream Features** | **5** | **Schematic Regional Macro-Backbone**: LineString features in GeoJSON. |
| **Total Vector Backbone Length** | **440.74 km** | Projected UTM 43N metric length across all 5 branches. |
| **Upper Yamuna Main Stem Length** | **116.38 km** | Yamunotri Glacier (31.02°N, 78.45°E) down to Hathnikund (30.317°N, 77.585°E). |
| **Tons River Length** | **137.86 km** | Har-ki-Dun/Supin (31.40°N, 78.35°E) down to Dakpathar confluence. |
| **Giri River Length** | **95.91 km** | Chail/Kufri ridge (31.10°N, 77.25°E) down to Paonta Sahib confluence. |
| **Pabbar River Length** | **45.97 km** | Chanshal Pass (31.30°N, 77.75°E) down to Tiuni confluence with Tons. |
| **Asan River Length** | **44.62 km** | Western Doon valley (30.35°N, 78.10°E) down to Dakpathar apron. |
| **Macro-Backbone Drainage Density** | **0.0353 km/km²** | Macro-scale orientation backbone ($440.74\text{ km} / 12,484.41\text{ km}^2$). |
| **Raster Drainage Density (Lit Benchmark)** | $\approx 0.38\text{ km/km}^2$ | Cell-by-cell dissected mountain stream density at $A_{\text{thresh}} = 50\text{ km}^2$. |

### 4.2 Tributary Discharge Inflows

- **Audit Resolution**: All unverified percentage figures ("~60% Tons", "~20% Giri") have been removed from user-facing presentations and API summaries.
- **Hydrological Qualification**: The Tons River drains high alpine snowmelt and glaciated terrain with the highest specific discharge in the basin, while the Giri River is a lower-elevation sub-Himalayan rain-fed tributary. Exact volumetric percentages require dedicated sub-basin gauge telemetry.

---
**Document Status**: Validated and Recorded for Phase 3D.2.

