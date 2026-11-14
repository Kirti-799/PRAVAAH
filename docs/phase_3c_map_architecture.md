# PRAVAAH Phase 3C — Interactive GIS Map Architecture

## 1. Overview & Objectives

In Phase 3C, PRAVAAH integrated a real interactive GIS workstation map using **Leaflet** (`v1.9.4`) and **React-Leaflet** (`v5.0.0`), replacing static mockup canvases with dynamic geospatial cartography. The map centers on the **Upper-to-Middle Yamuna River Corridor**, extending from **Hathnikund Barrage** ($\sim 30.31^\circ\text{ N}, 77.58^\circ\text{ E}$) down to **Delhi Old Railway Bridge (ORB)** ($\sim 28.66^\circ\text{ N}, 77.25^\circ\text{ E}$) and **Okhla Barrage** ($\sim 28.53^\circ\text{ N}, 77.30^\circ\text{ E}$).

The map architecture is built on three core pillars:
1. **Cartographic Decoupling:** Basemap tile URLs and attributions are dynamically configurable rather than hardcoded to a single provider.
2. **Layer Integrity & Honest Availability:** Layers are categorized by domain and enforce a strict availability state machine (`AVAILABLE`, `UNAVAILABLE_IN_REPOSITORY`, `LOADING`). Synthetic geometries are prohibited from being displayed as real geographic information.
3. **Interactive Coordinate Intelligence:** Clicking on the map captures coordinates, allows pinpoint inspection, and dispatches requests directly to the meteorological integration workspace.

---

## 2. Basemap Catalog & Provider Abstraction

Tile provider settings are centralized in `backend/app/integrations/maps/map_config.py` and exposed via `GET /api/weather/basemap/config`.

| Basemap Option | Tile URL Template | Attribution | Max Zoom | Primary Use Case |
| :--- | :--- | :--- | :--- | :--- |
| **OpenStreetMap Standard** *(Default)* | `https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png` | &copy; OpenStreetMap contributors | 19 | Standard geographic reference and infrastructure identification. |
| **CartoDB Positron** | `https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png` | &copy; OpenStreetMap &copy; CARTO | 19 | High-contrast muted background optimized for flood depth overlays. |
| **OpenTopoMap** | `https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png` | &copy; OpenStreetMap, SRTM; OpenTopoMap | 17 | Topographical contour and hillshade visualization for catchment runoff. |

### Tile Usage Policy & Fair Use
- OpenStreetMap tiles are served under the [OSM Foundation Tile Usage Policy](https://operations.osmfoundation.org/policies/tiles/).
- Standard HTTP User-Agent headers and client caching are respected to minimize unnecessary tile queries.

---

## 3. Spatial Extent & Reference Geometry

The study corridor is governed by the authoritative spatial contract established in Phase 3A:
- **West:** $76.85^\circ\text{ E}$
- **East:** $77.60^\circ\text{ E}$
- **South:** $28.50^\circ\text{ N}$
- **North:** $30.40^\circ\text{ N}$
- **Default Viewport Center:** $[29.45^\circ\text{ N}, 77.22^\circ\text{ E}]$, Default Zoom: $8$

### Primary Corridor Hydrometric Stations
The map renders custom SVG div-icon pins for the primary hydrometeorological monitoring stations:
1. **Hathnikund Barrage (Upstream Inflow):** $30.31^\circ\text{ N}, 77.58^\circ\text{ E}$ (Chainage Km 0.0)
2. **Yamunanagar Station:** $30.13^\circ\text{ N}, 77.29^\circ\text{ E}$ (Chainage Km 35.0)
3. **Karnal Bridge Gauge:** $29.69^\circ\text{ N}, 77.08^\circ\text{ E}$ (Chainage Km 95.0)
4. **Panipat Embankment Station:** $29.39^\circ\text{ N}, 77.10^\circ\text{ E}$ (Chainage Km 140.0)
5. **Sonipat Monitoring Gauge:** $28.99^\circ\text{ N}, 77.12^\circ\text{ E}$ (Chainage Km 195.0)
6. **Delhi Old Railway Bridge (ORB - Core Target):** $28.66^\circ\text{ N}, 77.25^\circ\text{ E}$ (Chainage Km 240.0; Warning: 204.50m, Danger: 205.33m)
7. **Okhla Barrage (Downstream Outflow):** $28.53^\circ\text{ N}, 77.30^\circ\text{ E}$ (Chainage Km 265.0)

---

## 4. Layer Architecture & Availability Guardrails

The map component (`frontend/src/components/map/InteractiveGISMap.tsx`) features an independent layer drawer that prevents unacquired datasets from being represented as active map features:

```
+--------------------------------------------------------------------+
| PRAVAAH GIS WORKSTATION                                           |
+--------------------------------------------------------------------+
|  [Basemap: OSM v]   [Reset to Corridor Extent]   [Layers (3/14) v]  |
+---------------------------------+----------------------------------+
| Map Viewport                    | Layer Catalog Drawer             |
|                                 |                                  |
| [Study Corridor Box: AVAILABLE] | [x] Corridor Boundary [AVAILABLE]|
| [River Centerline:   AVAILABLE] | [x] Main Yamuna River [AVAILABLE]|
| [Corridor Stations:  AVAILABLE] | [x] Forecast Markers  [AVAILABLE]|
|                                 | [ ] Tributaries      [UNAVAIL]   |
|                                 | [ ] Canals (WJC/EJC) [UNAVAIL]   |
| [Click Marker -> Inspect]       | [ ] Embankments      [UNAVAIL]   |
|                                 | [ ] DEM Raster       [UNAVAIL]   |
| (Scale: 10km | CRS: EPSG:4326)  | [ ] Terrain Slope    [UNAVAIL]   |
+---------------------------------+----------------------------------+
```

### Layer Status State Machine
1. **`AVAILABLE`:** Valid vector or raster features present in the active spatial database or reachable via live integration (e.g. Study Corridor, River Centerline, Corridor Weather Stations).
2. **`UNAVAILABLE_IN_REPOSITORY`:** Documented catalog layer whose raw source file has not yet been staged or ingested (e.g. Tributaries, Canals, Embankments, DEM). The checkbox is disabled, displaying an explicit amber badge.
3. **`LOADING`:** Layer data currently being fetched asynchronously.

---

## 5. Map Interaction Workflows

1. **Pan & Zoom:** Standard mouse wheel and pinch-to-zoom between zoom level 6 (regional basin context) and 18 (embankment-level detail).
2. **Reset-to-Corridor Button:** Uses Leaflet `fitBounds` with padding to instantly re-center on Hathnikund-to-Delhi bounds.
3. **Feature Click Popups:** Clicking any station marker displays its station type, coordinates, chainage, flood danger levels (where applicable), and a button: `"Query Weather & Forecast"`.
4. **Interactive Click Inspection:** Clicking any arbitrary coordinate in the study corridor drops a point pin, displays decimal coordinates, and enables single-click weather analysis.
