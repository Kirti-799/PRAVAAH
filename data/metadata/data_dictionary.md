# PRAVAAH — Hydrometeorological & Geospatial Data Dictionary

> **Milestone:** Phase 1A — Data Feasibility and Study Region Selection  
> **Schema Version:** 1.0.0  
> **Target Region:** Yamuna River Floodplain (Hathnikund to Delhi ORB Reach)  
> **Status:** Baseline Specification  

---

## 1. Overview and Standards

This data dictionary defines all primary variables and derived features required for the PRAVAAH Phase 1 flood-risk predictive modeling pipeline. 

### Data Integrity Rules:
- **No Fabricated Labels:** All hydrological and event labels are tied to authoritative measuring instruments (e.g., CWC staff gauges, acoustic Doppler current profilers).
- **Explicit Units:** All numeric values must retain physical SI or designated hydrological units (e.g., metres above Mean Sea Level, millimeters, cubic meters per second).
- **Coordinate Reference Systems:** All spatial features must record their native CRS and be reprojected to EPSG:4326 (WGS 84 geographic 2D) or EPSG:32643 (UTM Zone 43N projected planar) prior to spatial analysis.

---

## 2. Core Hydrometeorological & Geospatial Variables

### Variable 1: `rainfall_daily`
* **Definition:** Daily accumulated precipitation over a geographical grid cell or catchment area.
* **Unit:** Millimeters ($\text{mm}$).
* **Data Type:** Float (64-bit).
* **Source:** India Meteorological Department (IMD) 0.25° × 0.25° Daily Gridded Rainfall Dataset (Pai et al., 2014).
* **Temporal Meaning:** Total rainfall accumulated over the 24-hour window ending at 08:30 IST on the observation date.
* **Spatial Meaning:** Areal average over a 0.25° latitude by 0.25° longitude cell (~27.5 km × 27.5 km).
* **Missing-Value Representation:** `-999.0` (in native binary/NetCDF) or `NaN` (in processed tabular representations).
* **Known Limitations:** Spatial smoothing in mountainous upper catchments (Himachal Pradesh and Uttarakhand); convective cloudbursts under 10 km spatial scale may be attenuated.

---

### Variable 2A: `hathnikund_inflow` (`HKB U/S`)
* **Definition:** Total unregulated water volume per second entering the Hathnikund Barrage pond from the upper catchment (Yamuna, Tons, Giri, and Asan rivers).
* **Unit:** Cumecs ($\text{m}^3/\text{s}$). ($1 \text{ cusec} \approx 0.0283168 \text{ m}^3/\text{s}$).
* **Data Type:** Float (64-bit).
* **Source:** Haryana Irrigation and Water Resources Department / NWDP.
* **Temporal Meaning:** Daily reading (06:00 or 08:00 IST) representing peak or morning flow.
* **Spatial Meaning:** Point observation at Hathnikund Barrage Upstream ($30.3150^\circ\text{N}, 77.5828^\circ\text{E}$).
* **Missing-Value Representation:** `null` or `NaN` (7 missing days across 2018–2025, all in dry season).
* **Physical Significance:** Direct hydrological runoff response to upper-catchment antecedent rainfall.

---

### Variable 2B: `hathnikund_release` (`HKB D/S`)
* **Definition:** Net water discharge released from Hathnikund Barrage spillway directly into the active Yamuna river channel heading toward Delhi, after upstream diversions into the Western Yamuna Canal (WYC) and Eastern Yamuna Canal (EYC).
* **Unit:** Cumecs ($\text{m}^3/\text{s}$). ($1 \text{ cusec} \approx 0.0283168 \text{ m}^3/\text{s}$).
* **Data Type:** Float (64-bit).
* **Source:** Haryana Irrigation and Water Resources Department / NWDP.
* **Temporal Meaning:** Daily reading (06:00 or 08:00 IST).
* **Spatial Meaning:** Point release into downstream Yamuna River ($30.3150^\circ\text{N}, 77.5828^\circ\text{E}$).
* **Missing-Value Representation:** `null` or `NaN` (0 missing days across 2018–2025; 100% complete).
* **Physical Significance:** Primary hydrodynamic boundary input for downstream flood wave propagation to Delhi Old Railway Bridge (~48h travel time). During baseflow, release is $\sim 10\text{ m}^3/\text{s}$ while inflow is $\sim 125\text{ m}^3/\text{s}$ due to canal diversion. During high flood surges ($\ge 2,000\text{ m}^3/\text{s}$), canal gates are shut and release equals inflow.


