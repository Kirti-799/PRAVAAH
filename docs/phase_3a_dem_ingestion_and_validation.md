# Phase 3A: DEM Ingestion & Raster Validation Specification

**Project:** PRAVAAH (Predictive Risk Assessment and Vulnerability Analysis for Adaptive Assistance & Humanitarian Response)  
**Milestone:** Phase 3A — Spatial Data Infrastructure & Terrain Processing  
**Document:** Digital Elevation Model Ingestion and Geodetic Validation Protocol  
**Implementation Modules:** `ml/spatial/dem.py`, `backend/app/services/spatial.py`, `backend/app/api/routes/spatial.py`

---

## 1. Overview & Architecture

Digital Elevation Models (DEMs) form the spatial foundation for hydrodynamic slope analysis, overland flow direction, and catchment delineations. In operational disaster intelligence, faulty elevation data—such as inverted geotransforms, unmasked NoData voids, non-finite values, or incorrect horizontal/vertical units—can lead to catastrophic misinterpretations of flood risk.

PRAVAAH Phase 3A establishes a deterministic, automated DEM inspection and validation engine (`DEMValidator`) implemented with `rasterio`, `numpy`, and `shapely`.

```
Raw GeoTIFF File (data/raw/spatial/dem/<name>.tif)
                      │
                      ▼
┌────────────────────────────────────────────────────────┐
│             DEM Ingestion & Validation Pipeline         │
│             (`DEMValidator.inspect_dem_file`)          │
├────────────────────────────────────────────────────────┤
│ 1. Path Traversal & Existence Guards                   │
│ 2. Raster Format & Band Count Validation               │
│ 3. CRS & Geodetic Coordinate Frame Extraction          │
│ 4. Affine Geotransform & Pixel Resolution Checks       │
│ 5. Geodetic Boundary & Study-Area Overlap Check        │
│ 6. NoData Masking & Non-Finite Detection (NaN/Inf)     │
│ 7. Elevation Distribution Statistics (Min/Max/Mean/Std)│
│ 8. Plausible Yamuna Elevation Range Diagnostics        │
└────────────────────────────────────────────────────────┘
                      │
                      ▼
         DEMMetadataReport / JSON Response
```

---

## 2. Ingestion & Validation Protocols

