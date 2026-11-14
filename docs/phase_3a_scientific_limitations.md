# Phase 3A: Scientific Limitations & Geospatial Guardrails

**Project:** PRAVAAH (Predictive Risk Assessment and Vulnerability Analysis for Adaptive Assistance & Humanitarian Response)  
**Milestone:** Phase 3A — Spatial Data Infrastructure & Terrain Processing  
**Document:** Mandatory Scientific Guardrails, Analytical Boundaries, and Known Limitations  

---

## 1. Core Scientific Limitations & Explicit Prohibitions

In adherence to scientific integrity principles, the following technical and operational limitations are strictly maintained across PRAVAAH Phase 3A:

### 1. Routing Model Is Uncalibrated
The Muskingum hydrological routing prototype (`ml/routing/muskingum.py`) implemented in Phase 2C-B remains a parameter-explicit, uncalibrated mathematical routing prototype. It is **not** calibrated against observed downstream discharge or water-level observations at Delhi Old Railway Bridge (CWC Station 028-MDD).

### 2. No Operational Delhi Water-Level Forecast
The system **does not** provide an operational Delhi water-level or flood stage forecast. Upstream Hathnikund discharge estimates (Phase 2B) and routing simulations (Phase 2C-B) illustrate flood-wave transit timing under theoretical parameters; they do not predict exact river stage at Delhi.

### 3. Discharge Cannot Be Converted to Stage Without a Rating Curve
Volumetric river discharge ($Q$, in $\text{m}^3/\text{s}$ or cusecs) cannot be converted to water level/stage ($H$, in meters above MSL) without an authoritative, surveyed stage-discharge rating curve ($Q = a(H - H_0)^b$) calibrated for the Old Railway Bridge section. No synthetic or assumed rating curves are applied.

### 4. Terrain Elevation Alone Cannot Establish Inundation Extent
A Digital Elevation Model (DEM) represents the bare-earth or top-of-canopy topography. **Terrain elevation alone cannot establish flood inundation extent.** Accurate flood inundation modeling requires:
- Dynamic hydrodynamic shallow-water equations (1D/2D Saint-Venant solvers),
- River cross-section bathymetry (below the water surface),
- Embankment, bund, and drainage regulator structures,
- Time-varying hydrograph inputs and boundary conditions.
A low-lying terrain cell near the river is **not** automatically classified as flooded (bathtub models are scientifically invalid in complex alluvial corridors).

### 5. Study Area Is an Analytical Extent, Not a Watershed Boundary
The study area defined in `ml/spatial/study_area.py` ($76.85^\circ\text{ E} - 77.60^\circ\text{ E}$, $28.50^\circ\text{ N} - 30.40^\circ\text{ N}$) is explicitly an **analytical rectangular bounding box**. It encompasses the Yamuna transit corridor from Hathnikund Barrage to Delhi.
- It is **not** a verified watershed boundary.
- It is **not** a floodplain boundary.
- It must not be labeled or presented as a verified flood catchment.

### 6. Low Elevation Alone Does Not Establish Evacuation Safety
Topographic elevation does not equate to evacuation safety:
- Low-lying areas protected by certified ring bunds and floodwalls may remain dry.
- High-elevation mounds or bridge abutments lacking egress routes may become isolated "islands" surrounded by high-velocity flood flows.
- Determining evacuation safety requires structural integrity assessment, egress road network analysis, and velocity hazard mapping.

---

## 2. Geospatial Labeling Rules

To prevent misinterpretation by emergency managers and downstream users, strict labeling conventions are enforced in all API schemas, code variables, documentation, and frontend user interfaces:

### Permitted Geospatial Labels:
- `Source DEM`
- `Terrain elevation`
- `Terrain slope`
- `Study-area extent`
- `Candidate analysis area`
- `Coverage unavailable`
- `Uncalibrated routing scenario`

### Prohibited Geospatial Labels:
- ❌ `Predicted flood zone`
- ❌ `Verified inundation boundary`
- ❌ `Safe evacuation zone`
- ❌ `Flood depth forecast`
- ❌ `Population at risk`
- ❌ `Evacuation shelter`

---

## 3. Elevation Datum and Vertical Uncertainty

1. **Global DEM Vertical Datums:**
   - NASA SRTM uses the WGS 84 / EGM96 geoid.
   - Copernicus DEM GLO-30 uses the EGM2008 geoid.
   - Survey of India benchmarks and CWC river gauges reference the Indian Mean Sea Level (MSL / GTS Datum, Karachi/Mumbai datum origin).
   - Differences between EGM96, EGM2008, and local GTS MSL can vary by several decimeters across the Yamuna corridor.
2. **Vertical Resolution & Accuracy:**
   - 30-meter global DEMs exhibit absolute vertical errors ($\text{LE90}$) of approximately $5\text{ m} - 10\text{ m}$.
   - In low-gradient river channels where stage variations of $1\text{ m} - 2\text{ m}$ represent the difference between normal flow and devastating inundation, raw 30m DEMs without high-resolution LiDAR or DGPS river cross-sections cannot establish flood stage depths.

---

## 4. Isolation of Synthetic Fixtures

Synthetic raster fixtures generated within unit tests (`DEMValidator.create_synthetic_dem_fixture`) are:
1. Created with localized, synthetic elevation gradients (e.g., tilted planes with deterministic slopes) solely to verify numerical convergence of gradient filters and JSON serialization.
2. Strictly isolated from the production catalog and filesystem.
3. Never displayed on the user interface as real topography.
4. When public elevation tiles are not present in `data/raw/spatial/dem/`, the system truthfully and explicitly displays `UNAVAILABLE_IN_REPOSITORY`.
