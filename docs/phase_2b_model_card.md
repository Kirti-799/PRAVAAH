# Model Card: Hathnikund Random Forest Regressor v1 (`hathnikund_rf_v1`)

## 1. Model Details

- **Model Identifier:** `hathnikund_rf_v1`
- **Model Type:** Non-Linear Ensemble Regressor (`sklearn.ensemble.RandomForestRegressor`)
- **Version:** 1.0.0 (Phase 2B Research Benchmark)
- **Developed By:** PRAVAAH Hydrological Machine Learning & Geospatial Team
- **Framework & Libraries:**
  - `scikit-learn`: 1.9.1
  - `numpy`: 2.5.4
  - `joblib`: 1.6.0
  - Python 3.14 on Windows
- **Model Artifact:** `ml/models/hathnikund_rf_v1.joblib`
- **Metadata Registry:** `ml/models/hathnikund_rf_v1_metadata.json`
- **License / Governance:** Open Research Dissemination — Strictly Gated Under Phase 2B Decision Protocol

---

## 2. Intended Use & Target Task

### Intended Application
- Research-grade, 24-hour-ahead continuous streamflow forecasting for **Hathnikund Barrage Downstream Release (HKB D/S)**.
- Establishing non-linear machine learning benchmark against persistence, moving average, and linear regression baselines.
- Sensitivity and permutation importance analysis of antecedent rainfall on upstream Himalayan foothill discharge.

### Explicitly Prohibited Applications
1. **NO Delhi Water Level Prediction:** This model does NOT predict water stage (m MSL) at Delhi Old Railway Bridge (CWC Station 028-MDD).
2. **NO Flood Breach Probability:** Does NOT compute danger-mark breach probabilities or flood risk categorizations.
3. **NO Autonomous Emergency Mandates:** Must NEVER be used for emergency evacuation decisions, reservoir dispatch, or flood alerting without human hydrologist review.
4. **NO Out-of-Distribution Surge Reliance:** Must NEVER be assumed to forecast extreme, unprecedented flash floods exceeding training records.

---

## 3. Training & Validation Cohorts

- **Training Period:** 2018-01-08 to 2021-12-31 ($N=1,412$ complete operational days).
- **Validation Period:** 2022-01-01 to 2022-12-31 ($N=322$ complete operational days).
- **Held-Out Test Period:** 2023-01-01 to 2024-12-31 ($N=611$ complete operational days).
- **Input Features (23):** Current and lagged HKB discharge (1d, 2d, 3d, 7d), rates of change, rolling stats (3d, 7d), HKB inflow, antecedent IMD gridded rainfall (1d, 3d, 7d ended at D-1), and astronomical seasonal calendar harmonics.
- **Preprocessing:** `SimpleImputer(strategy="median")` fitted strictly on 2018–2021 training observations.

---

## 4. Hyperparameters

| Hyperparameter | Value | Description |
| :--- | :---: | :--- |
| `n_estimators` | 100 | Number of decision trees in ensemble |
| `max_depth` | 5 | Maximum tree depth (regularized to prevent overfitting) |
| `min_samples_leaf` | 5 | Minimum samples per terminal leaf |
| `random_state` | 42 | Fixed seed for exact reproducibility |
| `n_jobs` | -1 | Parallel execution across available cores |

---

## 5. Performance Summary & Benchmarks

| Metric | Validation (2022, $N=322$) | Held-Out Test (2023–2024, $N=611$) |
| :--- | :---: | :---: |
| **MAE ($\text{m}^3/\text{s}$)** | 77.48 | 95.82 |
| **RMSE ($\text{m}^3/\text{s}$)** | 485.06 | 469.52 |
| **$R^2$ / NSE** | 0.1823 | 0.3796 |
| **Mean Bias ($\text{m}^3/\text{s}$)** | -13.83 | -10.80 |
| **Skill vs. Persistence** | **+0.3202 (+32.0%)** | **-0.2392 (-23.9%)** |
| **High-Flow MAE ($Q \ge 1,500\,\text{m}^3/\text{s}$)** | 2,525.07 ($N=4$) | 2,883.34 ($N=8$) |
| **High-Flow RMSE ($Q \ge 1,500\,\text{m}^3/\text{s}$)** | 4,069.25 ($N=4$) | 3,669.87 ($N=8$) |

---

## 6. Known Failure Modes & Limitations

1. **Structural Tree-Leaf Capping:** Non-linear decision trees cannot predict values higher than the maximum training leaf. On July 11, 2023, when true release surged to 8,343 $\text{m}^3/\text{s}$, the model capped at 2,802 $\text{m}^3/\text{s}$ (60.6% underprediction).
2. **Daily Observation Latency:** IMD gridded rainfall has 24–48h publication latency. Rapid overnight cloudburst floods in upper Uttarakhand cannot be anticipated without real-time radar, satellite, or automatic weather station (AWS) feeds.
3. **Severe Extreme-Event Sample Scarcity:** Over 7 years, only 21 days exceeded 1,500 $\text{m}^3/\text{s}$ in complete operational rows. The model has insufficient historical high-flow exemplars for statistical confidence during extreme disasters.

---

## 7. Operational Status Under Phase 2B Decision Gate

**Status: NOT PROMOTED FOR AUTONOMOUS OPERATIONAL FLOOD WARNING.**
Retained as: **EXPERIMENTAL RESEARCH BENCHMARK**.

### Prerequisites Before Operational Promotion:
1. Ingestion of real-time sub-daily telemetry (hourly barrage gauges and AWS rainfall).
2. Integration of hydrodynamic or physical rainfall-runoff modeling capable of linear/non-linear extrapolation beyond historical records.
3. Calibration against authentic downstream Delhi Old Railway Bridge (Station 028-MDD) stage observations once acquired.
