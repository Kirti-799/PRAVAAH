# PRAVAAH Phase 3D.3 — Hydrological Terrain Conditioning & Flow Routing Diagnosis

**Project**: PRAVAAH (Predictive Risk Assessment and Vulnerability Analysis for Adaptive Assistance & Humanitarian Response)  
**Phase**: 3D.3 — Hydrological Terrain Conditioning  
**Target Basin**: Upper Yamuna Catchment Contributing to Hathnikund Barrage  
**Date**: 2026-11-01  
**Audit Determination**: `VERIFIED` (Reproducible Priority-Flood depression filling and spillway BFS flat routing implemented and validated)

---

## 1. Diagnostic Investigation of the Raw D8 Flow Failure

In Phase 3D.2, standard D8 flow routing on the raw Copernicus GLO-30 Digital Surface Model (DSM) terminated prematurely at the entrance to the lower Shivalik gorge, yielding an extracted catchment area of only **$10.93\text{ km}^2$** (373 cells) instead of the expected $>11,000\text{ km}^2$.

A spatial diagnostic analysis of the $7200 \times 7200$ Copernicus DEM mosaic (`upstream_yamuna_dem_mosaic.tif`) decimated to a $1200 \times 1200$ grid ($\approx 159.0\text{ m} \times 184.2\text{ m}$ cell size) revealed the structural causes of this failure:

### 1.1 Spatial Distribution of Internal Sinks
- **Total Internal Sinks**: **22,241 cells** ($1.54\%$ of the entire terrestrial grid).
- **Sink Elevation Range**: $256.9\text{ m}$ to $5,946.4\text{ m}$ MSL (median: $677.1\text{ m}$, mean: $1,063.5\text{ m}$).
- **River Gorge Bottlenecks**: In the critical $45\text{ km}$ river reach from Dakpathar Barrage ($442.1\text{ m}$ MSL) through Paonta Sahib ($398.4\text{ m}$ MSL) down to Hathnikund Barrage ($334.0\text{ m}$ MSL), **399 distinct internal sinks** were identified in the channel bed.

### 1.2 Geomorphic & Sensor Causes of Pits in Radar DSMs
1. **Bridge and Barrage Structures**:
   Engineered civil works (such as the Dakpathar Barrage, Asan Barrage, Paonta Sahib highway bridge, and Hathnikund barrage piers) appear in interferometric radar surface models as elevated barriers across the riverbed, forming artificial dams.
2. **Dense Riparian Canopy**:
   Copernicus GLO-30 is a Digital Surface Model (DSM) derived from TanDEM-X X-band radar, which reflects off tree canopies. Dense forested gorge flanks in the Shivaliks stand 15–25 m above the water level, obstructing narrow incised river gorges.
3. **Specularity & Water Level Fluctuations**:
   Radar backscatter over calm open water is highly specular, leading to low signal return and interpolation artifacts in water masks.
4. **Failure Mechanism in Standard D8**:
   In standard D8 routing, flow direction is calculated strictly by steepest downward gradient:
   $$\text{Slope}_i = \frac{z_{\text{center}} - z_i}{d_i}$$
   If all 8 adjacent neighbors have elevation $z_i \ge z_{\text{center}}$, the drop is $\le 0$, and the cell is assigned direction code `0` (sink). In raw D8, flow terminates at the very first sink encountered, completely isolating the Tons, Giri, Pabbar, and Yamunotri headwaters from the downstream barrage outlet.

---

## 2. Evaluation of Hydrological Conditioning Algorithms

To establish a scientifically defensible, reproducible solution suitable for steep Himalayan relief, multiple hydrological conditioning algorithms were evaluated:

