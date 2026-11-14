# PRAVAAH Phase 3C — Provider Readiness & Integration Register

## 1. Provider Readiness Classification Register

This register documents the operational status of all external meteorological, hydrological, and geospatial data providers evaluated for the PRAVAAH platform.

| Provider / Agency | Domain | Current Status | Integration Class | Access Mechanism | Temporal / Spatial Resolution | Limitations & Next Steps |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Open-Meteo** | Weather & Forecasting | **IMPLEMENTED** | `OpenMeteoAdapter` | Open HTTP REST JSON | Hourly / $0.1^\circ$ ($\sim 10\text{ km}$) | Active in Phase 3C. Free tier fair use (10k calls/day). Live queries verified. |
| **OpenStreetMap Standard** | GIS Basemap Cartography | **IMPLEMENTED** | `BasemapOption` | Standard Tile Server | Continuous Slippy Tiles ($z=4-19$) | Active in Phase 3C via Leaflet / React-Leaflet. Muted OSM cartography. |
| **CartoDB Positron** | GIS Basemap Cartography | **IMPLEMENTED** | `BasemapOption` | CARTO Tile CDN | Continuous Slippy Tiles ($z=4-19$) | Configured in Phase 3C basemap catalog. High-contrast light cartography. |
| **OpenTopoMap** | Topographic Basemap | **IMPLEMENTED** | `BasemapOption` | OpenTopoMap Tile CDN | Continuous Slippy Tiles ($z=4-17$) | Configured in Phase 3C basemap catalog. Topographical contours & hillshading. |
| **India Meteorological Department (IMD)** | Ground Weather Observations & Warnings | **PREPARED FOR FUTURE INTEGRATION** | `IMDWeatherAdapter` | Restricted / Academic Portal | Daily Ground Gauges / $0.25^\circ$ Gridded binary (`.grd`) | No public open REST API without institutional MoU or CAP warning scrapers. Prepared contract in Phase 3C. |
| **Central Water Commission (CWC) / India-WRIS** | River Gauge Water Levels & Discharge | **PREPARED FOR FUTURE INTEGRATION** | `CWCHydrologyAdapter` | India-WRIS Portal / Flood Bulletins | Hourly to Daily at Gauges (Delhi ORB, Hathnikund, Okhla) | No unauthenticated open REST API. Requires automated PDF/HTML bulletin ingestion or India-WRIS telemetry API keys. Contract prepared in Phase 3C. |
| **NASA GPM (IMERG)** | Satellite Precipitation | **PREPARED FOR FUTURE INTEGRATION** | `NASAGPMAdapter` | NASA Earthdata OPeNDAP / HTTPS | 30-minute / $0.1^\circ$ global raster grid | Requires Earthdata OAuth2 authentication, HDF5/NetCDF chunking, and raster aggregation over the Yamuna catchment. Interface prepared in Phase 3C. |
| **CartoDEM (ISRO / Bhuvan)** | High-Resolution Terrain Elevation | **PARTIALLY IMPLEMENTED** | Spatial File Ingestion | ISRO Bhuvan Download Portal | $10\text{ m} - 30\text{ m}$ GeoTIFF | Ingestion & slope processing engines implemented in Phase 3A (`ml/spatial/dem.py`), awaiting local GeoTIFF download into `data/raw/spatial/dem/`. |
| **Copernicus GLO-30 DEM** | Global Digital Elevation Model | **PARTIALLY IMPLEMENTED** | Spatial File Ingestion | OpenTopography / AWS Open Data | $30\text{ m}$ GeoTIFF | Validation pipeline in Phase 3A ready to ingest. |
| **OSM Overpass Hydrography** | Waterway Vector Geometries | **PARTIALLY IMPLEMENTED** | `ml/spatial/river.py` | Overpass QL API | Vector LineString / MultiLineString | Overpass public mirrors subject to regional HTTP 406 / timeouts. Ingestion pipeline ready; fallback to local staged shapefiles. |
| **Delhi Jal Board (DJB) Drainage** | Urban Stormwater Outfalls | **NOT AVAILABLE** | Future Milestone | Municipal Records | City-scale drain vector network | Data not in public domain. Awaiting Phase 3D/4 data acquisition. |
| **NDMA / SDMA Shelters** | Evacuation Infrastructure | **NOT AVAILABLE** | Future Milestone | State Disaster Management Portals | Point infrastructure | Awaiting Phase 4 humanitarian response milestone. |

---

## 2. Technical Requirements for Future Integrations

### A. Central Water Commission (CWC) & India-WRIS
- **Objective:** Stream near-real-time water levels (Delhi ORB gauge, current gauge reading vs. Warning Level 204.50m, Danger Level 205.33m) and Hathnikund discharge outflow.
- **Prerequisites:**
  1. Register for India-WRIS API developer credentials or create an automated daily flood bulletin parser (`backend/app/integrations/hydrology/cwc_bulletin_parser.py`).
  2. Implement station mapping table matching CWC station codes to PRAVAAH chainage stations.
  3. Strict non-fabrication invariant: when gauge levels are offline or delayed, display `UNAVAILABLE_FROM_AGENCY` rather than interpolating synthetic river stages.

### B. India Meteorological Department (IMD)
- **Objective:** Ingest official daily ground truth rainfall and color-coded severe weather warnings (Yellow/Orange/Red) for Haryana, UP, and Delhi NCT districts.
- **Prerequisites:**
  1. Access IMD Mausam API or parse Common Alerting Protocol (CAP) RSS feeds.
  2. Convert district alerts into GeoJSON polygon overlays.
  3. Validate rainfall measurements against physical limits ($0\text{ to }500\text{ mm/day}$).

### C. NASA GPM IMERG
- **Objective:** Spatially aggregated basin rainfall estimation over the Himalayan and Shivalik catchment draining into Hathnikund.
- **Prerequisites:**
  1. Set environment variables `EARTHDATA_USERNAME` and `EARTHDATA_PASSWORD`.
  2. Integrate `xarray` and `rasterio` in the ML spatial pipeline to clip GPM IMERG NetCDF4 rasters against the Yamuna basin boundary polygon.
  3. Aggregate half-hourly gridded precipitation into hourly mean catchment precipitation (mm) for input into hydrologic runoff models.

---

## 3. Data Integrity & Provenance Guardrails

1. **Explicit Provenance Metadata:** Every external dataset stored in cache or passed to frontend/ML components retains `source_reference`, `retrieved_at`, and `quality_status`.
2. **Missing Value Invariant:** Missing observations remain `None` / `null`. Under no circumstances are missing gauge levels or rainfall totals filled with artificial or synthetic values.
3. **No Direct Coupling to Operational Early-Warning Claims:** PRAVAAH maintains clear scientific disclaimers that it provides decision-support and geospatial intelligence, not official statutory flood warnings (which remain the exclusive jurisdiction of the Central Water Commission and Indian Meteorological Department).
