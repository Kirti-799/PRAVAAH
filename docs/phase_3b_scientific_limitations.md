# Phase 3B: Scientific Limitations & Geospatial Guardrails

**Project:** PRAVAAH (Predictive Risk Assessment and Vulnerability Analysis for Adaptive Assistance & Humanitarian Response)  
**Milestone:** Phase 3B — River Hydrography & Network Integration  
**Document:** Mandatory Scientific Guardrails, Analytical Boundaries, and Known Limitations  

---

## 1. Core Scientific Limitations & Explicit Prohibitions

In adherence to disaster-intelligence scientific standards, the following technical guardrails are strictly maintained across PRAVAAH Phase 3B:

### 1. River Centerlines Do Not Denote Inundation Extent
A vector river centerline represents the planimetric alignment of the river thalweg or primary channel bed.
- **A river line alone CANNOT determine flood inundation extent.**
- Accurate flood inundation mapping requires hydrodynamic shallow-water solvers (1D/2D Saint-Venant equations), boundary discharge hydrographs, river cross-section bathymetry, and terrain hydraulic roughness coefficients.
- Drawing arbitrary buffer distances around river polylines to simulate flood zones is scientifically invalid and strictly prohibited.

### 2. River Centerlines Do Not Reflect Bathymetry or Depth
OpenStreetMap and public vector datasets do not contain underwater bathymetric profiles, riverbed elevations, or channel cross-sections.
- Invert elevation and stage depth cannot be derived from vector polylines.
- Channel cross-section geometry cannot be assumed rectangular or uniform across reaches.

### 3. Mapped Embankments Lack Certified Crest Elevations
Vector features tagged as `embankment`, `dyke`, or `bund` represent planimetric linear traces of flood-protection structures.
- **Planimetric lines alone do not establish flood-protection safety.**
- Mapped embankments lack certified crest elevations (top of bund MSL height), structural compaction data, revetment conditions, and breach history.
- Emergency responders must not assume that an area behind a mapped embankment is safe from overtopping or piping failure during peak flood stages.

### 4. Undirected Topological Reaches (Flow Direction Guard)
Vector lines in OpenStreetMap and public shapefiles reflect the coordinate order in which they were digitized by individual mappers.
- Flow direction cannot be inferred solely from digitizing vertex order.
- Reach edges are modeled as undirected in topology calculations unless confirmed by hydraulic drop or hydrodynamic verification.

### 5. No Synthetic Channel Substitution on Missing Reaches
If an acquired river network exhibits gaps or missing reaches:
- Synthetic straight lines or interpolated vectors are **never** substituted for authentic river geometry.
- The system truthfully reports `ChannelContinuityStatus.DISCONNECTED` and refuses to calculate misleading cumulative chainage distances.

---

## 2. Geospatial Labeling Rules

To prevent misinterpretation by emergency planners and operational commanders, strict labeling conventions are enforced in all API schemas, code variables, documentation, and frontend user interfaces:

### Permitted Geospatial Labels:
- `River centerline`
- `River thalweg`
- `Hydrographic reach`
- `Tributary alignment`
- `Canal diversion`
- `Drainage channel`
- `Mapped embankment alignment`
- `River chainage (km)`
- `Reach network graph`

### Strictly Prohibited Labels:
- ❌ `Predicted flood zone`
- ❌ `Verified flood boundary`
- ❌ `Safe evacuation corridor`
- ❌ `Flood protection guarantee`
- ❌ `Flood depth forecast`
- ❌ `Inundation perimeter`

---

## 3. Synthetic Fixture Isolation Policy

Synthetic hydrography fixtures generated within unit tests (`HydrographyProcessor.create_synthetic_hydrography_fixture`) are:
1. Created with deterministic coordinate geometries solely to verify mathematical algorithms (NetworkX topology, gap calculations, metric projections).
2. Explicitly tagged with `is_synthetic_fixture: true` and warning disclaimers in GeoJSON properties.
3. Strictly isolated within temporary test directories.
4. Never presented in the production catalog or displayed on user dashboards as authentic geography.
