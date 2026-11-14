# Phase 3A: Spatial Data Inventory & Provenance Register

**Project:** PRAVAAH (Predictive Risk Assessment and Vulnerability Analysis for Adaptive Assistance & Humanitarian Response)  
**Milestone:** Phase 3A — Spatial Data Infrastructure & Terrain Processing  
**Audit Date:** October 2026  
**Status:** Ingestion Framework Verified | Spatial Datasets Cataloged | Repository Files Unacquired  

---

## 1. Executive Summary

Phase 3A establishes the core spatial data infrastructure and geodetic coordinate contracts for PRAVAAH.

In strict compliance with PRAVAAH scientific integrity standards, this inventory formally documents all candidate elevation, hydrographic, and administrative boundaries. It explicitly distinguishes between:
- **Available Datasets:** Physically present, checksum-verified, and inspected in the local filesystem.
- **Unavailable / Unacquired Datasets:** Officially cataloged and candidate sources that have **not** been downloaded or committed to the repository.

Under no circumstances are synthetic rasters substituted for unacquired public elevation models.

---

## 2. Comprehensive Spatial Dataset Inventory

| Dataset ID | Official Title | Data Category | Source Agency & Portal | Nominal Resolution | Native CRS & Datum | Repository Status | Storage Path | Acquisition Blockers & Access Notes |
| :--- | :--- | :--- | :--- | :---: | :--- | :---: | :--- | :--- |
| `SRTM_30M_GLOBAL` | NASA SRTM 1 Arc-Second Global Elevation (SRTMGL1 v003) | Digital Elevation Model (DEM) | NASA / USGS LP DAAC ([USGS Portal](https://lpdaac.usgs.gov/products/srtmgl1v003/)) | 1 arc-second (~30 m) | EPSG:4326 (WGS 84, EGM96 Geoid) | **UNAVAILABLE_IN_REPOSITORY** | `data/raw/spatial/dem/srtm_yamuna_30m.tif` | Requires credentialed Earthdata Login; tiles covering N28E077, N29E077, N30E077 have not been downloaded. |
| `COPERNICUS_GLO30` | Copernicus DEM GLO-30 | Digital Elevation Model (DEM) | European Space Agency (ESA) / Airbus ([ESA Portal](https://spacedata.copernicus.eu/)) | 1 arc-second (~30 m) | EPSG:4326 (WGS 84, EGM2008 Geoid) | **UNAVAILABLE_IN_REPOSITORY** | `data/raw/spatial/dem/copernicus_glo30_yamuna.tif` | Requires AWS S3 / Planetary Computer public bucket access or Copernicus Open Access registration. |
| `BHUVAN_CARTODEM_30M` | ISRO Bhuvan CartoDEM 30m Version 3R1 | Digital Elevation Model (DEM) | National Remote Sensing Centre (NRSC) / ISRO ([Bhuvan Portal](https://bhuvan-app1.nrsc.gov.in/)) | 30 m | EPSG:4326 (WGS 84 Ellipsoidal) | **UNAVAILABLE_IN_REPOSITORY** | `data/raw/spatial/dem/cartodem_yamuna_30m.tif` | Requires OTP-authenticated Indian user registration; bulk API downloads are restricted under national mapping policies. |
| `OSM_YAMUNA_HYDROGRAPHY` | OpenStreetMap Yamuna Corridor Waterways & Embankments | Hydrography & River Centerlines | OpenStreetMap Contributors / Geofabrik ([Geofabrik Extracts](https://download.geofabrik.de/asia/india.html)) | Vector features (lines/polygons) | EPSG:4326 (WGS 84) | **UNAVAILABLE_IN_REPOSITORY** | `data/raw/spatial/hydrography/osm_yamuna_waterways.geojson` | Requires downloading India/Northern Zone PBF extract and spatially clipping to Yamuna transit corridor bounds. |
| `DDA_O_ZONE_FLOODPLAIN` | Delhi Master Plan Zone-O (River Yamuna Floodplain) | Administrative Boundary | Delhi Development Authority (DDA) / Delhi I&FC ([DDA Master Plan](https://dda.gov.in/)) | Vector polygon | EPSG:4326 / Local Survey Grid | **UNAVAILABLE_IN_REPOSITORY** | `data/raw/spatial/boundaries/delhi_dda_zone_o.geojson` | Published predominantly as static PDF Master Plan documents; vector GIS layer restricted across municipal agencies. |

---

## 3. Physical Directory Audit

A recursive scan of the local filesystem confirmed:
- `data/raw/spatial/dem/`: Directory exists; currently contains **0 raster files** (`.tif` / `.tiff`).
- `data/raw/spatial/hydrography/`: Directory staged; contains **0 vector files**.
- `data/raw/spatial/boundaries/`: Directory staged; contains **0 vector files**.

### Policy Enforcement:
When `GET /api/spatial/dem/status` is called, the backend scans `data/raw/spatial/dem/` and returns an explicit `UNAVAILABLE` status with clear ingestion guidance. No mock elevation layers or pretend flood depths are returned.

---

## 4. Final Phase 3A Verification Matrix

| Component | Status | Test Mechanism | Notes / Evidence |
| :--- | :--- | :--- | :--- |
| **Spatial Dataset Inventory** | **Implemented & Tested** | `ml/tests/test_spatial.py::test_spatial_inventory_catalog_entries` | Authoritative catalog of 5 datasets with provenance, resolution, and blockers. |
| **Study Area Contract & CRS** | **Implemented & Tested** | `ml/tests/test_spatial.py::test_authoritative_study_area_metadata` | Verified rectangular bounding box [76.85°E–77.60°E, 28.50°N–30.40°N], EPSG:4326 & EPSG:32643. |
| **DEM Ingestion & Validation** | **Tested with Synthetic Data** | `ml/tests/test_spatial.py::test_dem_validator_synthetic_fixture` | Verified affine matrix, NoData masking, and CRS extraction using temporary test fixtures. Real data validation pending tile acquisition. |
| **Terrain Slope Engine** | **Tested with Synthetic Data** | `ml/tests/test_spatial.py::test_dem_validator_computes_slope` | Horn's (1981) finite difference with geodesic scaling tested on synthetic gradients. Real data validation pending. |
| **Backend REST APIs** | **Implemented & Tested** | `backend/tests/test_spatial.py` (8 tests) | All 5 spatial endpoints verified; directory traversal & file extension security guards enforced. |
| **Frontend Spatial Panel** | **Mounted in Live UI & Verified** | Browser subagent validation at `http://localhost:5173` | Fully integrated into Geospatial Workspace with tab switcher, Sidebar navigation, and Study Region link. |
| **Authentic Physical DEM** | **Blocked by Unavailable Data** | Physical scan of `data/raw/spatial/dem/` | 0 tiles committed. Truthfully reports `UNAVAILABLE` status and zero fabricated data notice. |
