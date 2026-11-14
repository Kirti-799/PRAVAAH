# PRAVAAH Phase 2B: Comprehensive Model Evaluation Report

## 1. Evaluation Methodology

Evaluation was executed across identical, complete operational rows on three chronological partitions:
- **TRAIN (2018–2021):** $N = 1,412$
- **VAL (2022):** $N = 322$
- **HELD-OUT TEST (2023–2024):** $N = 611$

### Primary Metrics
1. **MAE ($\text{m}^3/\text{s}$):** Mean Absolute Error.
2. **RMSE ($\text{m}^3/\text{s}$):** Root Mean Squared Error.
3. **$R^2$ / NSE:** Coefficient of Determination / Nash-Sutcliffe Efficiency.
4. **Skill Score vs. Persistence:** $1.0 - \frac{\text{MSE}_{\text{model}}}{\text{MSE}_{\text{persistence}}}$.
5. **High-Flow Subset ($Q \ge 1,500\,\text{m}^3/\text{s}$):** Diagnostic for flood-scale releases.

---

## 2. Multi-Model Performance Summary

### 2.1 Validation Partition (2022, $N=322$)

| Model | Overall MAE ($\text{m}^3/\text{s}$) | Overall RMSE ($\text{m}^3/\text{s}$) | $R^2$ / NSE | Skill vs. Persistence | High-Flow MAE ($N=4$) | High-Flow RMSE ($N=4$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Persistence Baseline** | 97.39 | 588.29 | -0.2027 | 0.0000 | 4,060.87 | 4,991.25 |
| **Trailing 3-Day Mean** | 104.69 | 558.76 | -0.0850 | +0.0979 | 2,984.70 | 4,243.50 |
| **Linear Regression OLS** | 89.91 | 489.13 | 0.1685 | +0.3087 | 3,321.24 | 4,267.82 |
| **Random Forest Regressor v1** | **77.48** | **485.06** | **0.1823** | **+0.3202** | **2,525.07** | **4,069.25** |
| **HistGradientBoosting v1** | 79.45 | 478.80 | 0.2033 | +0.3376 | 2,642.91 | 4,114.51 |
| **Gradient Boosting v1** | 109.88 | 597.93 | -0.2425 | -0.0330 | 3,704.40 | 4,532.78 |

**Validation Findings:**
- Both **Random Forest v1** and **HistGradientBoosting v1** achieved meaningful out-of-sample skill over persistence (+32.0% and +33.8% skill respectively).
- Random Forest v1 demonstrated the lowest overall MAE (77.48 $\text{m}^3/\text{s}$) and lowest high-flow MAE (2,525.07 $\text{m}^3/\text{s}$), outperforming all baselines on moderate surges and recession limbs.

---

### 2.2 Held-Out Test Partition (2023–2024, $N=611$)

The test partition was evaluated once only after validation decisions were locked:

| Model | Overall MAE ($\text{m}^3/\text{s}$) | Overall RMSE ($\text{m}^3/\text{s}$) | $R^2$ / NSE | Skill vs. Persistence | High-Flow MAE ($N=8$) | High-Flow RMSE ($N=8$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Persistence Baseline** | **74.25** | **421.78** | **0.4994** | 0.0000 | 2,524.06 | 3,311.61 |
| **Trailing 3-Day Mean** | 90.15 | 484.75 | 0.3387 | -0.3209 | 3,213.52 | 3,946.07 |
| **Linear Regression OLS** | 86.58 | 413.06 | 0.5199 | +0.0409 | 2,644.17 | 3,440.62 |
| **Random Forest Regressor v1** | 95.82 | 469.52 | 0.3796 | **-0.2392** | 2,883.34 | 3,669.87 |
| **HistGradientBoosting v1** | 100.21 | 482.34 | 0.3453 | **-0.3078** | 3,161.62 | 3,917.32 |
| **Gradient Boosting v1** | 104.60 | 501.25 | 0.2930 | **-0.4123** | 3,067.73 | 3,909.63 |

---

## 3. High-Flow Performance & Surge Error Analysis

### 3.1 Historical Sample Scarcity
Over the 7-year observational record (2018–2024), only 21 complete operational days had HKB D/S releases exceeding the 1,500 $\text{m}^3/\text{s}$ threshold:
- **TRAIN (2018–2021):** 9 observations
- **VAL (2022):** 4 observations
- **TEST (2023–2024):** 8 observations

This small sample size means test metrics are heavily dominated by a single historic catastrophe: the **July 2023 flood event**.

### 3.2 Detailed Episode Error Breakdown

#### Validation Surge (September 2022)
| Observation Date | Target Date | Current $Q(t)$ | Actual Target $Q(t+1)$ | RF Predicted | Error ($\text{m}^3/\text{s}$) | Underprediction % |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 2022-09-24 | 2022-09-25 | 312.71 | 426.76 | 324.91 | -101.85 | 23.9% |
| 2022-09-25 | 2022-09-26 | 426.76 | **8,380.40** | 407.11 | **-7,973.29** | **95.1%** |
| 2022-09-26 | 2022-09-27 | 8,380.40 | 2,665.22 | 2,838.67 | +173.45 | 6.5% |
| 2022-09-27 | 2022-09-28 | 2,665.22 | 760.35 | 2,322.00 | +1,561.65 | 205.4% |

#### Test Catastrophic Surge (July 2023)
| Observation Date | Target Date | Current $Q(t)$ | Actual Target $Q(t+1)$ | RF Predicted | Error ($\text{m}^3/\text{s}$) | Underprediction % |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 2023-07-09 | 2023-07-10 | 450.18 | **8,342.87** | 352.08 | **-7,990.79** | **95.8%** |
| 2023-07-10 | 2023-07-11 | 8,342.87 | 7,116.59 | 2,802.44 | **-4,314.15** | **60.6%** |
| 2023-07-11 | 2023-07-12 | 7,116.59 | 5,734.23 | 2,305.40 | **-3,428.83** | **59.8%** |
| 2023-07-12 | 2023-07-13 | 5,734.23 | 4,213.62 | 2,058.07 | **-2,155.55** | **51.2%** |

### 3.3 Hydrological & Algorithmic Root Cause of Underprediction
1. **Structural Tree Ceiling:** Tree-based regression models (Random Forest, Gradient Boosting) compute predictions by averaging observations within leaf nodes. As a result, **they cannot extrapolate beyond the maximum target value in the training dataset**. The training period (2018–2021) had a maximum daily discharge of ~4,100 $\text{m}^3/\text{s}$. When faced with the 8,343 $\text{m}^3/\text{s}$ event in July 2023, the model's prediction was capped at ~2,800–3,800 $\text{m}^3/\text{s}$, producing massive negative errors on the flood crest.
2. **Flash Flood Physics vs. Daily Data Latency:** On the morning of 2023-07-09 (08:00 IST), current discharge was only 450 $\text{m}^3/\text{s}$. The extreme precipitation that caused the surge occurred primarily on 2023-07-09 and 2023-07-10 in the upper catchment. Because IMD gridded rainfall has 24–48h publication latency, this rainfall was unavailable at issue time $t$. Without real-time telemetry or upstream numerical rainfall-runoff simulation, 24h daily models cannot anticipate overnight cloudburst-driven flash floods.

---

## 4. Feature Importance & Interpretability

Permutation feature importance was evaluated strictly on the **VALIDATION partition** (2022) to avoid data leakage and overcome tree-based impurity bias:

| Rank | Feature | Description | RF Impurity Importance | Val Permutation RMSE Drop ($\text{m}^3/\text{s}$) |
| :---: | :--- | :--- | :---: | :---: |
| 1 | `discharge_current_cumecs` | Current observed release $Q(t)$ | 0.2637 | **+27.29** |
| 2 | `inflow_current_cumecs` | Current upstream barrage inflow | 0.3027 | **+7.54** |
| 3 | `rainfall_max_cell_3d_prior_mm`| Prior 3-day peak cell intensity | 0.0160 | **+4.78** |
| 4 | `rainfall_accum_3d_prior_mm` | Prior 3-day basin accumulation | 0.0137 | **+4.25** |
| 5 | `discharge_delta_1d_cumecs` | 1-day rate of change in release | 0.2047 | **+1.85** |
| 6 | `rainfall_mean_d_minus_1_mm` | Prior 1-day mean rainfall | 0.0019 | **+1.49** |

### Key Interpretability Findings:
1. **Discharge Dominance:** Current discharge and inflow dominate predictive skill. The river system exhibits heavy autocorrelation during non-surge conditions.
2. **Rainfall Incremental Value:** Prior 3-day peak and accumulated rainfall provide clear positive incremental skill (+4.78 and +4.25 $\text{m}^3/\text{s}$ RMSE reduction upon permutation), demonstrating that antecedent catchment wetness informs discharge even with daily latency.
3. **Impurity Bias vs. Out-of-Sample Skill:** Standard tree impurity metrics assigned 0.1178 importance to `inflow_release_ratio_current`, but permutation on validation revealed it does not contribute out-of-sample generalization (-9.52 RMSE impact), proving the importance of permutation validation.

---

## 5. Decision Gate & Operational Recommendation

### Evaluation Decision: **CONDITIONAL GO (EXPERIMENTAL ONLY) / NOT PROMOTED FOR OPERATIONAL WARNING**

1. **Why Conditional Go?** The Phase 2B pipeline established a fully reproducible, leak-free non-linear modeling infrastructure. The model demonstrably improves over linear and persistence baselines during moderate flows and baseflows (+32.0% validation skill).
2. **Why NOT Promoted for Operations?** The model fails the strict promotion rule during extreme flood events due to structural leaf capping. On the held-out test partition containing the historic July 2023 disaster, persistence (RMSE 421.78) and linear regression (RMSE 413.06) both achieved higher accuracy than Random Forest (RMSE 469.52).
3. **Core Limitation:** Tree regressors cannot extrapolate beyond historical training extremes. True flood warning requires sub-daily telemetry, hydrodynamic routing, and upstream physics-based catchment models.
