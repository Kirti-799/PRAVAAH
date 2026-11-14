# PRAVAAH — Phase 1D Historical Data Completion & Final Dataset Assembly Report

> **Milestone:** Phase 1D — Historical Data Completion and Final Dataset Assembly  
> **Prepared by:** Senior Data Engineer, Geospatial Analyst, Hydrological Time-Series Engineer, ML Pipeline Developer  
> **Repository:** PRAVAAH (`c:\Users\kirti antil\OneDrive\Desktop\PRAVAAH`)  
> **Date of Evaluation:** October 2026  
> **Engineering Baseline:** Phase 1D Final Milestone Completion  

---

## 1. Executive Summary & Objective

Phase 1D resolves the critical historical meteorological data deficit identified in previous audits, constructs a robust ingestion framework for downstream target stage telemetry, and builds the end-to-end dataset assembly pipeline required for the primary flood-hazard prediction target of Project PRAVAAH.

### Primary Prediction Target Definition:
$$\hat{y}(t) = P\left( \max_{\tau \in [t+24\text{h}, t+48\text{h}]} \text{Stage}_{\text{ORB}}(\tau) \ge 205.33\,\text{m MSL} \;\middle|\; \mathcal{F}_t \right)$$

Where:
* $t$: Forecast issuance timestamp in UTC.
* $\mathcal{F}_t$: Filtration containing predictor features strictly observable at or before $t$.
* $\text{Stage}_{\text{ORB}}$: River stage elevation of the Yamuna River at Delhi Old Railway Bridge (CWC Station `028-MDD`).
* $205.33\text{ m MSL}$: Official Central Water Commission (CWC) Danger Mark.
* $[t+24\text{h}, t+48\text{h}]$: Forward prediction window reflecting the 48-hour hydrodynamic travel lag from Hathnikund Barrage.

### Strict Scope Restrictions Enforced:
1. **Zero Machine Learning Models Trained:** No Random Forest, Logistic Regression, Gradient Boosting, or Neural Networks were trained.
2. **Zero Fabricated Environmental Data:** No synthetic flood labels or artificial river stages were placed into production data directories.
3. **Zero Conversion of Missing Targets to Negatives:** Unobserved target periods are strictly preserved as `is_target_observed = False` and `target_danger_breach = None`.
4. **Existing Code & Raw Data Preserved:** Raw files (`data/raw/`) were never overwritten; Phase 1A/1B/1C findings in feasibility reports were preserved.

---

## 2. Initial Repository Audit Baseline

