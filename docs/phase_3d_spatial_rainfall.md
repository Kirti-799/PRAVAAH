# Phase 3D.4 — Spatial Rainfall Data Ingestion & Provider Assessment

**Project**: PRAVAAH (Predictive Risk Assessment and Vulnerability Analysis for Adaptive Assistance & Humanitarian Response)  
**Scope**: Catchment-Scale Precipitation Intelligence for Hathnikund Upstream Basin  
**Status**: MULTI-PROVIDER AUDIT & ADAPTER ARCHITECTURE COMPLETE

---

## 1. Context: Moving Beyond Point Weather to Catchment Intelligence

In Phase 3C, weather was queried at individual stations along the downstream 220 km corridor (e.g., Delhi, Panipat, Karnal). However, flood discharge at Hathnikund is driven entirely by precipitation occurring across the 11,112 km² upstream mountainous catchment.

Phase 3D establishes spatially distributed rainfall ingestion covering the basin across multiple elevations, from the Shivalik foothills (300 m) to glaciated headwaters (5,800 m).

---

## 2. Multi-Provider Investigation & Audit Matrix

In accordance with Phase 3D guardrails, three primary meteorological data providers were audited and modeled:

| Audit Parameter | Open-Meteo Catchment Ensemble | IMD 0.25° Gridded Rainfall | NASA GPM IMERG Early Run |
| :--- | :--- | :--- | :--- |
| **Provider** | Open-Meteo (ECMWF IFS / DWD ICON blend) | India Meteorological Department (IMD) | NASA GES DISC / GSFC |
| **Product Name** | Catchment NWP Forecast & Current Rate | 0.25° Daily Gridded Rainfall (`.GRD`) | GPM_3IMERGHHE (Early Run) |
| **Data Nature** | **Numerical Weather Prediction (NWP) Forecast** | **Ground Gauge Interpolated Observation** | **Merged Satellite / Microwave Observation** |
| **Native Spatial Res.** | 0.1° (~10 km) downscaled to terrain | 0.25° (~27.5 km × 27.5 km) | 0.1° (~10 km × 10 km) |
| **Temporal Res.** | Hourly, 7-day lead time | Daily (accumulated 08:30 to 08:30 IST) | 30 minutes |
| **Measurement Units** | mm (depth), mm/h (rate) | mm/day | mm/hr |
| **Publication Latency**| ~1 to 2 hours model run delay | **T+24h to T+48h operational QC delay** | **~4 hours satellite processing delay** |
| **Licensing** | CC-BY 4.0 Open Access | Open Data / Research Use Only | NASA Open Science Data Policy |
| **Access Method** | HTTP REST multi-coordinate API | Binary float32 raster (`.GRD`) file download | OPeNDAP / HTTPS HDF5 subsetting |
| **Integration Status** | **OPERATIONAL & LIVE** | **OFFLINE ARCHIVE ONLY (Documented)** | **AUTH TOKEN REQUIRED (Documented)** |
| **Access Blocker** | None; free open access | No public unauthenticated live REST API | Requires NASA Earthdata URS bearer token |

---

## 3. Representative Elevational Sampling Grid (20 Nodes)

To capture topographic precipitation gradients (orographic enhancement on windward slopes vs. rain shadow in high valleys), PRAVAAH established a 20-node sampling grid:

| Node ID | Location Name | Sub-Basin | Latitude | Longitude | Elevation (m) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `GRID_01` | Hathnikund Outlet / Plains Exit | Lower Yamuna | 30.32°N | 77.58°E | 295 m |
| `GRID_02` | Paonta Sahib / Bata Confluence | Lower Yamuna | 30.45°N | 77.62°E | 390 m |
| `GRID_03` | Dakpathar Barrage / Lower Yamuna-Tons | Yamuna-Tons | 30.50°N | 77.78°E | 460 m |
| `GRID_04` | Kalsi / Asan River Junction | Yamuna-Tons | 30.53°N | 77.85°E | 550 m |
| `GRID_05` | Renuka Lake / Giri Valley | Lower Giri | 30.60°N | 77.45°E | 670 m |
| `GRID_06` | Rajgarh / Mid-Giri Basin | Middle Giri | 30.85°N | 77.30°E | 1,550 m |
| `GRID_07` | Chail-Kufri Ridge / Giri Headwaters | Upper Giri | 31.05°N | 77.25°E | 2,250 m |
| `GRID_08` | Theog / Sutlej-Yamuna Divide | Giri Ridge | 31.12°N | 77.35°E | 2,300 m |
| `GRID_09` | Tiuni / Pabbar-Tons Confluence | Middle Tons | 30.95°N | 77.85°E | 1,050 m |
| `GRID_10` | Rohru / Mid-Pabbar Basin | Pabbar | 31.20°N | 77.75°E | 1,525 m |
| `GRID_11` | Chanshal Pass / High Pabbar Range | Upper Pabbar | 31.35°N | 77.70°E | 3,750 m |
| `GRID_12` | Naugaon / Mid-Yamuna Stem | Upper Yamuna | 30.78°N | 78.15°E | 1,200 m |
| `GRID_13` | Barkot / Yamuna Foothill Valley | Upper Yamuna | 30.82°N | 78.22°E | 1,220 m |
| `GRID_14` | Netwar / Tons Supin-Rupin Junction | Upper Tons | 31.05°N | 78.10°E | 1,400 m |
| `GRID_15` | Sankri / Govind Sanctuary (Supin) | Upper Tons | 31.08°N | 78.18°E | 1,950 m |
| `GRID_16` | Har-Ki-Dun Valley / High Glacial Tons | Glacial Tons | 31.15°N | 78.42°E | 3,550 m |
| `GRID_17` | Yamunotri Temple / Yamuna Source | Glacial Yamuna | 31.01°N | 78.46°E | 3,290 m |
| `GRID_18` | Bandarpunch Massif / Glacial Ridge | High Divide | 31.10°N | 78.55°E | 5,800 m |
| `GRID_19` | Mussoorie Ridge / Southern Catchment | Shivalik Ridge | 30.46°N | 78.07°E | 2,005 m |
| `GRID_20` | Dehradun Northern Divide (Asan) | Asan Basin | 30.38°N | 77.98°E | 640 m |

---

## 4. Software Architecture: Provider Adapter Pattern

```
backend/app/integrations/rainfall/
├── __init__.py
├── base.py           # BaseSpatialRainfallAdapter, ProviderProvenanceMetadata
├── open_meteo.py     # OpenMeteoCatchmentRainfallAdapter (Live Multi-Point API)
├── imd.py            # IMDRainfallAdapter (0.25° Offline .GRD contract)
└── nasa_gpm.py       # NASAGPMAdapter (IMERG Early Run & Earthdata token contract)
```

This decoupled architecture guarantees that if offline IMD gridded files are placed into `data/raw/spatial/rainfall/imd/`, or if a NASA Earthdata token is configured in `.env`, the respective adapters can be enabled without modifying downstream service logic.

