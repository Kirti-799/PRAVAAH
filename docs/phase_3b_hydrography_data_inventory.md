# Phase 3B: River Hydrography Data Inventory & Provenance Register

**Project:** PRAVAAH (Predictive Risk Assessment and Vulnerability Analysis for Adaptive Assistance & Humanitarian Response)  
**Milestone:** Phase 3B — River Hydrography & Network Integration  
**Audit Date:** October 2026  
**Status:** Ingestion & Validation Framework Active | Network Topology Implemented | Repository Files Unacquired  

---

## 1. Executive Summary

Phase 3B establishes the hydrographic data infrastructure, vector processing pipeline, NetworkX topology graph analysis, and river station chainage engine for the Upper-to-Middle Yamuna River Corridor.

In strict adherence to the PRAVAAH Scientific Integrity Protocol:
- All candidate hydrographic datasets are formally cataloged with source agency, portal URL, licensing terms, coordinate systems, and acquisition blockers.
- An explicit distinction is maintained between **Available Datasets** and **Unacquired Datasets** (`UNAVAILABLE_IN_REPOSITORY`).
- Under no circumstances are synthetic polylines or fabricated river centerlines substituted for unacquired public datasets.
- Online automated extraction attempts from public Overpass API mirrors were executed and audited. Because public Overpass servers returned HTTP 406 / connection timeouts / SSL certificate errors in the automated execution environment, the acquisition blockers are formally registered below.

---

## 2. Comprehensive Hydrographic Dataset Inventory

| Dataset ID | Official Title | Source Agency & Portal | Nominal Resolution | Native CRS | File Format | Status in Repository | Storage Path | Acquisition Blockers & Access Notes |
| :--- | :--- | :--- | :---: | :--- | :---: | :---: | :--- | :--- |
| `OSM_YAMUNA_WATERWAYS` | OpenStreetMap Northern India Waterway Network | OpenStreetMap Contributors / Geofabrik ([Geofabrik Extracts](https://download.geofabrik.de/asia/india.html)) | 1:10,000 to 1:50,000 vector detail | EPSG:4326 (WGS 84) | GeoJSON / PBF | **UNAVAILABLE_IN_REPOSITORY** | `data/raw/spatial/hydrography/osm_yamuna_waterways.geojson` | Automated Overpass API mirrors timed out or returned HTTP 406; requires downloading India/Northern Zone PBF and spatially clipping to corridor bounds [76.85°E–77.60°E, 28.50°N–30.40°N]. |
| `CWC_YAMUNA_REACHES` | Central Water Commission National River Reach Network | Ministry of Jal Shakti / CWC ([India-WRIS](https://indiawris.gov.in/)) | Authoritative reach lines | EPSG:4326 (WGS 84) | Shapefile / GeoPackage | **UNAVAILABLE_IN_REPOSITORY** | `data/raw/spatial/hydrography/cwc_yamuna_reaches.gpkg` | India-WRIS downloads require user credentials and departmental data-sharing agreements; spatial reach GIS layer uncommitted. |
| `SOI_HYDRO_150K` | Survey of India Open Series Maps (Hydrographic Layer) | Survey of India (SOI) ([Online Maps Portal](https://onlinemaps.surveyofindia.gov.in/)) | 1:50,000 scale | EPSG:4326 / Lambert Conformal Conic | GeoPDF / Shapefile | **UNAVAILABLE_IN_REPOSITORY** | `data/raw/spatial/hydrography/soi_yamuna_hydro.shp` | Available predominantly as DRM-locked raster GeoPDFs requiring non-commercial Aadhaar e-verification; vector hydrography is restricted across national defense boundaries. |
| `DELHI_IFC_EMBANKMENTS` | Delhi Irrigation & Flood Control Bunds & Embankments | Delhi I&FC Department / GNCTD ([Delhi I&FC](https://ifc.delhi.gov.in/)) | CAD / GIS alignment | Local Grid / EPSG:4326 | GeoJSON | **UNAVAILABLE_IN_REPOSITORY** | `data/raw/spatial/hydrography/delhi_ifc_bunds.geojson` | Embankment alignments published in static flood management manuals; vector GIS layers with certified crest elevations are held across inter-state committees (UP-Haryana-Delhi). |

---

## 3. Physical Directory Audit

A recursive scan of the local filesystem confirmed:
- `data/raw/spatial/hydrography/`: Directory exists; contains `.gitkeep`. **0 raw vector datasets present.**
- `data/processed/spatial/hydrography/`: Directory exists; contains `.gitkeep`. **0 processed vector datasets present.**

### Operational Policy Enforcement:
When `GET /api/spatial/hydrography/status` or `GET /api/spatial/hydrography/layers` is queried:
1. The backend scans both `data/processed/spatial/hydrography/` and `data/raw/spatial/hydrography/`.
2. Truthfully returns `"hydrography_availability": "UNAVAILABLE"`.
3. Returns complete acquisition instructions and target bounding coordinates without generating synthetic placeholders.

---

## 4. Live Acquisition Investigation & Blocker Audit

During Phase 3B implementation, automated online acquisition scripts were executed against multiple public OpenStreetMap Overpass API instances:
1. `https://overpass-api.de/api/interpreter`: Returned `HTTP 406 Not Acceptable` / `read operation timed out` on automated API queries.
2. `https://overpass.kumi.systems/api/interpreter`: Timed out due to community server rate limiting.
3. `https://maps.mail.ru/osm/tools/overpass/api/interpreter`: Failed SSL certificate chain verification (`[SSL: CERTIFICATE_VERIFY_FAILED]`).

### Blocker Conclusion:
Public online Overpass instances are rate-constrained and cannot be relied upon for automated non-interactive retrieval in this execution environment. Manual ingestion of the Geofabrik Northern India `.osm.pbf` or bulk vector GeoJSON directly into `data/raw/spatial/hydrography/osm_yamuna_waterways.geojson` is required for production operations.

---

## 5. Licensing and Provenance Standards

All future acquired hydrographic vector data must adhere to open access licenses:
* **OpenStreetMap Data:** Open Database License (ODbL 1.0). Attribution required: *"© OpenStreetMap contributors"*.
* **India-WRIS / CWC Data:** Government of India Open Data License (GODL-India).
* **Survey of India:** National Map Policy 2005 / SOI Open Series License.
