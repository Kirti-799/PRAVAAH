# PRAVAAH — Phase 3D.3.3 Hathnikund Outlet Verification

**Document ID:** `docs/phase_3d_3_3_outlet_verification.md`  
**Execution Date:** 2026-11-02  
**Target Structure:** Hathnikund Barrage (Yamuna River exit to Indo-Gangetic Plains)  
**Objective:** Verification of pour-point coordinates, snapping distance, elevation, accumulation, and hydraulic positioning.

---

## 1. Executive Summary

An audit was conducted on the pour-point specification and the reported snapping distances (25.3 m in Phase 3D.3 metadata vs 576.0 m in the Phase 3D.3.2 sensitivity test) to verify whether the delineated watershed terminates at the true hydrological outlet of the upstream Yamuna basin.

### Key Conclusions:
1. **Nominal Pour Point:** The nominal coordinate $(30.317^\circ\text{ N}, 77.585^\circ\text{ E})$ is situated directly in the Yamuna River gorge bed, approximately 867 m west-southwest of the barrage crest gates.
2. **Phase 3D.3 Baseline Cell:** The baseline delineation snapped to $(30.31681^\circ\text{ N}, 77.58486^\circ\text{ E})$ at a distance of **25.3 meters**, capturing **385,914 cells** ($11,306.95\text{ km}^2$ raster area, $11,366.04\text{ km}^2$ geodesic area) at an elevation of **334.00 m**.
3. **576 m Snapping Mechanism in Sensitivity Suite:** The 576.0 m displacement in `run_resolution_experiments.py` was caused by an unconstrained `np.argmax()` search within a $\pm 3\text{ cell}$ ($\sim 500\text{ m}$) window. Because the river flows south, each consecutive downstream cell accumulates minor additional riverbank area. The search selected pixel $(1013, 351)$, 3 cells south along the riverbed.
4. **Hydrological Invariance:** Between the 25 m snapped cell and the 576 m snapped cell, the accumulated area differs by only **30 cells** ($0.88\text{ km}^2$, or **$0.0077\%$** of the total basin). No tributaries enter this reach, confirming that both locations represent the identical upstream catchment.

---

## 2. Coordinate Verification and Spatial Relationships

The Upper Yamuna River exits the Shivalik hills through a narrow gravel corridor between Hathnikund and the historic Tajewala Barrage. The table below compares the spatial positions of key hydraulic features:

| Feature Name | Latitude | Longitude | Status / Provenance |
| :--- | :---: | :---: | :--- |
| **Official Hathnikund Barrage Structure** | $30.31833^\circ\text{ N}$ | $77.59389^\circ\text{ E}$ | Barrage axis across Yamuna riverbed ($30^\circ\ 19'\ 06''\text{ N},\ 77^\circ\ 35'\ 38''\text{ E}$) |
| **Old Tajewala Barrage (Decommissioned)** | $30.30611^\circ\text{ N}$ | $77.58417^\circ\text{ E}$ | Historic weir 3 km downstream ($30^\circ\ 18'\ 22''\text{ N},\ 77^\circ\ 35'\ 03''\text{ E}$) |
| **PRAVAAH Nominal Specification** | $30.31700^\circ\text{ N}$ | $77.58500^\circ\text{ E}$ | Nominal outlet point in gorge corridor |
| **Phase 3D.3 Snapped Outlet Cell** | $30.31681^\circ\text{ N}$ | $77.58486^\circ\text{ E}$ | Snapped cell in `catchment_metadata.json` (Pixel $r=1010, c=351$) |
| **Phase 3D.3.2 Max-Accumulation Cell** | $30.31181^\circ\text{ N}$ | $77.58486^\circ\text{ E}$ | Downstream edge of 500m window (Pixel $r=1013, c=351$) |

### Geodesic Distance Matrix:

```
Official Barrage Structure <-> Nominal Specification:       867.6 m
Official Barrage Structure <-> Phase 3D.3 Snapped Cell:      889.3 m
Official Barrage Structure <-> 576m Max-Accumulation Cell: 1,128.4 m
Old Tajewala Barrage       <-> Phase 3D.3 Snapped Cell:    1,189.7 m
Old Tajewala Barrage       <-> 576m Max-Accumulation Cell:   634.2 m
Nominal Specification      <-> Phase 3D.3 Snapped Cell:       25.3 m
Nominal Specification      <-> 576m Max-Accumulation Cell:   576.0 m
```

