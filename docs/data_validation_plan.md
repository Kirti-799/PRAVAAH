# PRAVAAH — Data Validation & Quality Assurance Plan

> **Milestone:** Phase 1A — Data Feasibility and Study Region Selection  
> **Author:** Data Engineering & ML Quality Assurance  
> **Status:** Standard Operating Procedure (SOP) & Validation Specifications  
> **Applicability:** All ingested raw, intermediate, and processed datasets  

---

## 1. Principles of Validation

In PRAVAAH, data validation is an empirical gatekeeping process. **A dataset is never marked "validated" simply because its source is known or a file opens successfully.** Validation requires meeting explicit, measurable criteria across data integrity, physical plausibility, temporal coherence, and geospatial alignment.

```
Raw Download ──> [Format & Readability Check] ──> [Physical Range & Anomaly Check]
                          │                                  │
                          ▼                                  ▼
                [Geospatial CRS / Bounds] ──────> [Temporal Alignment & Leakage Gate]
                                                             │
                                                             ▼
                                                [Validation Pass / Quarantine]
```

---

## 2. Exhaustive Validation Checklist & Pass/Fail Criteria

### Check 1: File Readability & Integrity
* **Validation Procedure:** Attempt automated uncorrupted stream reads using the designated parser (e.g., standard CSV reader, NetCDF4 engine, RasterIO GeoTIFF reader).
* **Failure Condition:** Unexpected end-of-file, checksum mismatch, non-UTF-8 corrupt characters in metadata headers, truncated bytes.
* **Reporting:** Return file format, byte size, header presence, and encoding status.

### Check 2: Missing Values & Null Pattern Analysis
* **Validation Procedure:** Compute null count and null percentage per column/band. Identify sentinel missing representations (e.g., `-999`, `-9999`, `999.9`, `NA`, empty strings).
* **Thresholds:**
  - *River stage / discharge telemetry:* Missing rate must be $\le 5\%$ for monsoon periods (June–October) across the target training evaluation window. Days with $>15\%$ missing hourly records cannot be interpolated linearly and must be flagged as unobserved.
  - *Rainfall:* Zero rainfall must be differentiated from missing data (`-999.0` sentinel).
* **Failure Condition:** Undocumented sentinel values parsed as valid physical quantities (e.g., $-999\text{ mm}$ interpreted as negative precipitation).

### Check 3: Duplicate Observations
* **Validation Procedure:** Check primary keys: `(station_id, observation_timestamp)` for time series, `(longitude, latitude, timestamp)` for gridded rasters.
* **Failure Condition:** Any duplicate primary key entry with conflicting values.
* **Action:** Flag conflicting duplicates for manual reconciliation; deduplicate exact byte-identical duplicates.

### Check 4: Timestamp Parsing & Timezone Uniformity
* **Validation Procedure:** Parse all timestamps to ISO 8601 strings and convert strictly to UTC or Indian Standard Time (IST = UTC+05:30) with explicit timezone awareness.
* **Failure Condition:** Ambiguous day-first vs month-first date formats (e.g., `07/08/2023`); naive datetime objects without timezone documentation.

### Check 5: Observation Frequency & Regularity
* **Validation Procedure:** Verify that time-series spacing matches expected cadence ($\Delta t = 1\text{ hour}$ for telemetry; $\Delta t = 24\text{ hours}$ for daily rainfall).
* **Failure Condition:** Undocumented gaps or irregular sampling steps disguised as continuous time-series.

### Check 6: Units & Plausible Physical Value Ranges
Every physical variable must conform to empirical bounding limits:
| Variable | Allowable Physical Range | Fatal Error Condition | Warning Condition |
| :--- | :--- | :--- | :--- |
| `rainfall_daily` | $0.0\text{ mm}$ to $1000.0\text{ mm}$ | $< 0.0\text{ mm}$ or $> 1500.0\text{ mm}$ | $> 350.0\text{ mm}$ (Requires synoptic storm verification) |
| `river_stage_orb` | $200.0\text{ m}$ to $212.0\text{ m MSL}$ | $< 195.0\text{ m}$ or $> 215.0\text{ m}$ | $> 208.5\text{ m}$ (Historical peak verification: 208.66m in 2023) |
| `hathnikund_discharge` | $0\text{ cusecs}$ to $1,000,000\text{ cusecs}$ | $< 0\text{ cusecs}$ or $> 1,200,000\text{ cusecs}$ | $> 500,000\text{ cusecs}$ (Extreme release verification) |
| `terrain_elevation` | $150.0\text{ m}$ to $350.0\text{ m MSL}$ (for NCR) | $< 100.0\text{ m}$ or $> 500.0\text{ m}$ in NCR | Negative hand values ($HAND < 0$) |

