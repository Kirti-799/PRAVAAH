# PRAVAAH Phase 2B: Non-Linear Machine Learning Regressors Training Pipeline

## 1. Executive Summary & Objective

Phase 2B of **PRAVAAH** (Predictive Risk Assessment and Vulnerability Analysis for Adaptive Assistance & Humanitarian Response) develops and evaluates non-linear machine learning regressors for forecasting upstream river discharge at **Hathnikund Barrage (HKB D/S)** approximately 24 hours ahead ($Q_{ds}(t + 24\text{h})$ in $\text{m}^3/\text{s}$).

### Strict Problem Formulation
- **Forecasting Target:** Continuous downstream release from Hathnikund Barrage ($Q_{ds}(t + 24\text{h})$).
- **Forecasting Horizon:** 24 hours ahead (next contiguous calendar day morning observation).
- **Prediction Units:** Cubic metres per second ($\text{m}^3/\text{s}$, cumecs).
- **Prohibited Substitutions:** The target is NOT Delhi Old Railway Bridge (Station 028-MDD) water level, NOT flood probability, NOT danger-mark breach, and NOT evacuation requirement. Simulated Muskingum routing outputs are never used as labels.

---

## 2. Chronological Data Partitioning

Data is strictly partitioned chronologically to mirror real-world operational forecasting and prevent temporal lookahead leakage:

| Partition | Time Period | Calendar Dates | Complete Operational Rows | High-Flow Rows ($Q \ge 1,500\,\text{m}^3/\text{s}$) | Purpose |
| :--- | :--- | :--- | :---: | :---: | :--- |
| **TRAIN** | 2018–2021 | 2018-01-08 to 2021-12-31 | 1,412 | 9 | Parameter fitting and learning |
| **VALIDATION** | 2022 | 2022-01-01 to 2022-12-31 | 322 | 4 | Model selection & hyperparameter tuning |
| **HELD-OUT TEST** | 2023–2024 | 2023-01-01 to 2024-12-31 | 611 | 8 | Final untouched evaluation |
| **TOTAL** | 2018–2024 | 2018-01-08 to 2024-12-31 | **2,345** | **21** | Complete operational cohort |

*Note:* Random splitting and k-fold cross-validation across time are strictly prohibited. The held-out test partition (2023–2024), which contains the historic July 2023 flood event, was locked and evaluated only once after validation choices were finalized.

---

## 3. Operational Feature Allowlist & Leakage Safeguards

A strict 23-feature operational allowlist was enforced. All predictors are available at forecast issue time $t$ (08:00 IST morning gauge).

### 3.1 Feature Allowlist (23 Features)

| # | Feature Name | Description & Formula | Lookback Window | Domain Validity |
| :---: | :--- | :--- | :--- | :--- |
| 1 | `discharge_current_cumecs` | Current observed HKB D/S release $Q_{ds}(t)$ | Time $t$ | $\ge 0.0\,\text{m}^3/\text{s}$ |
| 2 | `discharge_lag_1d_cumecs` | Observed HKB D/S release at $t - 24\text{h}$ | $t - 24\text{h}$ | $\ge 0.0\,\text{m}^3/\text{s}$ |
| 3 | `discharge_lag_2d_cumecs` | Observed HKB D/S release at $t - 48\text{h}$ | $t - 48\text{h}$ | $\ge 0.0\,\text{m}^3/\text{s}$ |
| 4 | `discharge_lag_3d_cumecs` | Observed HKB D/S release at $t - 72\text{h}$ | $t - 72\text{h}$ | $\ge 0.0\,\text{m}^3/\text{s}$ |
| 5 | `discharge_lag_7d_cumecs` | Observed HKB D/S release at $t - 168\text{h}$ | $t - 168\text{h}$ | $\ge 0.0\,\text{m}^3/\text{s}$ |
| 6 | `discharge_delta_1d_cumecs` | $Q_{ds}(t) - Q_{ds}(t - 1)$ (1-day rate of change) | $[t - 24\text{h}, t]$ | Real |
| 7 | `discharge_delta_ratio_1d` | $\Delta Q / (Q(t-1) + 1.0)$ (normalized rate of change) | $[t - 24\text{h}, t]$ | Real (no div by 0) |
| 8 | `discharge_rolling_mean_3d_cumecs`| Trailing 3-day mean release | $[t - 48\text{h}, t]$ | $\ge 0.0\,\text{m}^3/\text{s}$ |
| 9 | `discharge_rolling_mean_7d_cumecs`| Trailing 7-day mean release | $[t - 144\text{h}, t]$ | $\ge 0.0\,\text{m}^3/\text{s}$ |
| 10 | `discharge_rolling_max_7d_cumecs` | Trailing 7-day peak release | $[t - 144\text{h}, t]$ | $\ge 0.0\,\text{m}^3/\text{s}$ |
| 11 | `discharge_rolling_std_7d_cumecs` | Trailing 7-day release standard deviation | $[t - 144\text{h}, t]$ | $\ge 0.0\,\text{m}^3/\text{s}$ |
| 12 | `inflow_current_cumecs` | Current observed HKB U/S inflow $Q_{us}(t)$ | Time $t$ | $\ge 0.0\,\text{m}^3/\text{s}$ |
| 13 | `inflow_release_ratio_current` | Inflow to release ratio: $Q_{us}(t) / (Q_{ds}(t) + 1.0)$ | Time $t$ | $\ge 0.0$ (no div by 0) |
| 14 | `rainfall_mean_d_minus_1_mm` | Basin mean rainfall ending at 08:30 IST on $D-1$ | $D-1$ (~23.5h prior) | $\ge 0.0\,\text{mm}$ |
| 15 | `rainfall_max_cell_d_minus_1_mm` | Peak grid cell rainfall on $D-1$ | $D-1$ | $\ge 0.0\,\text{mm}$ |
| 16 | `rainfall_accum_3d_prior_mm` | Trailing 3-day rainfall accumulation $[D-3, D-1]$ | 3 days prior | $\ge 0.0\,\text{mm}$ |
| 17 | `rainfall_accum_7d_prior_mm` | Trailing 7-day rainfall accumulation $[D-7, D-1]$ | 7 days prior | $\ge 0.0\,\text{mm}$ |
| 18 | `rainfall_max_cell_3d_prior_mm` | Trailing 3-day peak single-cell intensity | 3 days prior | $\ge 0.0\,\text{mm}$ |
| 19 | `day_of_year` | Calendar day of year (1 to 366) | Time $t$ | $1 \dots 366$ |
| 20 | `month` | Calendar month (1 to 12) | Time $t$ | $1 \dots 12$ |
| 21 | `sin_doy` | Harmonic cycle: $\sin(2\pi \cdot \text{DOY} / 365.25)$ | Time $t$ | $[-1.0, 1.0]$ |
| 22 | `cos_doy` | Harmonic cycle: $\cos(2\pi \cdot \text{DOY} / 365.25)$ | Time $t$ | $[-1.0, 1.0]$ |
| 23 | `is_monsoon` | Binary meteorological indicator: month $\in [6, 7, 8, 9]$ | Time $t$ | $\{0, 1\}$ |