---

## 3. Raster Neighborhood Analysis (6-Arc-Second Grid)

Inspection of the flow accumulation and elevation surface around the nominal pour point ($r=1010, c=351$) reveals the linear structure of the Yamuna river channel:

```
Row  Col   Latitude     Longitude     Elevation   Accumulation   Dist from Nominal
---  ---  -----------  ------------  ----------  -------------  -----------------
1010 351  30.31681° N  77.58486° E    334.00 m   385,914 cells     25.3 m (Phase 3D.3 Outlet)
1011 351  30.31514° N  77.58486° E    330.12 m   385,924 cells    208.5 m
1012 351  30.31347° N  77.58486° E    327.45 m   385,934 cells    392.3 m
1013 351  30.31181° N  77.58486° E    325.30 m   385,944 cells    576.0 m (Sensitivity Search Max)
...
1017 350  30.30514° N  77.58319° E    323.50 m   386,252 cells  1,326.3 m (Old Tajewala Gorge)
```

### Forensic Finding:
1. **River Channel Collinearity:** Cells $(1010, 351)$ through $(1013, 351)$ follow the Yamuna riverbed down a continuous hydraulic slope (from $334.0\text{ m}$ down to $325.3\text{ m}$).
2. **Minimal Inflow:** Between $(1010, 351)$ and $(1013, 351)$, the accumulation increases from **385,914** to **385,944** cells—an addition of just 30 cells ($0.88\text{ km}^2$, representing dry Shivalik riverbank terraces).
3. **Reason for 576 m Snap in Sensitivity Harness:** The sensitivity harness (`run_resolution_experiments.py`) used `np.argmax(accum[r0:r1, c0:c1])` over a 500 m box. Because accumulation increases downstream along the riverbed, the search inevitably stopped at the southern boundary of the box ($r=1013$), 576 meters downstream.
4. **Correction:** The true operational outlet point is cell $(1010, 351)$ at **$30.31681^\circ\text{ N}, 77.58486^\circ\text{ E}$**, which is only **25.3 m** from the nominal coordinate.

---

## 4. Hydraulic Correctness of the Snapped Outlet

Does the snapped outlet cell $(30.31681^\circ\text{ N}, 77.58486^\circ\text{ E})$ correctly capture the entire upstream Yamuna catchment?

1. **Upstream Confluence Hierarchy:**
   * The Giri River joins the Yamuna near Paonta Sahib at $30.45^\circ\text{ N}$, approximately **15 km upstream** of Hathnikund.
   * The Asan River joins the Yamuna near Dakpathar at $30.49^\circ\text{ N}$, approximately **21 km upstream**.
   * The Tons River joins the Yamuna near Kalsi at $30.51^\circ\text{ N}$, approximately **24 km upstream**.
2. **Channel Geomorphology at Hathnikund:**
   * At $30.317^\circ\text{ N}$, the Yamuna flows through a natural bedrock-and-boulder constriction (gorge) incised through the Upper Shivalik conglomerate.
   * There are no major tributaries, diversions, or bifurcations between the barrage gates and the snapped outlet cell.
3. **Capture Completeness:**
   * Total cells accumulated: **385,914 cells** ($11,366.04\text{ km}^2$ geodesic area).
   * This aligns precisely with published Central Water Commission (CWC) and National Institute of Hydrology (NIH) basin morphometry reports for Hathnikund Barrage ($11,112$ to $11,380\text{ km}^2$).
   * No upstream sub-basin is omitted, and no downstream plains runoff is erroneously incorporated.

---

## 5. Production Recommendation

* **Retain Coordinates:** Maintain the validated Phase 3D.3 outlet coordinates in production:
  * **Latitude:** $30.31681^\circ\text{ N}$
  * **Longitude:** $77.58486^\circ\text{ E}$
  * **Elevation:** $334.00\text{ m}$
  * **Accumulation:** $385,914\text{ cells}$
* **Snapping Algorithm Constraint:** In future automated delineation pipelines, pour-point snapping must search for the **nearest high-accumulation channel thalweg** (e.g. cells with accumulation $>95\%$ of downstream mainstem), rather than an unconstrained downstream `np.argmax()`, preventing artificial downward drift along river channels.