### Check 7: Geographic Coverage & Spatial Bounding
* **Validation Procedure:** Intersect bounding boxes of all spatial layers with the study region polygon (Yamunanagar to Delhi NCR: $28.0^\circ\text{N} - 30.5^\circ\text{N}$, $76.8^\circ\text{E} - 77.8^\circ\text{E}$).
* **Failure Condition:** Grids or stations situated outside the hydrologically contributing basin.

### Check 8: Coordinate Reference Systems (CRS)
* **Validation Procedure:** Validate projection metadata. All vector and raster layers must explicitly declare their EPSG code.
* **Standard:** EPSG:4326 for storage/exchange; EPSG:32643 (UTM Zone 43N) for metric distance and area computations.
* **Failure Condition:** Missing projection definition (`CRS = None`) or planar coordinates assumed to be angular lat/lon.

### Check 9: Spatial Resolution Compatibility
* **Validation Procedure:** Document resolution conversion. When resampling DEM (30m) or gridded rainfall (0.25° ~ 27.5km), interpolation methods must be explicitly declared (e.g., bilinear for continuous elevation, conservative area-weighted averaging for rainfall accumulation).

### Check 10: Temporal Coverage & Overlap
* **Validation Procedure:** Verify that input environmental drivers (rainfall, upstream discharge) overlap seamlessly with target ground-truth gauge levels for each training/testing episode.
* **Standard Protocol:** Benchmark training window: 2010–2020; Validation: 2021–2022; Hold-out Test: 2023–2025.

### Check 11: Flood-Event Label Reliability
* **Validation Procedure:** Cross-reference flood events with multiple official records:
  1. CWC gauge danger level breach ($\ge 205.33\text{ m}$).
  2. Delhi Disaster Management Authority (DDMA) emergency evacuation advisories.
  3. Dartmouth Flood Observatory (DFO) flood event catalog.
* **Failure Condition:** Declaring a non-flood day solely because no disaster report was published, without inspecting the gauge stage.

### Check 12: Source Compatibility & Synchronisation
* **Validation Procedure:** Reconcile daily observation cut-offs. IMD rainfall accumulates over the 24 hours ending at 08:30 IST. Daily river gauge summaries typically represent 08:00 IST. The 30-minute timing offset must be explicitly accounted for during feature engineering.

### Check 13: Prevention of Target Leakage
* **Validation Procedure:** Time-stamped feature audit.
* **Strict Rule:** At prediction time $t_0$, no feature may contain information from $t > t_0$.
  - Downstream water level recorded at $t_0 + 12\text{h}$ cannot be an input when predicting flood stage at $t_0 + 48\text{h}$.
  - Upstream barrage discharge from $t_0$ is valid because water takes 48–50 hours to reach the downstream target zone.
  - Future weather forecasts (NWP) may only be used if they represent forecasts generated strictly before or at $t_0$.

### Check 14: Reproducibility & Provenance
* **Validation Procedure:** Every processed artifact in `data/processed/` must be generated by a version-controlled script in `ml/data_processing/` or `geospatial/`. No manual GUI editing in GIS software without a documented processing log and script equivalent.

### Check 15: Licensing & Attribution
* **Validation Procedure:** Verify that usage rights allow research, publication, and software distribution. Attribution guidelines must be added to repository metadata.

---

## 3. Current Execution Status

> [!NOTE]  
> As of Phase 1A baseline setup, **no external production datasets have been downloaded into the local repository**. Therefore, the above automated checks have **not yet been executed on live raw datasets**. The checks defined in this plan will be executed via the `inspect_dataset.py` utility as data files are fetched in subsequent steps.
