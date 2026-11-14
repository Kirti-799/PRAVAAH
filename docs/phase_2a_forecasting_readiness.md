# PRAVAAH — Phase 2A Forecasting Feasibility & Readiness Report

> **Milestone:** Phase 2A — Feature Engineering, Exploratory Data Analysis, and Upstream Discharge Forecasting Feasibility  
> **Prepared by:** Senior Machine Learning Engineer, Hydrological Data Scientist, Backend Engineer  
> **Repository:** PRAVAAH (`c:\Users\kirti antil\OneDrive\Desktop\PRAVAAH`)  
> **Date:** October 2026  
> **Decision Verdict:** **CONDITIONAL GO** (Upstream Discharge Dataset & Baselines Ready; Downstream Delhi Stage Strictly Gated)  

---

## 1. Executive Summary & Readiness Verdict

Phase 2A established a reproducible, contract-compliant feature engineering pipeline and evaluated the empirical feasibility of forecasting Hathnikund Barrage downstream release 24 hours into the future ($\hat{Q}_{\text{target}}(t + 24\text{h})$).

### Decision Verdict: **CONDITIONAL GO**
1. **Upstream Discharge Forecasting Readiness: READY FOR MACHINE LEARNING (Phase 2B)**
   - The 24-hour upstream forecasting dataset has been deterministically assembled and validated ([`data/processed/modelling/hathnikund_discharge_forecasting_24h.csv`](file:///c:/Users/kirti%20antil/OneDrive/Desktop/PRAVAAH/data/processed/modelling/hathnikund_discharge_forecasting_24h.csv)).
   - Leakage-free baseline benchmarks (Persistence, Trailing Mean, Seasonal-Naive, Linear OLS) were executed across chronological partitions.
   - An interpretable Linear OLS model achieves an $R^2$ of **0.5199** and RMSE of **413.06 m³/s** on the held-out test partition (2023–2024), beating the persistence baseline ($R^2 = 0.4994$, RMSE $= 421.78\text{ m}^3/\text{s}$).
2. **Downstream Delhi Flood-Stage Prediction: STRICTLY GATED & BLOCKED**
   - Continuous water-level observations for CWC Station `028-MDD` (Delhi Old Railway Bridge) have not been acquired.
   - Supervised models for Delhi water level, flood probability, or danger mark breach remain **strictly forbidden**.

---

## 2. Comparative Baseline Evaluation Results

Evaluated across the 2,345 complete operational rows in [`data/processed/analysis/phase_2a_baseline_evaluation.json`](file:///c:/Users/kirti%20antil/OneDrive/Desktop/PRAVAAH/data/processed/analysis/phase_2a_baseline_evaluation.json):

### A. Validation Partition Benchmark (Calendar Year 2022, N = 322):
*Note: Contains the September 2022 late-monsoon flood (peak 8,380 m³/s).*

| Forecasting Model | Sample Count | MAE (m³/s) | RMSE (m³/s) | $R^2$ Score (NSE) | Mean Bias (m³/s) | Skill vs Persistence ($1 - \text{MSE}/\text{MSE}_{\text{pers}}$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Persistence Baseline** ($Q_t$) | 322 | 97.39 | 588.29 | -0.2027 | 0.00 | 0.0000 |
| **Trailing 3-Day Mean** | 322 | 104.69 | 558.76 | -0.0850 | 0.00 | +0.0979 |
| **Seasonal-Naive (DOY Mean)** | 322 | 111.29 | 547.50 | -0.0417 | -42.30 | +0.1339 |
| **Linear Regression (OLS: $Q_t + R_{\text{3d}}$)** | 322 | **89.91** | **489.13** | **+0.1685** | -20.95 | **+0.3087** |

### B. Held-Out Untouched Test Partition (Calendar Years 2023–2024, N = 611):
*Note: Contains the historic July 2023 flood catastrophe (Hathnikund sustained $>7,000$ to $8,343\text{ m}^3/\text{s}$).*

| Forecasting Model | Sample Count | MAE (m³/s) | RMSE (m³/s) | $R^2$ Score (NSE) | Mean Bias (m³/s) | Skill vs Persistence ($1 - \text{MSE}/\text{MSE}_{\text{pers}}$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Persistence Baseline** ($Q_t$) | 611 | **74.25** | 421.78 | +0.4994 | -0.44 | 0.0000 |
| **Trailing 3-Day Mean** | 611 | 90.15 | 484.75 | +0.3387 | -1.12 | -0.3209 |
| **Seasonal-Naive (DOY Mean)** | 611 | 140.48 | 622.72 | -0.0912 | -64.93 | -1.1798 |
| **Linear Regression (OLS: $Q_t + R_{\text{3d}}$)** | 611 | 86.58 | **413.06** | **+0.5199** | -32.24 | **+0.0409** |

### C. Fitted Linear OLS Closed-Form Parameters (Fitted Strictly on TRAIN: 2018–2021):
$$\hat{Q}_{\text{pred}}(t + 24\text{h}) = 19.0503 + 0.5016 \cdot Q(t) + 2.0783 \cdot R_{\text{accum\_3d}}(t)$$
- Autoregressive weight on current discharge: $\beta_1 = 0.5016$.
- Antecedent rainfall coefficient: $\beta_2 = 2.0783\text{ cumecs per mm of 3-day rainfall}$.
- Intercept represents baseflow floor: $\beta_0 = 19.05\text{ m}^3/\text{s}$.

---

## 3. High-Flow Evaluation & Analytical Insights

During the 8 high-flow days in the Test Partition ($Q \ge 1,500\text{ m}^3/\text{s}$):
- **Persistence Error:** MAE $= 2,524.06\text{ m}^3/\text{s}$, RMSE $= 3,311.61\text{ m}^3/\text{s}$.
- **Linear OLS Error:** MAE $= 2,644.17\text{ m}^3/\text{s}$, RMSE $= 3,440.62\text{ m}^3/\text{s}$.
- **Small-Sample Hydrological Reality:** When a cloudburst strikes, release can surge from 450 to 8,343 m³/s in 24 hours. Daily linear models trained on broad historical data cannot capture the extreme non-linear threshold behaviour of saturated Shivalik catchments. This provides the exact empirical rationale for non-linear ML architectures (Gradient Boosted Trees / Random Forests) in Phase 2B.

---

## 4. Leakage Defense & Validation Integrity Audit

1. **Chronological Splitting:** Random k-fold cross-validation was strictly prohibited.
2. **Purge Boundary:** Because the target is 24 hours forward ($D + 1$), the target for the final training day (2021-12-31) is observed on 2022-01-01. Validation strictly starts on `2022-01-01` predicting `2022-01-02`. Zero target window overlap exists across partitions.
3. **Training-Only Preprocessing:** The seasonal-naive day-of-year table and the linear regression normal equations were fitted strictly on the TRAIN partition (1,412 rows). Validation and Test partitions were untouched during fitting.
4. **Rainfall Timing Gating:** All operational rainfall features end on date $D-1$ at 08:30 IST (~23.5 hours before forecast issue time $t$). Same-day rainfall is isolated as `RETROSPECTIVE_ANALYSIS_ONLY`.

---

## 5. Distinction Between Upstream Forecast and Downstream Flood Stage

| Dimension | Upstream Forecast (Phase 2A / 2B) | Downstream Stage Prediction (Strictly Gated) |
| :--- | :--- | :--- |
| **Location** | Hathnikund Barrage, Yamunanagar, Haryana | Delhi Old Railway Bridge (CWC Station 028-MDD), Delhi |
| **Target Variable** | River discharge release ($Q$ in m³/s) | Water surface elevation ($h$ in metres above MSL) |
| **Ground Truth Data** | Haryana I&WRD daily barrage records (Acquired & Verified) | Continuous hourly/daily CWC gauge telemetry (**UNACQUIRED**) |
| **Governing Physics** | Catchment rainfall-runoff & barrage sluice operations | 220 km hydraulic wave propagation & floodplain storage |
| **Current Status** | **VALIDATED & OPERATIONAL AS BASELINE** | **STRICTLY BLOCKED PENDING DATA REQUISITION** |

---

## 6. Recommendations for Phase 2B

1. **Advance Upstream Discharge Modeling to Non-Linear Tree Ensembles:**
   - Train LightGBM / XGBoost / Random Forest regressors to model the non-linear interaction between antecedent rainfall accumulations ($R_{\text{3d}}, R_{\text{7d}}$) and sudden flood spikes.
2. **Enforce Monotonicity Constraints:**
   - Higher antecedent rainfall and higher current flow should never decrease predicted discharge.
3. **Maintain Strict Delhi Flood-Stage Gating:**
   - Under no circumstances predict Delhi water level or flood probabilities until continuous target gauge telemetry is acquired from CWC.
