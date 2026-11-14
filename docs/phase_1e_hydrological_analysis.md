# PRAVAAH — Phase 1E Non-ML Historical Hydrological Analysis Report

> **Milestone:** Phase 1E — Scientific Data Validation and Non-ML Hydrological Analysis  
> **Prepared by:** Senior Hydrological Data Analyst, Geospatial Data Scientist, FastAPI Engineer  
> **Repository:** PRAVAAH (`c:\Users\kirti antil\OneDrive\Desktop\PRAVAAH`)  
> **Date of Evaluation:** October 2026  
> **Engineering Baseline:** Non-ML Empirical Hydrological Baseline  

---

## 1. Executive Summary & Methodological Principles

This report documents the non-machine-learning historical hydrological analysis of the Upper-to-Middle Yamuna River corridor (Hathnikund Barrage to Delhi Old Railway Bridge). The analysis is conducted strictly on real acquired datasets:
1. **Haryana I&WRD Daily River Discharge (2018–2025):** 5,192 verified daily records for Hathnikund Barrage (`HKB U/S` and `HKB D/S`).
2. **IMD Pune 0.25° Gridded Daily Rainfall (2018–2024):** 2,557 days extracted across the provisional Upper Yamuna bounding box ($28.0^\circ\text{N}-31.0^\circ\text{N}, 76.5^\circ\text{E}-78.0^\circ\text{E}$, 91 cells).

### Strict Scientific Safeguards Enforced:
* **Zero Machine-Learning Models:** No supervised ML classifiers (Random Forest, Logistic Regression, etc.) were trained.
* **Zero Target Stage Estimation:** Downstream water levels at Delhi Old Railway Bridge (CWC Station `028-MDD`) are **not estimated**, because authentic continuous non-flood target telemetry remains restricted on open portals.
* **Zero Lookahead Leakage:** Antecedent rainfall accumulation windows strictly end on date $D-1$, ensuring that rainfall accumulated after morning discharge readings is never used to explain that discharge.

---

## 2. Historical High-Discharge Event Analysis

### Event Definition & Extraction Methodology:
* **Threshold Benchmark:** $Q \ge 1,500\text{ m}^3/\text{s}$ (~53,000 cusecs) observed in either Upstream Inflow (`HKB U/S`) or Downstream Release (`HKB D/S`).
  *(In Haryana I&WRD operational rules, flows exceeding 70,000 cusecs / ~2,000 cumecs trigger canal closures and flood mobilization).*
