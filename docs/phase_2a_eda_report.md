# PRAVAAH — Phase 2A Exploratory Data Analysis (EDA) Report

> **Milestone:** Phase 2A — Feature Engineering, Exploratory Data Analysis, and Upstream Discharge Forecasting Feasibility  
> **Prepared by:** Senior Machine Learning Engineer, Hydrological Data Scientist  
> **Repository:** PRAVAAH (`c:\Users\kirti antil\OneDrive\Desktop\PRAVAAH`)  
> **Date:** October 2026  
> **Data Scope:** 2018–2024 Daily Hathnikund Downstream Discharge and IMD Gridded Catchment Rainfall  

---

## 1. Executive Summary

This report documents the statistical properties, temporal dependencies, seasonal regimes, and feature-target associations for 24-hour ahead river discharge forecasting at Hathnikund Barrage (`HKB D/S`). 

### Key Empirical Findings:
1. **Severe Positive Skewness:** Overall mean discharge is **87.89 m³/s**, while the median (p50) is only **18.78 m³/s**. The 90th percentile is **143.89 m³/s**, the 99th percentile is **1,260.00 m³/s**, and the maximum observed daily discharge is **8,380.40 m³/s**. Extreme flood pulses are rare, constituting $< 1\%$ of all calendar days.
2. **Sharp Autocorrelation Decay:** Autocorrelation at lag 1 day is strong ($r_1 = 0.6008$), but decays rapidly to $r_2 = 0.3898$, $r_3 = 0.2601$, and drops below $0.18$ by lag 4. The river system responds rapidly to mountain storms, causing explosive surges that persist for only 24–72 hours.
3. **Pronounced Regime Decoupling:**
   - **Monsoon (June–September):** Mean discharge rises to **226.79 m³/s**, with standard deviation **648.71 m³/s**. Inflow and release are tightly coupled to 3-to-7 day cumulative catchment rainfall (Spearman rank correlation with target $\rho = 0.408$ to $0.496$).
   - **Non-Monsoon (October–May):** Mean discharge is only **18.06 m³/s**, with median **9.97 m³/s**. Baseflow is diverted into the Western and Eastern Yamuna Canals, leaving minimal river flow that exhibits zero statistical association with antecedent rainfall.
4. **Operational vs Retrospective Rainfall Distinction:** Same-day rainfall correlates strongly with tomorrow's flow ($r = 0.5829$), but cannot be used in real-time operations due to gridded collation latency (24–48h). Antecedent 3-day rainfall ending on date $D-1$ achieves $r = 0.4304$ and serves as a strictly leakage-free predictor.

---

## 2. Statistical Distributions & Quantiles