---

### Variable 3: `river_stage_orb`
* **Definition:** Observed surface water elevation of the Yamuna River measured at the Old Railway Bridge (ORB) staff gauge in Delhi.
* **Unit:** Metres above Mean Sea Level ($\text{m MSL}$).
* **Data Type:** Float (64-bit).
* **Source:** Central Water Commission (CWC) Gauge-Discharge Site (Site Code: 028-MDD).
* **Temporal Meaning:** Hourly or daily (08:00 IST) recorded water level.
* **Spatial Meaning:** Point observation at Old Railway Bridge, Delhi (Coordinates: 28.6625°N, 77.2483°E).
* **Missing-Value Representation:** `null` or `NaN`.
* **Known Limitations:** Riverbed silting and sedimentation over decades has altered the stage-discharge relationship (a stage of 205.33m today corresponds to a different discharge volume than in 1978).

---

### Variable 4: `flood_stage_class` (Ground-Truth Target Label)
* **Definition:** Categorical hazard level at the reference monitoring station based on official CWC operational flood benchmarks.
* **Unit:** Dimensionless (Categorical / Ordinal).
* **Data Type:** Integer / Categorical:
  - `0`: Normal Flow ($< 204.50\text{ m}$)
  - `1`: Warning Stage ($\ge 204.50\text{ m}$ and $< 205.33\text{ m}$)
  - `2`: Danger Stage ($\ge 205.33\text{ m}$ and $< 206.00\text{ m}$)
  - `3`: Extreme Flood / Evacuation Stage ($\ge 206.00\text{ m}$)
* **Source:** CWC Flood Forecasting Network / Delhi Disaster Management Authority (DDMA).
* **Temporal Meaning:** Maximum flood stage class observed over a forward-looking prediction horizon window ($t + 24\text{h}$ to $t + 48\text{h}$).
* **Spatial Meaning:** Reference reach of the Yamuna Floodplain in Delhi NCT (Wazirabad to Okhla Barrage).
* **Missing-Value Representation:** Excluded from training/evaluation if underlying gauge level is unrecorded.
* **Known Limitations:** Represents river channel overbank threshold; does not directly capture internal urban pluvial waterlogging caused by blocked stormwater drains unless river backflow occurs.

---

### Variable 5: `antecedent_precipitation_index_3d` (Derived Feature)
* **Definition:** Exponentially weighted or cumulative sum of basin precipitation over the preceding 3 calendar days: $\text{API}_{3d} = \sum_{k=1}^{3} w_k \cdot P_{t-k}$.
* **Unit:** Millimeters ($\text{mm}$).
* **Data Type:** Float (64-bit).
* **Source:** Derived from IMD gridded daily rainfall aggregated across the upper-middle Yamuna catchment.
* **Temporal Meaning:** Catchment wetness proxy at prediction time $t$, utilizing strictly historical observations ($t-1, t-2, t-3$).
* **Spatial Meaning:** Spatially weighted catchment average over the contributing sub-basin polygon.
* **Missing-Value Representation:** `NaN` if any input day in the lookback window is missing.
* **Known Limitations:** Assumes uniform soil infiltration characteristics across different soil types in the basin.

---