### 2.1 File System Confinement & Path Security
To prevent arbitrary filesystem traversal vulnerabilities, callers cannot provide arbitrary absolute filesystem paths.
- All candidate DEMs must be physically located within the configured directory: `data/raw/spatial/dem/`.
- File resolution parses only the base file name (`Path(filename).name`), stripping any directory traversal characters (`..`, `/`, `\`).
- If the resolved path does not exist or is outside the sandbox, the engine returns an HTTP 422 or 404 structured error.

### 2.2 Raster Format and Band Structure
- **Format:** GeoTIFF (`.tif`, `.tiff`), Cloud-Optimized GeoTIFF (COG), or HGT.
- **Band Count:** Validated to contain at least 1 elevation band. Phase 3A processes Band 1 as elevation surface data.
- **Data Types:** Readily handles `float32`, `float64`, `int16`, `int32`, `uint16`. Multi-band imagery or non-raster files are rejected.

### 2.3 Coordinate Reference System (CRS)
- The raster CRS is parsed and validated using `rasterio.crs.CRS`.
- Rasters lacking CRS definitions (unreferenced rasters) are marked `is_valid: false` with validation error `"Raster is missing Coordinate Reference System (CRS) metadata"`.
- Both Geographic CRS (`EPSG:4326`, WGS 84 ellipsoidal coordinates) and Projected CRS (`EPSG:32643`, UTM Zone 43N) are supported and properly cataloged.

### 2.4 Affine Geotransform & Spatial Resolution
- Affine transformation matrices are evaluated via `dataset.transform`.
- Resolution along the X and Y axes is extracted: `(pixel_width, pixel_height)`.
- If either pixel dimension is zero or negative (in scale), or if the affine matrix is singular/degenerate, the raster fails validation.

### 2.5 Study Area Spatial Coverage
- The bounding box `(west, south, east, north)` is computed from the raster bounds.
- The bounds are cross-referenced against the official Yamuna Upper-to-Delhi Study Area bounds:
  - West: `76.85° E`, South: `28.50° N`, East: `77.60° E`, North: `30.40° N`.
- The engine computes spatial overlap. If the DEM falls completely outside the study corridor, a diagnostic warning is attached to the report.

---

## 3. Cell Data Integrity & NoData Protocol

### 3.1 Non-Finite Value Detection
Unchecked IEEE `NaN` (Not a Number), `+Infinity`, and `-Infinity` values in raster arrays break down-stream scientific calculations (mean, standard deviation, gradient filters).
- The validator performs an explicit `np.isnan(raw_data) | np.isinf(raw_data)` scan across all raster pixels.
- The count of non-finite values is recorded.
- Non-finite values are automatically appended to the invalid-data mask.

### 3.2 NoData Value Masking
- The raster metadata NoData tag (`dataset.nodata`) is extracted (e.g., `-9999.0`, `-32768`).
- A composite boolean mask is constructed:
  $$\text{Mask}_{\text{invalid}} = \text{isnan}(Z) \lor \text{isinf}(Z) \lor (Z == \text{nodata})$$
- The percentage of missing/invalid cells is computed:
  $$\% \text{Missing} = \frac{\sum \text{Mask}_{\text{invalid}}}{N_{\text{rows}} \times N_{\text{cols}}} \times 100$$
- If $\% \text{Missing} > 50\%$, the dataset is flagged with a diagnostic warning for low data coverage.
- If $\% \text{Missing} == 100\%$ (empty raster), validation fails immediately with `is_valid: false`.

---

## 4. Elevation Statistics & Plausibility Diagnostics

### 4.1 Statistical Distribution
For valid, unmasked cells, the engine calculates:
- Minimum elevation ($Z_{\text{min}}$)
- Maximum elevation ($Z_{\text{max}}$)
- Arithmetic mean elevation ($Z_{\text{mean}}$)
- Standard deviation of elevation ($Z_{\text{std}}$)

### 4.2 Plausible Elevation Bounds for Yamuna Corridor
The Yamuna river corridor between Hathnikund Barrage (Yamunanagar, Haryana) and Old Railway Bridge (Delhi) traverses the Siwalik foothills down through the Indo-Gangetic alluvium:
- **Baseline low elevation (Delhi Okhla / ORB):** $\approx 195\text{ m}$ to $210\text{ m}$ above MSL.
- **Foothills elevation (Hathnikund / Tajewala):** $\approx 300\text{ m}$ to $360\text{ m}$ above MSL.
- **Immediate catchment ridgelines:** Up to $\approx 1200\text{ m} - 1500\text{ m}$.

The validator implements an automated plausibility diagnostic range:
- Lower threshold: `150.0 m`
- Upper threshold: `1500.0 m`

> [!IMPORTANT]
> **Diagnostic Purpose Only:** Elevation range checks are treated strictly as heuristic diagnostics to identify unit mismatches (e.g., feet vs meters) or unmasked negative fill values. They are **not** unquestioned proof of topographic correctness.

---

## 5. Separation of Synthetic Test Fixtures from Production Data

1. **Unit Testing Isolation:**
   - In `ml/tests/test_spatial.py` and `backend/tests/test_spatial.py`, `DEMValidator.create_synthetic_dem_fixture` is used to create tiny, deterministic in-memory/temporary GeoTIFF rasters (e.g., $20 \times 20$ grid) solely to test:
     - Affine matrix parsing
     - Geodesic slope algorithms
     - NoData masking and non-finite error handling
     - REST API status code contracts
2. **Strict Production Prohibition:**
   - Synthetic fixtures are deleted immediately after test teardown.
   - Synthetic data is **never** committed to `data/raw/spatial/dem/`.
   - The production backend scans the physical filesystem. If no real GeoTIFF exists, it returns `status: UNAVAILABLE`. PRAVAAH never substitutes synthetic elevation files into production workflows.
3. **Final Verification Classification:**
   - **Tested with synthetic data:** Deterministic test fixtures verify affine coordinates, Horn's finite-difference slope calculation, NoData masking, and HTTP inspection contracts.
   - **Real-data validation:** Remains strictly pending physical ingestion of authenticated multi-tile GeoTIFF rasters for the Upper-to-Middle Yamuna Plain.