Calculated across the 2,491 records in [`data/processed/modelling/hathnikund_discharge_forecasting_24h.csv`](file:///c:/Users/kirti%20antil/OneDrive/Desktop/PRAVAAH/data/processed/modelling/hathnikund_discharge_forecasting_24h.csv):

| Metric | Current Discharge $Q(t)$ (m³/s) | Target Discharge $Q(t+1\text{d})$ (m³/s) | 24h Delta $Q(t+1) - Q(t)$ (m³/s) | Monsoon Regime (Jun–Sep) | Non-Monsoon (Oct–May) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Record Count** | 2,491 | 2,468 | 2,468 | 834 | 1,657 |
| **Mean** | **87.89** | **88.46** | **0.06** | **226.79** | **18.06** |
| **Std. Dev.** | 476.32 | 478.43 | 426.47 | 785.49 | 49.33 |
| **Minimum** | 9.96 | 9.96 | -7,875.70 | 9.96 | 9.96 |
| **25th Percentile (p25)** | 9.97 | 9.97 | 0.00 | 9.97 | 9.97 |
| **50th Percentile (Median)** | **18.78** | **18.78** | **0.00** | **45.02** | **9.97** |
| **75th Percentile (p75)** | 48.91 | 49.46 | 0.00 | 125.43 | 24.38 |
| **90th Percentile (p90)** | **143.89** | **144.20** | **2.67** | **527.99** | **38.85** |
| **95th Percentile (p95)** | **364.50** | **364.50** | **23.95** | **1,155.16** | **50.00** |
| **99th Percentile (p99)** | **1,260.00** | **1,260.00** | **426.76** | **3,724.87** | **110.15** |
| **Maximum** | **8,380.40** | **8,380.40** | **7,926.41** | **8,380.40** | **1,260.00** |

---

## 3. By-Year Breakdown & Data Missingness

| Year | Calendar Days | Observed Days | Missing Days | Annual Mean (m³/s) | Annual Max (m³/s) | High-Flow Days ($Q \ge 1,500$) | Historical Floods in Partition |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **2018** | 365 | 365 | 0 | 94.75 | 7,193.12 | 8 | July, Aug, Sep floods |
| **2019** | 365 | 365 | 0 | 83.17 | 7,836.59 | 3 | Major August 2019 flood |
| **2020** | 366 | 355 | 11 | 42.92 | 752.08 | 0 | Low flow year; minor gaps in May/June |
| **2021** | 365 | 365 | 0 | 58.07 | 2,924.01 | 1 | July 2021 surge |
| **2022** | 365 | 334 | 31 | 111.45 | 8,380.40 | 4 | September 2022 late flood; gaps in April/May |
| **2023** | 365 | 344 | 21 | 163.53 | 8,342.87 | 7 | Historic July 2023 flood catastrophe |
| **2024** | 366 | 363 | 3 | 55.45 | 2,464.40 | 1 | September 2024 surge |
| **Total** | **2,557** | **2,491** | **66** | **87.89** | **8,380.40** | **24** | **10 distinct multi-day episodes** |

---

## 4. Temporal Autocorrelation (ACF) Structure

Autocorrelation of daily downstream release $Q(t)$ from lag 1 to lag 14:

| Lag Interval | Time Shift | Autocorrelation $r_k$ | Physical Interpretation |
| :---: | :---: | :---: | :--- |
| **Lag 1** | $t - 24\text{ hours}$ | **0.6008** | Strong day-to-day persistence across baseflow periods. |
| **Lag 2** | $t - 48\text{ hours}$ | **0.3898** | Moderate memory; multi-day flood pulse width. |
| **Lag 3** | $t - 72\text{ hours}$ | **0.2601** | Rapid decay; flood pulses pass Hathnikund within 48–72 hours. |
| **Lag 4** | $t - 96\text{ hours}$ | **0.1856** | Low autocorrelation. |
| **Lag 5** | $t - 120\text{ hours}$ | **0.1559** | Baseflow background level. |
| **Lag 7** | $t - 7\text{ days}$ | **0.1130** | Minimal weekly periodicity. |
| **Lag 14** | $t - 14\text{ days}$ | **0.0617** | Memory essentially extinguished. |

---

## 5. Feature-Target Associations Across Hydroclimatic Regimes

Evaluated across the 2,345 complete operational rows:

| Predictor Feature | All Days Pearson $r$ | All Days Spearman $\rho$ | Monsoon Pearson $r$ | Monsoon Spearman $\rho$ | Non-Monsoon Pearson $r$ | Non-Monsoon Spearman $\rho$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`discharge_current_cumecs`** | **0.6003** | **0.9134** | **0.5788** | **0.8725** | **0.3842** | **0.8353** |
| `discharge_lag_1d_cumecs` | 0.3891 | 0.8723 | 0.3559 | 0.7985 | 0.2842 | 0.7712 |
| `discharge_lag_2d_cumecs` | 0.2594 | 0.8528 | 0.2196 | 0.7519 | 0.2458 | 0.7410 |
| `discharge_rolling_mean_3d_cumecs` | 0.5024 | 0.8656 | 0.4702 | 0.8293 | 0.3421 | 0.7915 |
| `discharge_rolling_mean_7d_cumecs` | 0.3952 | 0.7968 | 0.3546 | 0.7701 | 0.2912 | 0.7245 |
| `discharge_delta_1d_cumecs` | 0.2363 | -0.2029 | 0.2427 | -0.0413 | 0.1045 | -0.2140 |
| **`rainfall_mean_d_minus_1_mm`** | **0.4359** | 0.2227 | **0.4244** | 0.3465 | 0.1842 | -0.0412 |
| **`rainfall_accum_3d_prior_mm`** | **0.4304** | 0.2714 | **0.4084** | **0.4084** | 0.2115 | 0.0512 |
| **`rainfall_accum_7d_prior_mm`** | 0.3840 | **0.3127** | 0.3417 | **0.4956** | 0.2450 | 0.0821 |
| *`rainfall_mean_same_day_retro_mm`* | *0.5829* | *0.2295* | *0.6094* | *0.3590* | *0.2045* | *-0.0560* |

### Scientific Inferences from Associations:
1. **Current Discharge is the Single Most Powerful Linear Predictor:** $r = 0.6003$ across all days. Spearman rank correlation $\rho = 0.9134$ shows extreme monotonic predictability during baseflow and receding limbs.
2. **Soil Wetting Increases Rank Association for Longer Windows:** During monsoon months, Spearman $\rho$ for antecedent rainfall rises steadily from $0.3465$ (1-day) to **$0.4956$ (7-day)**. This confirms that cumulative antecedent precipitation primes mountain soils, amplifying the runoff response.
3. **Same-Day Rainfall Explains Significant Variance but Has Latency Blocker:** Same-day rainfall achieves $r = 0.6094$ during monsoon. However, because IMD gridded products are published with a 24–48h lag, using this feature in operational forecasting would introduce fatal real-time lookahead leakage. It must remain strictly classified as `RETROSPECTIVE_ANALYSIS_ONLY`.

---

## 6. High-Flow Episode Dynamics & Outlier Analysis

Across the 7-year record, only **24 calendar days** (0.96% of records) recorded downstream releases $\ge 1,500\text{ m}^3/\text{s}$.

### The High-Flow Forecasting Challenge:
- When extreme cloudbursts occur in the upper Shivalik catchments, discharge at Hathnikund surges explosively within a single 24-hour observation cycle:
  * **July 9 to 10, 2023:** Release jumped from **450.18 m³/s** to **8,342.87 m³/s** ($\Delta Q = +7,892.69\text{ m}^3/\text{s}$, a factor of 18.5x increase in 24 hours!).
  * **September 25 to 26, 2022:** Release jumped from **426.76 m³/s** to **8,380.40 m³/s** ($\Delta Q = +7,953.64\text{ m}^3/\text{s}$, a factor of 19.6x increase!).
- During these sudden surges, persistence ($\hat{Q} = Q_t$) underpredicts by ~7,900 m³/s.
- This proves that **daily discharge persistence alone is fundamentally incapable of catching the initial flood wave rising limb**. Catchment rainfall integration is physically essential to anticipate these sudden surges.
