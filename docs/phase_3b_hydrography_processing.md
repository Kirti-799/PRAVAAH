# Phase 3B: Hydrography Validation & Processing Specification

**Project:** PRAVAAH (Predictive Risk Assessment and Vulnerability Analysis for Adaptive Assistance & Humanitarian Response)  
**Milestone:** Phase 3B — River Hydrography & Network Integration  
**Implementation Modules:** `ml/spatial/hydrography.py`, `backend/app/services/spatial.py`, `backend/app/schemas/spatial.py`  

---

## 1. Overview & Processing Architecture

The Hydrography Processing Pipeline (`HydrographyProcessor`) ingests, cleanses, validates, reprojects, and classifies vector waterway networks within the Upper-to-Middle Yamuna River Corridor.

```
Raw Vector File (GeoJSON / Shapefile / GeoPackage)
                    │
                    ▼
┌────────────────────────────────────────────────────────┐
│             Hydrography Processing Pipeline             │
│        (`HydrographyProcessor.validate_and_process`)   │
├────────────────────────────────────────────────────────┤
│ 1. Format Verification & Path Traversal Guards         │
│ 2. CRS Inspection & Reprojection (EPSG:32643 UTM 43N)  │
│ 3. Geometry Audit (Empty & Invalid Geometry Removal)   │
│ 4. Coordinate Range & Duplicate Geometry De-duplication│
│ 5. Spatial Clipping to Study Corridor Extent           │
│ 6. Evidence-Based Waterway Classification              │
│ 7. Metric Geodesic Length Calculations (meters/km)     │
│ 8. Main Channel Extraction & Continuity / Gap Analysis │
│ 9. NetworkX Graph Representation & Topology Metrics    │
│ 10. Downstream Station Chainage Derivation             │
└────────────────────────────────────────────────────────┘
                    │
                    ▼
Processed GeoDataFrame & HydrographyProcessingReport
```

---

## 2. Ingestion & Validation Protocols

### 2.1 File System Confinement
All candidate hydrography files must reside physically within:
- `data/raw/spatial/hydrography/` (raw unedited vector sources), or
- `data/processed/spatial/hydrography/` (clipped, cleaned, or cached outputs).
Directory traversal attempts using relative separators (`..`, `/`, `\`) are strictly blocked by the backend service.

### 2.2 Coordinate Reference Systems & Metric Scaling
Public vector extracts (OSM, GeoJSON) are predominantly distributed in **WGS 84 Geographic Coordinates (`EPSG:4326`)** where coordinates are expressed in decimal degrees.
- Direct Euclidean length calculations in degrees introduce unacceptable spatial distortion (up to $100,000\times$).
- The pipeline parses native CRS and reprojects geometries to **`EPSG:32643` (WGS 84 / UTM Zone 43N)**, the official metric projected coordinate system for Haryana and Delhi NCR.
- All linear reach lengths (`length_m`, `length_km`, and cumulative chainage) are derived exclusively in UTM Zone 43N.

### 2.3 Geometry Cleansing & Duplicate Removal
1. **Empty and Null Geometries:** Features with empty coordinates or null geometries are pruned from the dataset.
2. **Invalid Geometries:** Self-intersecting lines or degenerate rings are cleaned using topological `buffer(0)`.
3. **Duplicate Features:** Duplicate geometry polylines (identical WKT coordinate signatures) are identified and de-duplicated to prevent double-counting of river lengths.

### 2.4 Study Corridor Clipping
Features are clipped to the authoritative PRAVAAH rectangular study area bounds:
$$\text{West: } 76.85^\circ\text{ E}, \quad \text{South: } 28.50^\circ\text{ N}, \quad \text{East: } 77.60^\circ\text{ E}, \quad \text{North: } 30.40^\circ\text{ N}$$
Segments crossing the boundary are cleanly intersected; features lying entirely outside are excluded.

---

## 3. Evidence-Based Waterway Classification

To prevent misrepresenting canals or drains as the main natural river, `HydrographyProcessor.classify_feature()` applies strict, attribute-driven classification rules based on source tags:

| Category | Identifying Tags & Source Evidence | Physical / Hydrological Role |
| :--- | :--- | :--- |
| **Main River (`main_river`)** | `waterway=river` AND (`name` matches Yamuna / Jumna / Jamuna) AND NOT `canal` / `drain`. | Primary natural thalweg and high-discharge conveyance channel. |
| **Tributaries (`tributary`)** | `waterway=river` or `stream` with names matching known Yamuna tributaries (Hindon, Som, Boli, Maskara, Pathrala, Budhi Yamuna). | Contributing upstream watersheds and inflow hydrographs. |
| **Canals (`canal`)** | `waterway=canal` or names matching Western Yamuna Canal (WYC), Eastern Yamuna Canal (EYC), Agra Canal, Munak Canal. | Engineered irrigation and municipal water diversion channels. |
| **Drains / Minor (`drain_minor`)** | `waterway=drain` or `ditch` or names matching Najafgarh Drain, Barapullah, Shahdara Drain, Supplementary Drain. | Urban stormwater runoffs and treated effluent channels. |
| **Embankments (`embankment`)** | `man_made=dyke` or `man_made=embankment` or `barrier=embankment` or `flood_protection=yes` or `bund`/`bundh`. | Earthen marginal bunds and flood-defense levees. |
| **Ambiguous (`ambiguous`)** | Unnamed waterways lacking conclusive classification tags. | Explicitly cataloged as ambiguous; never guessed from geometry alone. |

---

## 4. Main Channel Extraction & Continuity / Gap Analysis

A primary requirement of Phase 3B is establishing whether the Yamuna main channel forms a continuous hydraulic thalweg from Hathnikund Barrage down to Delhi.

### Gap Analysis Methodology (`analyze_channel_continuity`):
1. Filters features classified as `main_river`.
2. Reprojects to UTM Zone 43N meters.
3. Sorts reach segments geographically from upstream (North) to downstream (South).
4. Computes Euclidean endpoint-to-startpoint gap distances between consecutive segments:
   $$d_{\text{gap}} = \text{dist}(\text{Reach}_{i,\text{end}}, \text{Reach}_{i+1,\text{start}})$$
5. Evaluates continuity status:
   - **`CONTINUOUS`:** All sequential reaches connect within snapping tolerance ($d_{\text{gap}} \le 25\text{ m}$).
   - **`FRAGMENTED`:** Minor localized gaps ($\le 3$ gaps, $d_{\text{gap}} < 500\text{ m}$) attributable to unmapped bridge crossings or island braids.
   - **`DISCONNECTED`:** Significant breaks ($> 500\text{ m}$), missing reaches, or severe digitizing gaps.
