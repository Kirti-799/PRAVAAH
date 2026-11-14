# Phase 3A: Terrain Processing & Slope Analysis Specification

**Project:** PRAVAAH (Predictive Risk Assessment and Vulnerability Analysis for Adaptive Assistance & Humanitarian Response)  
**Milestone:** Phase 3A — Spatial Data Infrastructure & Terrain Processing  
**Document:** Terrain Processing and Geodesic Slope Calculation Methodology  
**Implementation Modules:** `ml/spatial/dem.py`, `backend/app/services/spatial.py`, `backend/app/schemas/spatial.py`

---

## 1. Mathematical Formulation of Terrain Slope

Terrain slope is defined as the maximum rate of change in elevation from an elevation cell to its eight orthogonal and diagonal neighbors. It indicates steepness and directly impacts hydrological runoff velocities and sheet flow accumulation.

PRAVAAH implements **Horn's (1981)** 2nd-order finite difference algorithm, the recognized standard in GIS and computational geomorphology (used in GDAL, ArcGIS, and GRASS GIS).

For a $3 \times 3$ moving kernel centered at pixel $e$:
```
[ a   b   c ]
[ d   e   f ]
[ g   h   i ]
```

The horizontal and vertical partial derivatives ($p = \frac{\partial z}{\partial x}$, $q = \frac{\partial z}{\partial y}$) are given by:

$$p = \frac{\partial z}{\partial x} = \frac{(c + 2f + i) - (a + 2d + g)}{8 \times \Delta x}$$

$$q = \frac{\partial z}{\partial y} = \frac{(g + 2h + i) - (a + 2b + c)}{8 \times \Delta y}$$

From the directional derivatives, the slope angle in radians $\theta$ and degrees $\theta_{\text{deg}}$ is computed:

$$\theta = \arctan\left(\sqrt{p^2 + q^2}\right)$$

$$\theta_{\text{deg}} = \theta \times \frac{180}{\pi}$$

The slope percent (rise over run) is given by:

$$\text{Slope}_{\%} = \tan(\theta) \times 100 = \sqrt{p^2 + q^2} \times 100$$

---

## 2. Geodesic Metric Scaling & CRS Handling

### 2.1 The Fundamental Angular vs Metric Problem
Public DEMs (such as SRTMGL1 and Copernicus GLO-30) are commonly published in Geographic Coordinates (WGS 84, `EPSG:4326`), where coordinates and grid resolutions are defined in **angular degrees ($^\circ$)**, while elevation values $z$ are recorded in **meters ($m$)**.

If the finite difference derivatives are computed using raw degree resolution:
$$\Delta x \approx 0.000277^\circ \quad \text{(30m resolution)}$$
$$\frac{\Delta z}{\Delta x} \approx \frac{1\text{ m}}{0.000277^\circ} \approx 3,600 \text{ (Distortion factor $> 100,000\times$)}$$

This results in absurd, mathematically corrupted slopes ($> 89.9^\circ$).

### 2.2 PRAVAAH Geodesic Correction Protocol
`DEMValidator.compute_slope()` resolves this by inspecting the CRS and applying geodetic metric scaling:

1. **Projected CRS (e.g., UTM Zone 43N, `EPSG:32643`):**
   - Horizontal units are already defined in meters ($m$).
   - $\Delta x = \text{pixel\_size}_x$
   - $\Delta y = \text{pixel\_size}_y$
2. **Geographic CRS (e.g., WGS 84, `EPSG:4326`):**
   - The engine computes the central latitude $\phi_{\text{mean}}$ of the raster extent.
   - Ground distance per degree longitude:
     $$\Delta x = \text{pixel\_size}_x \times 111,320.0 \times \cos\left(\frac{\pi}{180} \cdot \phi_{\text{mean}}\right) \quad (\text{meters})$$
   - Ground distance per degree latitude:
     $$\Delta y = \text{pixel\_size}_y \times 110,540.0 \quad (\text{meters})$$
   - For the Yamuna corridor ($\phi \approx 29.5^\circ\text{ N}$), $\cos(29.5^\circ) \approx 0.8703$, giving $\Delta x \approx 27.0\text{ m}$ and $\Delta y \approx 30.7\text{ m}$ for 1-arc-second data.

---

## 3. Kernel Edge and Masking Protocol

1. **Boundary Cells:**
   - 1-pixel outer borders are evaluated using forward/backward difference or masked appropriately to avoid boundary artifacts.
2. **NoData & Non-Finite Propagation:**
   - If any neighbor in the $3 \times 3$ window is invalid (NoData or non-finite), the center cell's slope derivative is marked invalid.
   - The invalid mask is propagated to ensure slope outputs do not contain corrupted values.

---

## 4. Slope Distribution Schema

For valid cells in the terrain surface, `DEMValidator.compute_slope()` computes:

| Parameter | Unit | Scientific Significance |
| :--- | :---: | :--- |
| `min_slope_deg` | Degrees ($^\circ$) | Baseline flatness of riverbeds and floodplains. |
| `max_slope_deg` | Degrees ($^\circ$) | Peak steepness on embankments, bridges, and foothills. |
| `mean_slope_deg` | Degrees ($^\circ$) | Average gradient across the candidate spatial tile. |
| `median_slope_deg`| Degrees ($^\circ$) | Robust central tendency resilient to localized spikes. |
| `std_slope_deg` | Degrees ($^\circ$) | Topographic variability and surface roughness indicator. |
| `max_slope_percent`| Percent ($\%$) | Hydraulic gradient indicator ($> 100\%$ indicates slopes steeper than $45^\circ$). |

### Slope Categorization:
- **Flat (< 2°):** Active river channel, alluvial floodplains, low terraces (Yamuna floodway).
- **Gentle (2° – 5°):** Inhabited alluvial terraces, embankments, urban agricultural land.
- **Moderate (5° – 15°):** Natural riverbanks, highway approach ramps, minor terrain undulations.
- **Steep (> 15°):** Siwalik foothill ridges, engineered revetments, bridge piers.

---

## 5. Strict Unavailable Handling

If no validated DEM raster is available in `data/raw/spatial/dem/`:
- `GET /api/spatial/terrain/summary` returns an explicit `UNAVAILABLE` status.
- **No mock rasters are calculated or persisted.**
- Frontend displays a structured empty state indicating that terrain analysis is awaiting real DEM tile ingestion.
