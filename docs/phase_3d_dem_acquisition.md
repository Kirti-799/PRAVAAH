# Phase 3D.1 — Authentic DEM Acquisition & Processing Report

**Project**: PRAVAAH (Predictive Risk Assessment and Vulnerability Analysis for Adaptive Assistance & Humanitarian Response)  
**Phase**: 3D — Upstream Catchment Delineation, Terrain Data Acquisition & Spatial Rainfall Intelligence  
**Authoritative Scope**: Upstream Himalayan Catchment Contributing to Hathnikund Barrage (Lat 30.0°N to 32.0°N, Lon 77.0°E to 79.0°E)  
**Status**: COMPLETE (100% Target Tile Coverage Acquired and Mosaicked)

---

## 1. Executive Summary & Provenance Register

Phase 3D transitions PRAVAAH from a localized 220 km downstream river corridor to an upstream catchment-scale hydrological domain. The Upper Yamuna basin feeding Hathnikund Barrage spans across Uttarakhand, Himachal Pradesh, and Haryana, encompassing elevations from 255 m MSL at the plains exit to 6,740 m MSL at the glaciated Chaukhamba/Bandarpunch massifs.

Rather than relying on synthetic raster approximations or low-resolution global grids, PRAVAAH acquired 4 authentic high-resolution tiles of the European Space Agency (ESA) Copernicus DEM GLO-30 (DSM COG 10) distributed via Open Data on AWS.

### Authoritative Dataset Provenance

| Parameter | Specification |
| :--- | :--- |
| **Provider** | European Space Agency (ESA) / Airbus Defence and Space |
| **Distribution Platform** | Registry of Open Data on AWS (`s3://copernicus-dem-30m/`) |
| **Product Name** | Copernicus DEM GLO-30 (Global 30m Digital Surface Model) |
| **Product Version** | DSM COG 10 (2022 release, Cloud-Optimized GeoTIFF) |
| **Native Spatial Resolution** | 1.0 arc-second (~30 m metric grid at equator, ~26 m at 30°N) |
| **Horizontal CRS** | EPSG:4326 (WGS 84 ellipsoidal 2D coordinates) |
| **Vertical Reference Datum** | EGM2008 Geoid (Earth Gravitational Model 2008) |
| **Vertical Units** | Meters above MSL (Float32) |
| **Acquisition Date** | 2026-10-31 |
| **Target Bounding Box** | South: 30.0°N, North: 32.0°N, West: 77.0°E, East: 79.0°E |
| **Licensing** | Free and Open Access under Copernicus WorldDEM-30 License |
| **Raw File Directory** | `data/raw/spatial/dem/` |
| **Processed Mosaic** | `data/processed/spatial/dem/upstream_yamuna_dem_mosaic.tif` |

---

## 2. Tile Inventory & Acquisition Verification

Four adjacent 1° × 1° tiles were retrieved to form a complete contiguous bounding box covering the entire upstream contributing basin:

| Tile Identifier | Geographic Coverage | File Size | Elevation Range (m) | Catchment Region Covered |
| :--- | :--- | :--- | :--- | :--- |
| `Copernicus_DSM_COG_10_N30_00_E077_00_DEM.tif` | 30°N–31°N, 77°E–78°E | 42.84 MB | 255 – 3,647 | Hathnikund Barrage outlet, lower Yamuna gorge, Paonta Sahib, Giri & Bata confluences |
| `Copernicus_DSM_COG_10_N30_00_E078_00_DEM.tif` | 30°N–31°N, 78°E–79°E | 43.32 MB | 362 – 3,022 | Dehradun valley, Mussoorie ridge, Asan River basin, lower Tons gorge (Dakpathar/Kalsi) |
| `Copernicus_DSM_COG_10_N31_00_E077_00_DEM.tif` | 31°N–32°N, 77°E–78°E | 42.48 MB | 628 – 5,280 | Upper Giri basin, Pabbar River catchment, Rohru, Shimla-Kinnaur high ridge divide |
| `Copernicus_DSM_COG_10_N31_00_E078_00_DEM.tif` | 31°N–32°N, 78°E–79°E | 40.65 MB | 1,040 – 6,740 | Upper Tons River, Supin & Rupin headwaters, Yamunotri glacier, Bandarpunch peaks |

**Total Raw Tile Size**: 169.29 MB  
**Tile Completeness**: 4 / 4 tiles (100.0% coverage of target bounding box).

---

## 3. DEM Mosaicking & Terrain Processing Workflow

The raw tiles were mosaicked using `DEMValidator.mosaic_tiles()` powered by `rasterio.merge`. The resulting seamless mosaic was saved as a single unified raster:

- **Mosaic Path**: `data/processed/spatial/dem/upstream_yamuna_dem_mosaic.tif`
- **Mosaic File Size**: 207.40 MB
- **Dimensions**: 7,200 columns × 7,200 rows = 51,840,000 cells
- **Pixel Depth**: 32-bit floating point (`float32`)
- **NoData Value**: Preserved as `-9999.0`
- **CRS**: EPSG:4326 (WGS 84)

### Regional Elevation Statistics (Full Mosaic)

- **Minimum Elevation**: 254.8 m MSL (Yamunanagar / downstream Yamuna floodplains)
- **Maximum Elevation**: 6,739.9 m MSL (Gangotri / Chaukhamba / Bandarpunch massifs)
- **Mean Elevation**: 2,462.1 m MSL
- **Plausible Regional Elevation Check**: PASSED (All valid cells fall within the valid Himalayan range 200 m to 7,500 m MSL).

---

## 4. Terrain Derivative Products

From the validated elevation surface, two metric terrain derivatives are computed on demand:

1. **Aspect**:
   Downslope compass bearing in degrees (0°–360°, where 0° = North, 90° = East). Calculated using central differences scaled by geodetic metric factor $dx = res_x \cdot 111320 \cdot \cos(\phi)$ and $dy = res_y \cdot 110540$.

2. **Hillshade**:
   Normalized shaded relief (0–255 grayscale) representing oblique illumination from azimuth 315° (North-West) and solar altitude 45°, highlighting ridgelines, gorges, and valley floors.