* **Gap Tolerance:** Discrete daily exceedances separated by $\le 2$ calendar days ($\le 48\text{ hours}$) are merged into a single multi-day episode, adhering to [`ml/data_processing/event_analysis.py`](file:///c:/Users/kirti%20antil/OneDrive/Desktop/PRAVAAH/ml/data_processing/event_analysis.py).
* **Antecedent Precipitation Windows:** Rainfall accumulations over 1-day ($D-1$), 3-day ($D-3$ to $D-1$), 5-day ($D-5$ to $D-1$), and 7-day ($D-7$ to $D-1$) preceding the peak day.

### Extracted Episodes Summary:
Saved in [`data/processed/analysis/historical_high_discharge_episodes.csv`](file:///c:/Users/kirti%20antil/OneDrive/Desktop/PRAVAAH/data/processed/analysis/historical_high_discharge_episodes.csv):

| Episode ID | Start Date | End Date | Dur. (Days) | Peak Date | Peak Inflow HKB U/S (cumecs) | Peak Release HKB D/S (cumecs) | Rain 1d (mm) | Rain 3d (mm) | Rain 7d (mm) | Historical Flood Event Status | Proposed ML Partition |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `EPISODE_2018_01` | 2018-07-26 | 2018-07-30 | 5 | 2018-07-29 | 7,193.1 | 7,193.1 | 51.9 | 118.0 | 168.8 | Observed High Discharge | Train (2018–2021) |
| `EPISODE_2018_02` | 2018-08-13 | 2018-08-14 | 2 | 2018-08-14 | 4,475.0 | 4,475.0 | 29.9 | 46.7 | 71.7 | Observed High Discharge | Train (2018–2021) |
| `EPISODE_2018_03` | 2018-09-25 | 2018-09-25 | 1 | 2018-09-25 | 4,700.6 | 4,700.6 | 38.4 | 74.2 | 74.2 | Observed High Discharge | Train (2018–2021) |
| `EPISODE_2019_04` | 2019-08-18 | 2019-08-20 | 3 | 2019-08-20 | **17,623.1** | 1,522.8 | 14.8 | 71.3 | 100.3 | **DOCUMENTED MAJOR FLOOD** | Train (2018–2021) |
| `EPISODE_2021_05` | 2021-07-29 | 2021-07-29 | 1 | 2021-07-29 | 2,924.0 | 2,924.0 | 42.8 | 56.9 | 74.6 | Observed High Discharge | Train (2018–2021) |
| `EPISODE_2022_06` | 2022-08-11 | 2022-08-12 | 2 | 2022-08-12 | 2,758.6 | 2,758.6 | 15.1 | 16.9 | 45.5 | Observed High Discharge | Validation (2022) |
| `EPISODE_2022_07` | 2022-09-26 | 2022-09-27 | 2 | 2022-09-26 | **8,380.4** | **8,380.4** | 38.9 | 109.7 | 139.0 | **DOCUMENTED MAJOR FLOOD** | Validation (2022) |
| `EPISODE_2023_08` | 2023-07-10 | 2023-07-27 | 18 | 2023-07-10 | **8,342.9** | **8,342.9** | 59.7 | 84.2 | 114.8 | **DOCUMENTED RECORD FLOOD** | Test (2023–2024) |
| `EPISODE_2023_09` | 2023-08-15 | 2023-08-15 | 1 | 2023-08-15 | 1,787.4 | 1,260.0 | 14.8 | 20.6 | 42.4 | Observed High Discharge | Test (2023–2024) |
| `EPISODE_2024_10` | 2024-09-26 | 2024-09-26 | 1 | 2024-09-26 | 2,819.0 | 2,464.4 | 0.0 | 0.0 | 15.0 | Observed High Discharge | Test (2023–2024) |

### Detailed Hydrological Characterization of Major Floods:
1. **August 2019 Historic Inflow Surge:**
   - Inflow `HKB U/S` reached **17,623.08 m³/s** (~622,354 cusecs) on August 20, 2019 following a 3-day catchment rainfall accumulation of 71.3 mm.
   - Delhi Old Railway Bridge recorded a flood crest of **206.60 m MSL** on August 21, 2019, exceeding the Danger Mark (205.33 m) by 1.27 m.
2. **September 2022 Late-Monsoon Surge:**
   - On September 26, 2022, a 3-day rainfall accumulation of 109.7 mm produced a synchronized inflow and downstream release peak of **8,380.40 m³/s** (~295,952 cusecs).
   - Delhi ORB crested at **205.99 m MSL** on September 28, 2022 (~48 hours post-peak).
3. **July 2023 Catastrophic Inundation Episode:**
   - Driven by extreme Shivalik rainfall (single-cell peak 283.0 mm/day on July 9 and 261.6 mm/day on July 10), Hathnikund sustained high release across **18 continuous days** (July 10–27).
   - Release was sustained at >7,000 cumecs for multiple days, causing the Yamuna at Delhi Old Railway Bridge to breach its all-time Highest Flood Level (HFL) reaching **208.66 m MSL** on July 13, 2023, causing extensive inundation of the Ring Road, Red Fort area, and ITO.

---

## 3. Rainfall-Discharge Association Analysis

The statistical relationship between antecedent multi-day catchment rainfall and barrage discharge was evaluated across **2,484 concurrent daily observations** (2018–2024).

Saved in [`data/processed/analysis/rainfall_discharge_association_summary.json`](file:///c:/Users/kirti%20antil/OneDrive/Desktop/PRAVAAH/data/processed/analysis/rainfall_discharge_association_summary.json):

### A. All-Days Regime (Full Year, N = 2,484):
| Antecedent Window | Inflow (HKB U/S) Pearson $r$ | Inflow (HKB U/S) Spearman $\rho$ | Release (HKB D/S) Pearson $r$ | Release (HKB D/S) Spearman $\rho$ |
| :--- | :---: | :---: | :---: | :---: |
| **1-Day ($D-1$)** | 0.556 | 0.588 | **0.579** | 0.218 |
| **3-Day ($D-3$ to $D-1$)** | **0.584** | 0.619 | 0.551 | 0.272 |
| **5-Day ($D-5$ to $D-1$)** | 0.557 | 0.640 | 0.510 | 0.294 |
| **7-Day ($D-7$ to $D-1$)** | 0.545 | **0.652** | 0.475 | 0.312 |

### B. Monsoon Season Regime (June–September, N = 834):
| Antecedent Window | Inflow (HKB U/S) Pearson $r$ | Inflow (HKB U/S) Spearman $\rho$ | Release (HKB D/S) Pearson $r$ | Release (HKB D/S) Spearman $\rho$ |
| :--- | :---: | :---: | :---: | :---: |
| **1-Day ($D-1$)** | 0.522 | 0.499 | **0.609** | 0.364 |
| **3-Day ($D-3$ to $D-1$)** | **0.534** | 0.579 | 0.568 | 0.437 |
| **5-Day ($D-5$ to $D-1$)** | 0.486 | 0.635 | 0.515 | 0.482 |
| **7-Day ($D-7$ to $D-1$)** | 0.462 | **0.678** | 0.471 | **0.520** |

### C. Non-Monsoon Season Regime (October–May, N = 1,650):
| Antecedent Window | Inflow (HKB U/S) Pearson $r$ | Inflow (HKB U/S) Spearman $\rho$ | Release (HKB D/S) Pearson $r$ | Release (HKB D/S) Spearman $\rho$ |
| :--- | :---: | :---: | :---: | :---: |
| **1-Day ($D-1$)** | 0.286 | 0.249 | 0.204 | -0.056 |
| **3-Day ($D-3$ to $D-1$)** | 0.345 | 0.269 | 0.284 | 0.040 |
| **5-Day ($D-5$ to $D-1$)** | 0.359 | 0.275 | 0.295 | 0.075 |
| **7-Day ($D-7$ to $D-1$)** | **0.427** | **0.280** | **0.387** | 0.095 |

---

## 4. Key Hydrological Findings & Discussion

### 1. Cumulative Soil Wetting Governs Inflow (Spearman Rank Peak at 7 Days):
While linear Pearson correlation peaks at 3 days ($r = 0.584$), monotonic rank correlation (Spearman $\rho$) rises steadily from $0.499$ (1-day) to **$0.678$ (7-day)** during the monsoon season.
*Physical Explanation:* Runoff generation in the mountainous upper Yamuna catchment is governed by non-linear antecedent soil moisture conditions. A single isolated rainstorm falling on dry soil produces modest runoff; identical rainfall following 5–7 days of prior rain causes massive surface runoff surges due to saturated hydraulic conductivity limits.

### 2. Immediate Operational Sluice Gate Opening for Downstream Release (Peak at 1 Day):
For downstream release (`HKB D/S`), Pearson correlation peaks at **1-day prior** ($r = 0.609$ in monsoon).
*Physical Explanation:* When extreme inflows arrive at Hathnikund, barrage operators immediately open sluice gates and shut canal intakes within hours to prevent structure overtopping. Thus, downstream river release mirrors 24-hour storm spikes with very short operational response delays.

### 3. Decoupling of Inflow and Release During Dry Season:
In the dry season (October–May), Spearman correlation for `HKB D/S` drops to $\rho \approx -0.056$ to $+0.095$.
*Physical Explanation:* Baseflow entering Hathnikund is diverted into the Western and Eastern Yamuna Canals for municipal and irrigation needs, leaving minimal baseflow in the river channel regardless of minor local precipitation.

---

## 5. Statistical & Hydrological Limitations

1. **Correlation Is Not Causation:** Empirical correlation reflects physical association and operational protocols, but does not represent a hydrodynamically conditioned rainfall-runoff routing model.
2. **Target Water Level Remains Unobserved:** Downstream stage at Delhi Old Railway Bridge (Station `028-MDD`) cannot be predicted from this analysis.
3. **Coarse Daily Temporal Resolution:** Daily readings (06:00/08:00 IST) smooth out instantaneous sub-daily flash flood peaks that occur over 6–12 hour intervals.
4. **Provisional Spatial Bounding Box:** The 91-cell rectangular box does not perfectly isolate the hydrological watershed polygon.

---

## 6. Non-ML Analysis Service & API Delivery

A clean, read-only analytical service was implemented in FastAPI:
* **Endpoints:**
  - `GET /api/hydrology/summary`: Delivers latest observations, multi-window rainfall accumulations, historical discharge distribution quantiles, and data quality audits.
  - `GET /api/hydrology/events`: Delivers the 10 verified multi-day high-discharge episodes.
* **Integrity Guarantee:** Target gauge stage is explicitly returned as `latest_water_level_m = None` and `observation_status = "DATA_RESTRICTED_PENDING_CWC_REQUISITION"`.

---

## 7. Frontend Integration Summary

A dedicated, cream-and-brown styled component was implemented in [`frontend/src/components/hydrology/HistoricalHydrologyPanel.tsx`](file:///c:/Users/kirti%20antil/OneDrive/Desktop/PRAVAAH/frontend/src/components/hydrology/HistoricalHydrologyPanel.tsx) and docked inside the GIS workstation Sidebar:
* **Displays:** Verified upstream inflow and downstream release, antecedent 1d/3d/7d rainfall accumulations, and historical discharge quantiles.
* **Badges:** Explicitly marked "Empirical Non-ML", with "Telemetry Restricted" badge on Delhi ORB stage.
* **Safety Disclaimer:** Prominently warns users that **no flood probability is displayed** because supervised model training remains gated.
