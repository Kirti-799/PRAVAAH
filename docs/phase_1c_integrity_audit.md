# PRAVAAH — Phase 1C Data Integrity Audit & Modelling Readiness Report

> **Milestone:** Phase 1C — Data Integrity Audit and Modelling Readiness  
> **Prepared by:** Senior Data Engineer, Hydrological Time-Series Analyst, and ML Validation Group  
> **Date:** October 2026  
> **Status:** Formal Engineering Audit Baseline  

---

## 1. Executive Summary

This report establishes a rigorous data integrity audit, mathematical verification, and modelling-readiness assessment for Project PRAVAAH prior to the commencement of any supervised machine-learning development.

In strict adherence to the project charter, **no machine-learning models (Random Forest, Logistic Regression, Gradient Boosting, or Neural Networks) have been trained**, and **zero artificial flood predictions or fabricated continuous labels have been created**.

### Key Audit Findings:
1. **Hathnikund Upstream Discharge Dataset Verified:** The acquired dataset ([`data/raw/hydrological/riverdischarge_manual_daily_irrigation-water-resources-department-haryana_hr_2001_2025.csv`](file:///c:/Users/kirti%20antil/OneDrive/Desktop/PRAVAAH/data/raw/hydrological/riverdischarge_manual_daily_irrigation-water-resources-department-haryana_hr_2001_2025.csv)) contains 123,073 records across 52 stations. 5,192 daily records for Hathnikund Barrage (`HKB U/S` and `HKB D/S`) spanning **January 1, 2018 to August 12, 2025** were verified with **0.00% missing values in discharge**, capturing historic flood surges (August 2019: $17,623\text{ m}^3/\text{s}$; September 2022: $8,380\text{ m}^3/\text{s}$; July 2023: $8,343\text{ m}^3/\text{s}$).
2. **IMD Rainfall Dataset Provenance Clarified:** The raw NWDP IMD file ([`data/raw/rainfall/rainfall_districtwise_daily_imd.csv`](file:///c:/Users/kirti%20antil/OneDrive/Desktop/PRAVAAH/data/raw/rainfall/rainfall_districtwise_daily_imd.csv)) is an operational rolling 2-month snapshot (`2026-08-19` to `2026-10-18`) rather than a multi-year historical archive. For the historical training period (2018–2024), gridded daily precipitation must be acquired from the IMD Pune 0.25° gridded archive.
3. **Temporal Leakage Safeguard Hardened:** An observation cut-off vulnerability was identified and resolved in [`ml/data_processing/align_data.py`](file:///c:/Users/kirti%20antil/OneDrive/Desktop/PRAVAAH/ml/data_processing/align_data.py). Because IMD daily rainfall accumulates over the 24 hours ending at **08:30 IST (03:00 UTC)**, predictions made before 03:00 UTC on date $D$ now strictly look back to completed rainfall from date $D-1$.
4. **Upstream Lag Analysis Methodology Clarified:** The ~48-hour hydrodynamic delay between Hathnikund Barrage and Delhi Old Railway Bridge is derived from **hydraulic peak-to-peak wave transit times** established by CWC and Delhi I&FC, **not from an empirical full-series cross-correlation on real continuous non-flood data**. Full continuous cross-correlation across all 2,600 days cannot be claimed until continuous non-flood downstream stage registers are ingested.
5. **Modelling Dataset Contract Implemented:** A formal verification contract was built in [`ml/data_processing/schema_contract.py`](file:///c:/Users/kirti%20antil/OneDrive/Desktop/PRAVAAH/ml/data_processing/schema_contract.py) to validate schema adherence, temporal causality, and target separation.

---

## 2. Dataset Provenance & Semantic Audit

| Processed Dataset | Source Publisher & Portal | Temporal Coverage on Disk | Geographic Scope & Semantics | Audited Quality on Disk |
| :--- | :--- | :--- | :--- | :--- |
| [`data/processed/hydrological/haryana_hathnikund_discharge_daily_2018_2025.csv`](file:///c:/Users/kirti%20antil/OneDrive/Desktop/PRAVAAH/data/processed/hydrological/haryana_hathnikund_discharge_daily_2018_2025.csv) | Irrigation & Water Resources Dept, Haryana via NWDP CKAN | **2018-01-01 to 2025-08-12** (5,192 records) | Hathnikund Barrage ($30.315^\circ\text{N}, 77.583^\circ\text{E}$): Segregated into `HKB U/S` (Upstream Inflow) and `HKB D/S` (Downstream River Channel Release). | **High Integrity:** 0 null values; 0 duplicates; 100% valid ISO dates; max discharge $17,623.1\text{ m}^3/\text{s}$. |
| [`data/processed/rainfall/imd_yamuna_catchment_daily_rainfall.csv`](file:///c:/Users/kirti%20antil/OneDrive/Desktop/PRAVAAH/data/processed/rainfall/imd_yamuna_catchment_daily_rainfall.csv) | India Meteorological Department via NWDP CKAN | **2026-08-19 to 2026-10-18** (427 records) | Yamunanagar, Karnal, Panipat, Sonipat, and Delhi NCT districts. | **Operational Snapshot:** 0 nulls; valid for recent operational testing, but lacks 2018–2024 historical overlap. |

### Semantic Distinctions Preserved:
- **`HKB U/S` vs `HKB D/S`:** `HKB U/S` measures total inflow arriving from the upper Shivalik/Himalayan catchment; `HKB D/S` measures the net water volume discharged directly into the downstream Yamuna river channel heading toward Delhi after canal diversions (Western Yamuna Canal and Eastern Yamuna Canal).
- **District Rainfall vs Catchment Precipitation:** District-averaged rainfall represents political administrative boundaries, which only approximate the hydrologically contributing watershed polygon.

---

## 3. Temporal Alignment & Target Leakage Audit

The temporal alignment engine in [`ml/data_processing/align_data.py`](file:///c:/Users/kirti%20antil/OneDrive/Desktop/PRAVAAH/ml/data_processing/align_data.py) was audited against strict causal invariants:

```
Prediction Time t (Filtration F_t)
         │
         ├── Upstream discharge Q(t)               [AVAILABLE]
         ├── Upstream lag Q(t - 24h), Q(t - 48h)   [AVAILABLE]
         ├── Completed Rainfall (08:30 IST cutoff) [AVAILABLE]
         │
         ▼
[Embargo Window: t to t + 24h] ──> [Forward Target Window: t + 24h to t + 48h]
                                                  │
                                                  ▼
                                 Target: max(Stage) >= 205.33 m MSL
```

### Critical Safeguards Verified:
1. **Rainfall Gating at 08:30 IST:**  
   If prediction time $t$ in UTC is $< 03:00\text{ UTC}$ (08:30 IST), daily rainfall for calendar date $D$ is incomplete; the aligner automatically assigns completed rainfall from date $D-1$, preventing lookahead leakage.
2. **Missing Target vs Negative Target Distinction:**  
   If downstream observations are missing during $[t+24\text{h}, t+48\text{h}]$, the sample is assigned `is_target_observed = False` and `target_danger_breach = None`. Treating missing periods as non-floods (`0`) is strictly blocked.
3. **Zero Silent Forward-Filling:**  
   The aligner does not interpolate across multi-day telemetry gaps.

---

## 4. Verification of the Target Definition

* **Target Entity:** Surface water stage elevation of the Yamuna River at Delhi Old Railway Bridge.
* **Station Code:** CWC Site ID `028-MDD` (Coordinates: $28.6625^\circ\text{N}, 77.2489^\circ\text{E}$).
* **Vertical Datum:** Mean Sea Level (MSL).
* **Official Danger Mark:** **205.33 m MSL**.
* **Target Mathematical Formulation:**
  $$y(t) = \mathbb{I}\left( \max_{\tau \in [t+24\text{h}, t+48\text{h}]} \text{Stage}_{\text{ORB}}(\tau) \ge 205.33\,\text{m} \right)$$
* **Temporal Resolution Implication:**  
  Because water level fluctuations during monsoon crests occur on hourly timescales, evaluating $y(t)$ using only daily 08:00 IST readings introduces peak-clipping risk (a surge could crest at 205.80 m at 18:00 IST and recede before the next morning's reading). Therefore, **hourly stage observations are required for production label certification**.

---

## 5. Audit of Upstream-Downstream Lag Analysis

In Phase 1B, an approximate 48-hour delay and a correlation near 0.82 were reported. This Phase 1C audit explicitly clarifies the scientific basis of these numbers:

### Clarification of Terms:
1. **Peak-to-Peak Hydraulic Lag:**  
   The physical travel time required for a high-discharge flood wave released from Hathnikund Barrage to travel down the ~220 km river channel to Delhi Old Railway Bridge. Official CWC flood bulletins and Delhi I&FC flood routing logs document this travel time as **48 to 50 hours** during major monsoon surges.
2. **Time-Series Cross-Correlation Lag:**  
   The statistical shift $k^*$ that maximizes the Pearson correlation $r(k)$ between two continuous, complete time series across all weather regimes.
3. **Operational Forecast Lead Time:**  
   The forward planning horizon required by disaster management authorities to execute evacuations (typically 24 to 48 hours).

### Audit Finding:
The ~48h figure is an established **hydraulic event peak-to-peak transit time**, supported by discrete flood episodes (August 2019, September 2022, July 2023). **It was not computed from a continuous, gap-free 7-year real time-series cross-correlation across all low-flow days**, because continuous downstream stage data for non-flood days is not yet on disk. Statistical baselines must not conflate event peak transit with full-series correlation.

---

## 6. Baseline Evaluation Audit

* **File Audited:** [`ml/evaluation/baselines.py`](file:///c:/Users/kirti%20antil/OneDrive/Desktop/PRAVAAH/ml/evaluation/baselines.py)
* **Finding:** All baseline models (`PersistenceBaseline`, `RecentTrendBaseline`, `UpstreamLagAnalyzer`, and classification metric calculations) were verified via **synthetic unit-test fixtures** in [`ml/tests/test_baselines.py`](file:///c:/Users/kirti%20antil/OneDrive/Desktop/PRAVAAH/ml/tests/test_baselines.py).
* **Integrity Assertion:** **Zero real-data baseline benchmark performance scores are claimed as production results**, because continuous downstream stage ground truth is not yet complete. The baseline code is verified algorithmically, but production benchmarks remain pending data acquisition.

---

## 7. Proposed Chronological ML Evaluation Design

When continuous target data is ingested, future ML models must adhere to the following chronological protocol:

```
[TRAINING SET: 2018-01-01 to 2021-12-31]  (4 years, ~1,460 days, includes Aug 2019 flood)
        │
        ├── [PURGE EMBARGO BUFFER: 48 hours (2021-12-30 to 2022-01-02)]
        │
[VALIDATION SET: 2022-01-01 to 2022-12-31] (1 year, includes Sep 2022 flood, used for tuning)
        │
        ├── [PURGE EMBARGO BUFFER: 48 hours (2022-12-30 to 2023-01-02)]
        │
[FINAL HELD-OUT TEST SET: 2023-01-01 to 2024-12-31] (2 years, includes July 2023 historic peak)
```

### Metric Selection Strategy:
Given severe class imbalance ($< 1\%$ positive breach days):
- **Accuracy is prohibited** as a primary metric.
- **Primary Metrics:** Precision-Recall AUC (PR-AUC), Precision@Recall=0.80, F1-Score, and Brier Score.
- **Event-Level Metrics:** Episode Detection Rate (percentage of distinct multi-day breach episodes correctly alerted at least 24h prior).

---

## 8. Modelling Dataset Contract

A formal contract validator was implemented in [`ml/data_processing/schema_contract.py`](file:///c:/Users/kirti%20antil/OneDrive/Desktop/PRAVAAH/ml/data_processing/schema_contract.py).

### Schema Contract:
* **Predictor Columns:** `feature_upstream_discharge_cumecs_t`, `feature_upstream_discharge_cumecs_t_minus_24h`, `feature_upstream_discharge_cumecs_t_minus_48h`, `feature_upstream_discharge_change_24h`, `feature_catchment_rainfall_actual_mm_t`, `feature_local_stage_m_t`.
* **Target Columns:** `target_window_start_utc`, `target_window_end_utc`, `target_max_stage_m`, `target_danger_breach`, `is_target_observed`.
* **Metadata Columns:** `prediction_timestamp_utc`, `upstream_station_name`, `downstream_station_name`, `lead_time_hours`, `prediction_window_hours`, `danger_threshold_m`, `data_source_upstream`, `data_source_downstream`.

### Contract Rules Enforced by Validator:
1. `prediction_timestamp_utc < target_window_start_utc <= target_window_end_utc`.
2. `feature_upstream_discharge_cumecs_t >= 0.0`.
3. If `is_target_observed == False`, then `target_danger_breach` must be `None` (not 0).
4. If `is_target_observed == True`, then `target_danger_breach` must be `0` or `1`.

---

## 9. Data-Access Blocker & Concrete Acquisition Checklist

The single active blocker preventing supervised model training is the lack of continuous daily/hourly water level observations for Delhi Old Railway Bridge (CWC Station 028-MDD).

### Actionable Acquisition Checklist:
1. **India-WRIS / NWIC API Access:**
   - Register researcher profile at `https://nwdp.nwic.gov.in/user/register` and `https://indiawris.gov.in`.
   - Submit API token request for telemetry station code `CW1YAU000346` / `028-MDD`.
2. **CWC Archival Requisition:**
   - File official data request with the **Chief Engineer, Yamuna Basin Organisation, Central Water Commission, Sewa Bhawan, R.K. Puram, New Delhi** for daily gauge records of Station 028-MDD from 2018 to 2024.
3. **IMD Gridded Historical Rainfall:**
   - Download historical 0.25° gridded daily rainfall NetCDF files (2018–2024) from the IMD Pune Climate Research portal to replace the 2-month operational snapshot.

---

## 10. Audit Decision: CONDITIONAL GO

* **Decision:** **CONDITIONAL GO**
* **Justification:**
  - The data engineering pipeline, temporal alignment engine, event clustering utilities, baseline benchmarks, and schema contract validators are fully constructed and verified with **20 passing automated tests**.
  - Upstream regulatory discharge (Hathnikund 2018–2025) is genuine and verified on disk.
  - Model training must remain blocked until the continuous downstream target register for Station 028-MDD is acquired.