An initial audit of files on disk verified the starting state:
* Upstream discharge archive: [`data/raw/hydrological/riverdischarge_manual_daily_irrigation-water-resources-department-haryana_hr_2001_2025.csv`](file:///c:/Users/kirti%20antil/OneDrive/Desktop/PRAVAAH/data/raw/hydrological/riverdischarge_manual_daily_irrigation-water-resources-department-haryana_hr_2001_2025.csv) (21.83 MB, 123,073 records).
* Hathnikund extracted series: [`data/processed/hydrological/haryana_hathnikund_discharge_daily_2018_2025.csv`](file:///c:/Users/kirti%20antil/OneDrive/Desktop/PRAVAAH/data/processed/hydrological/haryana_hathnikund_discharge_daily_2018_2025.csv) (5,192 daily records, 0 nulls, 0 duplicates).
* Existing rainfall archive: [`data/raw/rainfall/rainfall_districtwise_daily_imd.csv`](file:///c:/Users/kirti%20antil/OneDrive/Desktop/PRAVAAH/data/raw/rainfall/rainfall_districtwise_daily_imd.csv) (7.33 MB) — verified as a rolling 2-month operational snapshot (`2026-08-19` to `2026-10-18`).
* **Confirmed Missing at Start:** Historical daily rainfall covering 2018–2024 and continuous downstream stage records for CWC Station `028-MDD`.

---

## 3. Historical IMD Gridded Rainfall Acquisition

### Official Source Investigation:
* **Publisher:** Climate Application and User Interface Group (CMPG), National Climate Centre, India Meteorological Department (IMD), Pune.
* **Portal Endpoints:**
  - Interactive Portal: `https://imdpune.gov.in/cmpg/Griddata/Rainfall_25_Bin.html`
  - Download Dispatcher: `https://imdpune.gov.in/cmpg/Griddata/rainfall.php`
* **Licensing / Terms:** Government of India Open Data / Academic and Non-commercial Research Use under the National Data Sharing and Accessibility Policy (NDSAP).

### National Grid Specifications:
* **Spatial Resolution:** $0.25^\circ \times 0.25^\circ$ (~27.5 km $\times$ 27.5 km).
* **Grid Extents:** Latitude $6.5^\circ\text{N}$ to $38.5^\circ\text{N}$ (129 points, step 0.25°); Longitude $66.5^\circ\text{E}$ to $100.0^\circ\text{E}$ (135 points, step 0.25°).
* **Array Layout:** $129 \times 135 = 17,415$ single-precision IEEE 754 32-bit floats per day ($69,660\text{ bytes/day}$).
* **Units:** Millimeters per day ($\text{mm/day}$).
* **Temporal Accumulation:** 24-hour accumulation ending at 08:30 IST (03:00 UTC).
* **Missing-Value Sentinel:** `-999.0` (hex `0x00 0xC0 0x79 0xC4`).

### Download Verification:
All 7 required calendar years (2018–2024) were legitimately downloaded directly from the official IMD Pune endpoint and stored unmodified in `data/raw/rainfall/gridded/`:

| Year | File Name | Days | Size (Bytes) | SHA-256 / Format Verification | Download Status |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **2018** | `ind2018_rfp25.grd` | 365 | 25,425,900 | Binary float32, exact byte match ($365 \times 69,660$) | **VERIFIED** |
| **2019** | `ind2019_rfp25.grd` | 365 | 25,425,900 | Binary float32, exact byte match ($365 \times 69,660$) | **VERIFIED** |
| **2020** | `ind2020_rfp25.grd` | 366 (leap) | 25,495,560 | Binary float32, exact byte match ($366 \times 69,660$) | **VERIFIED** |
| **2021** | `ind2021_rfp25.grd` | 365 | 25,425,900 | Binary float32, exact byte match ($365 \times 69,660$) | **VERIFIED** |
| **2022** | `ind2022_rfp25.grd` | 365 | 25,425,900 | Binary float32, exact byte match ($365 \times 69,660$) | **VERIFIED** |
| **2023** | `ind2023_rfp25.grd` | 365 | 25,425,900 | Binary float32, exact byte match ($365 \times 69,660$) | **VERIFIED** |
| **2024** | `ind2024_rfp25.grd` | 366 (leap) | 25,495,560 | Binary float32, exact byte match ($366 \times 69,660$) | **VERIFIED** |
| **Total** | **7 Years** | **2,557** | **178,189,680** | **Complete historical record (2018-01-01 to 2024-12-31)** | **ACQUIRED** |

---

## 4. Catchment Rainfall Extraction & Geospatial Analysis

### Provisional Bounding Box Definition:
* **Latitude Range:** $28.0^\circ\text{N}$ to $31.0^\circ\text{N}$ (grid indices 86 to 98 $\rightarrow$ 13 latitude steps).
* **Longitude Range:** $76.5^\circ\text{E}$ to $78.0^\circ\text{E}$ (grid indices 40 to 46 $\rightarrow$ 7 longitude steps).
* **Total Bounding Box Grid Cells:** $13 \times 7 = 91$ grid cells.

### Geospatial & Hydrological Limitations:
1. **Geometric Approximation:** A rectangular bounding box does not coincide with the true hydrological divide of the Yamuna Basin. It includes some peripheral area of adjacent Ghaggar and Hindon drainages, and clips high-altitude headwaters in Himachal Pradesh/Uttarakhand.
2. **Aggregation Method:** The regional rainfall metric is computed as an unweighted spatial arithmetic mean across valid land pixels within the bounding box ($N_{\text{valid}} \le 91$). It must not be interpreted as a true hypsometrically weighted catchment average.
3. **Missing Value Integrity:** Ocean/external pixels encoded with `-999.0` are strictly preserved as `None` (null) and are **never converted to zero**.

### Extraction Pipeline Implementation:
Implemented in [`ml/data_processing/extract_gridded_rainfall.py`](file:///c:/Users/kirti%20antil/OneDrive/Desktop/PRAVAAH/ml/data_processing/extract_gridded_rainfall.py).
Generated two processed files in `data/processed/rainfall/gridded/`:
1. `imd_gridded_daily_regional_summary_2018_2024.csv`: 2,557 rows containing daily bounding-box metrics (`rainfall_spatial_mean_mm`, `rainfall_spatial_max_mm`, `rainfall_spatial_min_mm`, `valid_cells_count`, `missing_cells_count`).
2. `imd_gridded_daily_cell_rainfall_2018_2024.csv`: 232,687 rows ($2,557 \times 91$) detailing every individual grid cell coordinate, date, and precipitation amount.

### Historical Event Meteorological Verification:
* **July 9, 2023 Cloudburst:** Single-cell peak rainfall reached **283.01 mm/day** at $(30.75^\circ\text{N}, 76.75^\circ\text{E})$ in the upper Shivalik zone directly feeding the Yamuna at Hathnikund.
* **July 10, 2023 Surge:** Regional mean precipitation peaked at **65.53 mm/day** across all 91 cells, coinciding with Hathnikund discharge ramping up to 8,343 cumecs and subsequent record flooding in Delhi.
* **August 18–19, 2019 Storm:** Regional mean precipitation peaked at **51.20 mm/day**, precipitating the historic August 20, 2019 discharge surge of 17,623 cumecs.

---

## 5. Downstream CWC Data Acquisition Workflow

The downstream continuous target observations for Delhi Old Railway Bridge (CWC Station `028-MDD`) remain omitted from open CKAN bulk downloads on NWDP under transboundary river data classifications.

To ensure authorized, transparent, and non-fabricated acquisition, a formal checklist was compiled in [`docs/cwc_target_data_acquisition_checklist.md`](file:///c:/Users/kirti%20antil/OneDrive/Desktop/PRAVAAH/docs/cwc_target_data_acquisition_checklist.md):
1. **Route 1 (India-WRIS / NWIC):** Institutional researcher profile registration and custom telemetry data requisition for Station `028-MDD` / `CW1YAU000346`.
2. **Route 2 (CWC Yamuna Basin Organisation):** Formal departmental letter to Chief Engineer, YBO, Central Water Commission, Sewa Bhawan, R.K. Puram, New Delhi.
3. **Route 3 (Delhi I&FC Department):** Requisition of Delhi Central Flood Control Room gauge logs and monsoon situation bulletins.
4. **Route 4 (RTI Application):** Online Right to Information submission to CPIO, Central Water Commission.

---

## 6. Target-Data Importer Module

To ingest and validate the downstream gauge export once acquired, a reusable module was built in [`ml/data_processing/import_target_gauge.py`](file:///c:/Users/kirti%20antil/OneDrive/Desktop/PRAVAAH/ml/data_processing/import_target_gauge.py).

### Core Features & Validation Rules:
* **Dynamic Column Resolution:** Heuristically resolves or explicitly maps varied telemetry header names (`water_level_m`, `stage_m`, `reading_time`, etc.).
* **Timestamp Standardization:** Converts all valid strings to ISO 8601 UTC datetimes (`YYYY-MM-DDTHH:MM:SSZ`).
* **Duplicate Detection:** Flags and counts duplicated timestamps.
* **Plausibility Bounds:** Validates that water levels lie within physically plausible elevations for Delhi MSL ($190.0\text{ m} \le \text{Stage} \le 215.0\text{ m}$).
* **Preservation of Missing Observations:** Null sentinels (`""`, `NaN`, `null`, `-999.0`, `-9999`) result in `water_level_m = None`, `is_missing = True`, and `is_danger_breached = None`.
* **Zero Silent Conversions:** Unexpected units (e.g. feet) trigger audit warnings without silent mathematical alteration.

---

## 7. Final Dataset Assembly Pipeline

The alignment framework was extended into an end-to-end dataset assembler in [`ml/data_processing/assemble_dataset.py`](file:///c:/Users/kirti%20antil/OneDrive/Desktop/PRAVAAH/ml/data_processing/assemble_dataset.py).

### Separation of Concerns:
```
Prediction Issuance Time t
 ├── Upstream Discharge Q(t), Q(t-24h), Q(t-48h), Delta_Q  [PREDICTORS]
 ├── Completed IMD Rainfall (08:30 IST Cut-off Gated)      [PREDICTORS]
 ├── Metadata (Station codes, horizons, benchmarks)        [METADATA]
 │
 ├── [Purge Buffer: t to t + 24h]                          [EMBARGO]
 │
 └── [Forward Horizon: t + 24h to t + 48h]                 [TARGET WINDOW]
      └── max(Stage) >= 205.33 m MSL                       [TARGET LABEL]
```

### Ingestion of Real Production Data:
The assembler was executed on the verified real predictor data:
* Upstream: [`data/processed/hydrological/haryana_hathnikund_discharge_daily_2018_2025.csv`](file:///c:/Users/kirti%20antil/OneDrive/Desktop/PRAVAAH/data/processed/hydrological/haryana_hathnikund_discharge_daily_2018_2025.csv)
* Rainfall: [`data/processed/rainfall/gridded/imd_gridded_daily_regional_summary_2018_2024.csv`](file:///c:/Users/kirti%20antil/OneDrive/Desktop/PRAVAAH/data/processed/rainfall/gridded/imd_gridded_daily_regional_summary_2018_2024.csv)
* Downstream: Pending authorized acquisition.
* Output: [`data/processed/assembled_modelling_dataset_provisional.csv`](file:///c:/Users/kirti%20antil/OneDrive/Desktop/PRAVAAH/data/processed/assembled_modelling_dataset_provisional.csv) (2,599 records).

### Assembly Audit Metrics:
* Total assembled records: **2,599**
* Observed target windows: **0**
* Unobserved target windows: **2,599**
* Contract validation violations: **0** (100% compliant with `ModellingDatasetContractValidator`)
* Dataset readiness status: `INCOMPLETE_PENDING_TARGET_GROUND_TRUTH`
* Ready for ML training: `False` (strictly preventing unauthorized training)

---

## 8. Automated Testing & Verification Suite

All modules were tested using rigorous, dependency-isolated unit tests in `ml/tests/`:

```
============================= test session starts =============================
platform win32 -- Python 3.14.2, pytest-9.1.1, pluggy-1.6.0
collected 31 items

ml\tests\test_align_data.py ...                                          [  9%]
ml\tests\test_assemble_dataset.py .....                                  [ 25%]
ml\tests\test_baselines.py ....                                          [ 38%]
ml\tests\test_event_analysis.py ...                                      [ 48%]
ml\tests\test_inspect_dataset.py .....                                   [ 64%]
ml\tests\test_schema_contract.py .....                                   [ 80%]
ml\tests\test_target_importer.py ......                                  [100%]

============================= 31 passed in 0.56s ==============================
```

Backend test suite verification:
```
backend\tests\test_health.py ...                                         [100%]
======================== 3 passed, 1 warning in 0.77s =========================
```

---

## 9. Updated Readiness Dimension Tracking

| Dimension | Engineering Requirement | Phase 1C State | Phase 1D State | Evidence / Artifact |
| :---: | :--- | :---: | :---: | :--- |
| **1** | Upstream Predictor Data | READY | **READY** | Hathnikund 2018–2025 (5,192 records, 0 nulls) |
| **2** | Downstream Target Observations | BLOCKED | **BLOCKED** | Station 028-MDD continuous series pending requisition |
| **3** | Ground-Truth Benchmark | READY | **READY** | CWC Danger Mark (205.33 m MSL) verified |
| **4** | Meteorological Predictors | IN PROGRESS | **READY** | IMD Pune 0.25° Gridded (2018–2024, 2,557 days, 178 MB) |
| **5** | Temporal Alignment Engine | READY | **READY** | `align_data.py` & `assemble_dataset.py` with 08:30 IST cut-off |
| **6** | Event Clustering | READY | **READY** | `event_analysis.py` 48h temporal clustering |
| **7** | Non-ML Baselines | READY | **READY** | `baselines.py` verified with synthetic unit tests |
| **8** | Schema Contract & Validator | READY | **READY** | `schema_contract.py` enforcing contract rules |
| **9** | Chronological Split Protocol | READY | **READY** | 48h purge buffer between Train/Val/Test |
| **10** | Code & Pipeline Testing | READY | **READY** | 31 ML tests + 3 Backend tests passing |

**Readiness Score:** **9 of 10 Dimensions READY** (Up from 8 in Phase 1C).

---

## 10. Final Readiness Decision & Gate Verdict

$$\mathbf{CONDITIONAL\; GO}$$

### Justification:
1. **Why Not NO-GO?** The data engineering foundation, geospatial grid extraction, temporal alignment, baseline framework, schema contracts, and upstream predictor archives are complete, verified, and backed by authentic government records and passing automated tests.
2. **Why Not GO?** The primary prediction target requires supervised ground-truth observations at Delhi Old Railway Bridge across both flood and non-flood days. Because continuous non-flood stage observations remain restricted, label construction cannot be finalized. Declaring "GO" without target data would violate scientific integrity.
3. **Condition for Gate Unlocking:** Supervised model training (Phase 2) remains gated until the downstream CWC target gauge export is obtained via the actions defined in [`docs/cwc_target_data_acquisition_checklist.md`](file:///c:/Users/kirti%20antil/OneDrive/Desktop/PRAVAAH/docs/cwc_target_data_acquisition_checklist.md).
