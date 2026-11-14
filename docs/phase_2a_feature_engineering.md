# PRAVAAH — Phase 2A Feature Engineering & Dataset Specification

> **Milestone:** Phase 2A — Feature Engineering, Exploratory Data Analysis, and Upstream Discharge Forecasting Feasibility  
> **Prepared by:** Senior Machine Learning Engineer, Hydrological Data Scientist, Backend Engineer  
> **Repository:** PRAVAAH (`c:\Users\kirti antil\OneDrive\Desktop\PRAVAAH`)  
> **Date:** October 2026  
> **Target Horizon:** 24-Hour Ahead Downstream Release at Hathnikund Barrage ($Q_{\text{target}}(t + 24\text{h})$)  

---

## 1. Executive Summary & Target Formulation

Phase 2A establishes the machine-learning feature engineering foundation for forecasting river discharge along the Upper Yamuna corridor. 

### Critical Scientific Principle:
Downstream flood-stage prediction at Delhi Old Railway Bridge (CWC Station `028-MDD`) remains **STRICTLY GATED** because continuous target telemetry has not been acquired from CWC / India-WRIS. In Phase 2A, the forecasting objective is formulated strictly as:

$$\hat{Q}_{\text{target}}(t + 24\text{h}) = \text{Forecasted downstream release at Hathnikund Barrage (HKB D/S) 24 hours into the future}$$

### Observation Frequency & Timestamp Convention:
- **Observation Frequency:** Daily observations reported by the Irrigation & Water Resources Department, Haryana.
- **Reporting Timestamp:** 08:00 IST morning gauge reading ($02:30\text{ UTC}$, recorded as `YYYY-MM-DDT08:00:00Z`).
- **Contiguity Requirement:** The target $Q_{\text{target}}(t + 24\text{h})$ is defined **strictly as the observation on date $D + 1\text{ day}$**. If date $D + 1$ is absent from the historical records, date $D$ is assigned a null target (`has_valid_24h_target = False`). **Silent gap-skipping (pairing date $D$ with $D + 2$ or $D + k$) is strictly prohibited.**

---

## 2. Complete Feature Manifest & Mathematical Definitions