### 3.2 Explicitly Excluded Columns
1. `target_discharge_24h_cumecs`: Ground truth label. Strictly excluded from $X$.
2. `rainfall_mean_same_day_retro_mm`: IMD gridded products have 24–48h publication latency. Including same-day rainfall introduces retrospective lookahead leakage impossible during real-time dispatch.
3. `rainfall_valid_cells_d_minus_1`: Zero-variance audit flag (constant value 91 in all rows). Excluded.
4. `date`, `timestamp_utc`, `partition`, `target_date`, `has_valid_24h_target`, `is_complete_operational_row`, `missing_feature_flags`: Partition metadata and quality flags.

---

## 4. Preprocessing & Imputation Strategy

- **Imputation:** `SimpleImputer(strategy="median")` fitted **strictly on the TRAIN partition** (2018–2021).
- Training feature medians were saved into metadata (`hathnikund_rf_v1_metadata.json`) to guarantee zero leakage during validation, test evaluation, and inference.
- No scaling was applied to decision trees, preserving exact physical units ($\text{m}^3/\text{s}$, $\text{mm}$, dates).

---

## 5. Candidate Models & Hyperparameter Tuning

Hyperparameter exploration was conducted strictly on the **TRAIN** partition and evaluated on the **VALIDATION** partition (2022). No test data was inspected during tuning.

### Candidate Configurations Evaluated on Validation Set (2022)

| Model Candidate | Key Hyperparameters | Val MAE ($\text{m}^3/\text{s}$) | Val RMSE ($\text{m}^3/\text{s}$) | Val $R^2$ | Val Skill vs Pers. | High-Flow MAE ($\text{m}^3/\text{s}$) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Persistence Baseline** | $Q(t+1) = Q(t)$ | 97.39 | 588.29 | -0.2027 | 0.0000 | 4,060.87 |
| **Trailing 3d Mean** | Rolling 3d mean | 104.69 | 558.76 | -0.0850 | +0.0979 | 2,984.70 |
| **Linear Regression OLS** | Bivariate $(Q(t), \text{RF}_{3d})$ | 89.91 | 489.13 | 0.1685 | +0.3087 | 3,321.24 |
| **Random Forest (d=5)** | $n=100, \text{depth}=5, \text{leaf}=5$ | **77.48** | **485.06** | **0.1823** | **+0.3202** | **2,525.07** |
| **Random Forest (d=6)** | $n=100, \text{depth}=6, \text{leaf}=4$ | 81.08 | 495.27 | 0.1476 | +0.2912 | 2,631.45 |
| **HistGradientBoosting** | $\text{depth}=4, \lambda=10.0, \eta=0.03$ | 79.45 | 478.80 | 0.2033 | +0.3376 | 2,642.91 |
| **Gradient Boosting** | $\text{depth}=3, \eta=0.03, n=100$ | 109.88 | 597.93 | -0.2425 | -0.0330 | 3,704.40 |

### Selection Rationale
`RandomForestRegressor(n_estimators=100, max_depth=5, min_samples_leaf=5, random_state=42)` was selected as the primary non-linear candidate:
1. **Lowest Validation MAE:** 77.48 $\text{m}^3/\text{s}$ (vs 97.39 for persistence, a 20.4% reduction).
2. **Lowest High-Flow MAE:** 2,525.07 $\text{m}^3/\text{s}$ (substantially superior to persistence 4,060.87 and OLS 3,321.24).
3. **Safety & Stability:** Random forest ensembles average predictions across uncorrelated trees, preventing extreme out-of-distribution divergence.

---

## 6. Execution & Reproducibility Instructions

The complete training and evaluation pipeline is fully automated and deterministic:

```bash
# Execute Phase 2B model training pipeline
.\backend\.venv\Scripts\python.exe -m ml.training.train_discharge_models

# Run test suite
.\backend\.venv\Scripts\python.exe -m pytest ml/tests/test_model_training.py backend/tests/test_forecasting.py
```

### Artifacts Emitted:
1. Model Binary: `ml/models/hathnikund_rf_v1.joblib`
2. Model Metadata: `ml/models/hathnikund_rf_v1_metadata.json`
3. Evaluation Analysis: `data/processed/analysis/phase_2b_model_evaluation.json`