| Conditioning Method | Algorithmic Mechanism | Strengths | Failure Modes in Steep Relief | Selection Status |
| :--- | :--- | :--- | :--- | :--- |
| **Simple Cutoff Sink Cleaning** | Replaces values $< -100\text{ m}$ or NaNs | Fast, trivial | Does not resolve actual terrain pits ($10.93\text{ km}^2$ failure) | **REJECTED** |
| **Depression Breaching (Carving)** | Carves trenches through barriers to lower downstream cells | Preserves upstream elevations | Fails when barriers exceed search radius or in long multi-km gorge backwaters | **REJECTED** |
| **Least-Cost Breaching** | Minimizes volume of carved terrain | Geomorphologically realistic | High computational cost ($O(N \log N)$ with complex heuristics); unstable in wide reservoirs | **REJECTED** |
| **Priority-Flood Filling (Barnes et al., 2014)** | Uses min-heap starting from domain boundary to fill pits to spillway level | Optimal $O(N \log N)$, fully fills all depressions to spillway height | Leaves flat lake surfaces with zero slope ($\text{Slope} = 0$) | **SELECTED (Part 1)** |
| **Spillway Breadth-First Flat Routing** | Breadth-first search from spillway outlets backward into flat lakes | Assigns monotonic D8 flow direction to every flat cell without artificial slope gradients | Requires multi-pass BFS queue management | **SELECTED (Part 2)** |

---

## 3. Implementation of Priority-Flood & Spillway Flat Routing

The two-stage conditioning engine was implemented in `ml/spatial/catchment.py`:

### Stage 1: Optimal Priority-Flood Depression Filling
```python
# Push all domain boundary cells into a min-heap
for r, c in domain_boundaries:
    heapq.heappush(heap, (dem[r, c], r, c))
    visited[r, c] = True

# Pop lowest cell and raise neighbors to spillway height if lower
while heap:
    z, r, c = heapq.heappop(heap)
    for nr, nc in neighbors(r, c):
        if not visited[nr, nc]:
            visited[nr, nc] = True
            nz = dem[nr, nc]
            if nz < z:
                filled[nr, nc] = z
                heapq.heappush(heap, (z, nr, nc))
            else:
                heapq.heappush(heap, (nz, nr, nc))
```
- **Execution Performance**: 8.15 seconds on $1,440,000$ cells.
- **Maximum Fill Depth**: $207.43\text{ m}$ in deep mountain gorge backwaters.

### Stage 2: Spillway Breadth-First Flat Resolution
When depressions are filled, the interior becomes a horizontal lake surface with elevation $z$ ($40,893\text{ cells}$). To assign continuous flow directions without adding arbitrary elevation gradients:
1. Identify all flat cells bordering resolved terrain where neighbor elevation $\le z$ and neighbor `flow_dir != 0` (the spillway cells).
2. Seed a FIFO queue with these spillway cells.
3. Perform a breadth-first expansion into the interior of the flat lake, pointing each flat cell toward its neighbor that has a shorter path to the spillway.
4. **Result**: 100% of flat lake cells receive a continuous D8 downstream flow pointer directed toward the natural spillway outlet.

---

## 4. Intermediate Artifact Register

All conditioned rasters have been generated and saved to `data/processed/spatial/catchment/`:

| Artifact Path | Format | Dimensions | File Size | Description |
| :--- | :--- | :--- | :--- | :--- |
| `hathnikund_conditioned_dem.tif` | GeoTIFF (Float32) | 1200 × 1200 | 5,060,084 B | Hydrologically conditioned DEM with filled depressions. |
| `hathnikund_flow_direction.tif` | GeoTIFF (UInt8) | 1200 × 1200 | 492,152 B | D8 flow direction codes (1, 2, 4, 8, 16, 32, 64, 128) with flat routing. |
| `hathnikund_flow_accumulation.tif` | GeoTIFF (Int32) | 1200 × 1200 | 1,294,015 B | Contributing upstream cell count for each grid cell. |
| `hathnikund_watershed_raster.tif` | GeoTIFF (UInt8) | 1200 × 1200 | 13,192 B | Binary watershed mask (1 = upstream basin, 0 = outside). |
| `hathnikund_stream_raster.tif` | GeoTIFF (UInt8) | 1200 × 1200 | 19,394 B | Extracted stream network raster ($A \ge 1,000\text{ cells}$). |

---
**Status**: Methodologically Verified and Documented for Phase 3D.3.