Implemented in [`ml/features/feature_manifest.py`](file:///c:/Users/kirti%20antil/OneDrive/Desktop/PRAVAAH/ml/features/feature_manifest.py) and [`ml/features/feature_pipeline.py`](file:///c:/Users/kirti%20antil/OneDrive/Desktop/PRAVAAH/ml/features/feature_pipeline.py):

| Feature Name | Mathematical Formula | Units | Provenance Source | Lookback Window | Operational Availability | Leakage Risk & Safeguards | Classification |
| :--- | :--- | :---: | :--- | :---: | :--- | :--- | :---: |
| **`target_discharge_24h_cumecs`** | $Q_{\text{ds}}(D + 1\text{d})$ | m³/s | Haryana I&WRD (`HKB D/S`) | $+24\text{h}$ | Time $t + 24\text{h}$ (Tomorrow 08:00 IST) | **TARGET VARIABLE:** Strictly isolated from predictor matrix. | `TARGET` |
| **`discharge_current_cumecs`** | $Q_{\text{ds}}(D)$ | m³/s | Haryana I&WRD (`HKB D/S`) | $t$ | Available at issue time $t$ | Current measurement. Zero lookahead. | `OPERATIONAL` |
| **`discharge_lag_1d_cumecs`** | $Q_{\text{ds}}(D - 1\text{d})$ | m³/s | Haryana I&WRD (`HKB D/S`) | $t - 24\text{h}$ | Known 24h prior to issue time | Trailing observation. Null if $D-1$ unobserved. | `OPERATIONAL` |
| **`discharge_lag_2d_cumecs`** | $Q_{\text{ds}}(D - 2\text{d})$ | m³/s | Haryana I&WRD (`HKB D/S`) | $t - 48\text{h}$ | Known 48h prior to issue time | Trailing observation. Null if $D-2$ unobserved. | `OPERATIONAL` |
| **`discharge_lag_3d_cumecs`** | $Q_{\text{ds}}(D - 3\text{d})$ | m³/s | Haryana I&WRD (`HKB D/S`) | $t - 72\text{h}$ | Known 72h prior to issue time | Trailing observation. Null if $D-3$ unobserved. | `OPERATIONAL` |
| **`discharge_lag_7d_cumecs`** | $Q_{\text{ds}}(D - 7\text{d})$ | m³/s | Haryana I&WRD (`HKB D/S`) | $t - 168\text{h}$ | Known 7 days prior to issue time | Trailing observation. Null if $D-7$ unobserved. | `OPERATIONAL` |
| **`discharge_delta_1d_cumecs`** | $Q_{\text{ds}}(D) - Q_{\text{ds}}(D - 1\text{d})$ | m³/s | Derived from `HKB D/S` | $[t - 24\text{h}, t]$ | Available at issue time $t$ | 24-hour rate of change. Trailing only. | `OPERATIONAL` |
| **`discharge_delta_ratio_1d`** | $\frac{Q(D) - Q(D-1)}{Q(D-1) + 1.0}$ | ratio | Derived from `HKB D/S` | $[t - 24\text{h}, t]$ | Available at issue time $t$ | Normalized surge indicator. Trailing only. | `OPERATIONAL` |
| **`discharge_rolling_mean_3d_cumecs`** | $\frac{1}{3}\sum_{k=0}^2 Q(D - k\text{d})$ | m³/s | Derived from `HKB D/S` | $[t - 48\text{h}, t]$ | Available at issue time $t$ | **Strictly trailing window** (never centered). | `OPERATIONAL` |
| **`discharge_rolling_mean_7d_cumecs`** | $\frac{1}{7}\sum_{k=0}^6 Q(D - k\text{d})$ | m³/s | Derived from `HKB D/S` | $[t - 144\text{h}, t]$ | Available at issue time $t$ | Trailing moving average. Requires all 7 days. | `OPERATIONAL` |
| **`discharge_rolling_max_7d_cumecs`** | $\max_{k=0..6} Q(D - k\text{d})$ | m³/s | Derived from `HKB D/S` | $[t - 144\text{h}, t]$ | Available at issue time $t$ | Trailing peak envelope. | `OPERATIONAL` |
| **`discharge_rolling_std_7d_cumecs`** | $\sigma_{\text{sample}}(Q(D - k\text{d}))$ | m³/s | Derived from `HKB D/S` | $[t - 144\text{h}, t]$ | Available at issue time $t$ | Trailing discharge volatility. | `OPERATIONAL` |
| **`inflow_current_cumecs`** | $Q_{\text{us}}(D)$ | m³/s | Haryana I&WRD (`HKB U/S`) | $t$ | Available at morning gauge $t$ | Upstream barrage inflow. | `OPERATIONAL` |
| **`inflow_release_ratio_current`** | $\frac{Q_{\text{us}}(D)}{Q_{\text{ds}}(D) + 1.0}$ | ratio | Derived from `HKB U/S` & `D/S` | $t$ | Available at issue time $t$ | Distinguishes canal diversions vs flood bypass. | `OPERATIONAL` |
| **`rainfall_mean_d_minus_1_mm`** | $\bar{R}(D - 1\text{d})$ | mm/day | IMD 0.25° Gridded (91 cells) | Ended $D-1$ at 08:30 IST | Ended ~23.5h prior to time $t$ | **Zero Lookahead:** Completed before current gauge. | `OPERATIONAL` |
| **`rainfall_max_cell_d_minus_1_mm`** | $\max_{\text{cells}} R(D - 1\text{d})$ | mm/day | IMD 0.25° Gridded | Ended $D-1$ at 08:30 IST | Ended ~23.5h prior to time $t$ | Peak cell storm intensity. | `OPERATIONAL` |
| **`rainfall_accum_3d_prior_mm`** | $\sum_{k=1}^3 \bar{R}(D - k\text{d})$ | mm | Derived from IMD Gridded | $[D-3\text{d}, D-1\text{d}]$ | Known prior to issue time $t$ | Trailing 3-day antecedent catchment volume. | `OPERATIONAL` |
| **`rainfall_accum_7d_prior_mm`** | $\sum_{k=1}^7 \bar{R}(D - k\text{d})$ | mm | Derived from IMD Gridded | $[D-7\text{d}, D-1\text{d}]$ | Known prior to issue time $t$ | Trailing 7-day soil saturation proxy. | `OPERATIONAL` |
| **`rainfall_max_cell_3d_prior_mm`** | $\max_{k=1..3} R_{\text{max}}(D - k)$ | mm/day | Derived from IMD Gridded | $[D-3\text{d}, D-1\text{d}]$ | Known prior to issue time $t$ | Trailing peak storm cell. | `OPERATIONAL` |
| **`rainfall_valid_cells_d_minus_1`** | Count valid cells | count | IMD Extraction Audit | Date $D-1$ | Check on grid completeness | Quality audit flag (91 cells expected). | `OPERATIONAL` |
| **`rainfall_mean_same_day_retro_mm`**| $\bar{R}(D)$ | mm/day | IMD 0.25° Gridded | Ended $D$ at 08:30 IST | **Publication Latency (24–48h)** | **LEAKAGE RISK:** Not available operationally at 08:00 IST. Strictly retrospective research only. | `RETROSPECTIVE_ANALYSIS_ONLY` |
| **`day_of_year`** | Integer $1..366$ | integer | Calendar date of time $t$ | Date $t$ | Known deterministically | Seasonal proxy. | `OPERATIONAL` |
| **`month`** | Integer $1..12$ | integer | Calendar date of time $t$ | Date $t$ | Known deterministically | Calendar month. | `OPERATIONAL` |
| **`sin_doy`** | $\sin\left(\frac{2\pi \cdot \text{doy}}{365.25}\right)$ | index | Cyclical calendar coordinate | Date $t$ | Known deterministically | Continuous cyclical representation. | `OPERATIONAL` |
| **`cos_doy`** | $\cos\left(\frac{2\pi \cdot \text{doy}}{365.25}\right)$ | index | Cyclical calendar coordinate | Date $t$ | Known deterministically | Continuous cyclical representation. | `OPERATIONAL` |
| **`is_monsoon`** | $1 \text{ if } m \in [6,7,8,9] \text{ else } 0$ | binary | Meteorological definition | Date $t$ | Known deterministically | Monsoon regime indicator. | `OPERATIONAL` |

---

## 3. Dataset Assembly & Exclusion Auditing

Generated by [`ml/features/dataset_generator.py`](file:///c:/Users/kirti%20antil/OneDrive/Desktop/PRAVAAH/ml/features/dataset_generator.py) into [`data/processed/modelling/hathnikund_discharge_forecasting_24h.csv`](file:///c:/Users/kirti%20antil/OneDrive/Desktop/PRAVAAH/data/processed/modelling/hathnikund_discharge_forecasting_24h.csv):

- **Modelling Date Range:** `2018-01-01` to `2024-12-31` (7 full calendar years, 2,557 calendar days).
- **Total Generated Rows:** **2,491 rows** (corresponding to all observed `HKB D/S` dates in this period).
- **Missing Calendar Days in HKB D/S:** 66 days across 2018–2024 (e.g. May/June 2020, April/May 2022).
- **Valid 24h Targets:** **2,468 rows** (where date $D+1$ is observed and contiguous).
- **Broken Target Rows:** 23 rows (where date $D+1$ was missing or at the end of the 2024 boundary).
- **Complete Operational Rows:** **2,345 rows** (where all core discharge, rainfall, and seasonal predictors are fully populated without missing history).

### Exclusion Breakdown:
1. Initial 7-day lookback warm-up (January 1–7, 2018): 7 rows lack 7-day rolling history.
2. Calendar gaps in discharge records: 115 rows have incomplete trailing rolling windows due to antecedent gaps.
3. Boundary / missing target days: 23 rows lack valid next-day targets.
4. Total complete operational rows ready for ML evaluation: **2,345 rows**.

---

## 4. Chronological Partitioning & Purge Boundary

| Partition | Calendar Date Range | Total Days | Complete Operational Rows | High-Flow Events Included |
| :--- | :---: | :---: | :---: | :--- |
| **TRAIN** | 2018-01-01 to 2021-12-31 | 1,450 | **1,412** | July 2018, Aug 2018, Sep 2018, August 2019 (6.22 lakh cusecs), July 2021 |
| **VAL** | 2022-01-01 to 2022-12-31 | 334 | **322** | August 2022, September 2022 flood (8,380 cumecs) |
| **TEST** | 2023-01-01 to 2024-12-31 | 707 | **611** | July 2023 catastrophic flood (8,343 cumecs), August 2023, September 2024 |
| **Total** | 2018-01-01 to 2024-12-31 | 2,491 | **2,345** | All 10 verified historical high-flow episodes represented |

### Purge / Gap Boundary:
Because the target is 24 hours ahead ($D + 1$), the target for the final training day (2021-12-31) is observed on 2022-01-01 (the first day of validation). To maintain complete separation, validation evaluation starts strictly on `2022-01-01` predicting `2022-01-02`. Zero target overlap exists across partition boundaries.