### Variable 6: `terrain_elevation`
* **Definition:** Surface elevation above the vertical reference geoid.
* **Unit:** Metres ($\text{m}$).
* **Data Type:** Float (32-bit raster).
* **Source:** Copernicus GLO-30 DEM (Airbus/ESA) or NASA SRTMGL1 (1 arc-second).
* **Temporal Meaning:** Static topographical reference (Epoch 2011–2015).
* **Spatial Meaning:** Continuous raster surface sampled at 30 m spatial resolution.
* **Missing-Value Representation:** `-9999.0` or `NoData`.
* **Known Limitations:** Static surface; does not reflect micro-embankments, flyover piers, or local flood wall structures constructed after the satellite radar flight acquisition epoch.

---

### Variable 7: `relative_elevation_to_channel` (Height Above Nearest Drainage — HAND)
* **Definition:** Vertical elevation difference between a terrain grid cell and the nearest point on the hydrologically connected river flow path.
* **Unit:** Metres ($\text{m}$).
* **Data Type:** Float (32-bit raster).
* **Source:** Derived from hydrologically conditioned DEM using flow direction and drainage accumulation rasters.
* **Temporal Meaning:** Static morphological flood vulnerability feature.
* **Spatial Meaning:** 30 m grid cell throughout the study region buffer.
* **Missing-Value Representation:** `NaN` or `NoData`.
* **Known Limitations:** Sensitivity to DEM depression filling algorithms in flat urban plains.

---

### Variable 8: `distance_to_active_channel`
* **Definition:** Euclidean horizontal distance from each spatial unit to the center line or active channel boundary of the Yamuna River.
* **Unit:** Metres ($\text{m}$).
* **Data Type:** Float (64-bit).
* **Source:** Computed from OpenStreetMap river coastline / waterway vectors or hydro-conditioned flow lines.
* **Temporal Meaning:** Static geometric feature.
* **Spatial Meaning:** Planar distance in EPSG:32643 coordinate space.
* **Missing-Value Representation:** Not applicable (computable for all valid points in domain).
* **Known Limitations:** High-flow braiding or seasonal channel migration may shift the active water line by several dozen metres.

---

## 3. Phase 1D Assembled Modelling Dataset Variables

Variables produced by `ml/data_processing/extract_gridded_rainfall.py` and `ml/data_processing/assemble_dataset.py`:

### `rainfall_spatial_mean_mm`
* **Definition:** Arithmetic mean of daily accumulated rainfall across all valid reporting grid cells within the provisional Upper Yamuna bounding box ($28.0^\circ\text{N}-31.0^\circ\text{N}, 76.5^\circ\text{E}-78.0^\circ\text{E}$).
* **Unit:** Millimeters per day ($\text{mm/day}$).
* **Temporal Semantics:** 24h accumulation ending at 08:30 IST (03:00 UTC) on the indicated date.
* **Spatial Caveat:** Calculated over a provisional rectangular bounding box (91 cells); does not represent a DEM-delineated hypsometric watershed boundary.
* **Missing Value:** `None` (null) if all cells in the bounding box report missing values.

### `is_target_observed`
* **Definition:** Boolean indicator denoting whether at least one verified downstream stage observation was recorded during the forward target prediction window $[t+24\text{h}, t+48\text{h}]$.
* **Values:** `True` (target window observed) or `False` (target window unobserved).
* **Integrity Invariant:** If `is_target_observed == False`, `target_danger_breach` and `target_max_stage_m` MUST be `None` (null). They are never imputed as negative (0).

### `target_danger_breach`
* **Definition:** Binary classification target label indicating whether the maximum downstream stage in the forward prediction window $[t+24\text{h}, t+48\text{h}]$ reached or exceeded the official CWC Danger Mark ($205.33\text{ m MSL}$).
* **Values:**
  - `1`: Positive breach event ($\max_{\tau \in [t+24, t+48]} \text{Stage}(\tau) \ge 205.33\text{ m MSL}$).
  - `0`: Negative non-breach event ($\max_{\tau \in [t+24, t+48]} \text{Stage}(\tau) < 205.33\text{ m MSL}$).
  - `None` (null): Unobserved target window.

