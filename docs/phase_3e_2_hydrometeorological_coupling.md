# PRAVAAH — Phase 3E.2 Hydro-Meteorological Feature Coupling Report

**Document ID:** `docs/phase_3e_2_hydrometeorological_coupling.md`  
**Execution Date:** 2026-11-02  
**Target Milestone:** Phase 3E.2 — Coupling Live Catchment Meteorology with Hathnikund Discharge Forecasting  
**Model Identifier:** `hathnikund_rf_v1` (`RandomForestRegressor`)  
**Lead Time:** 24 Hours Ahead ($Q_{ds}(t + 24\text{h})$ at Hathnikund Barrage)

---

## 1. Executive Summary & Core Decision

Phase 3E.2 investigated the scientific and mathematical feasibility of establishing a real-time connection between live spatial rainfall intelligence (Open-Meteo 20-node catchment sampling) and the existing upstream Hathnikund Barrage discharge model (`hathnikund_rf_v1`).

### The Central Scientific Decision
**Verdict:** **GATED / DISCONNECTED FOR AUTONOMOUS LIVE FLOOD FORECASTING.**  
A dedicated, non-destructive hydrometeorological feature adapter (`ml/features/hydromet_adapter.py`) and coupled inference endpoints (`/api/forecasting/hydromet-status`, `/api/forecasting/predict-coupled`) have been successfully implemented and tested. However, autonomous live forecasting is strictly gated based on two immutable physical barriers:
1. **Absence of Real-Time Discharge Telemetry:** The Random Forest regressor relies on 13 discharge/inflow predictors that account for **>77% of total permutation feature importance** (`discharge_current_cumecs`: 0.2637, `inflow_current_cumecs`: 0.3027, `discharge_delta_1d_cumecs`: 0.2047). Real-time telemetry for Hathnikund Barrage gauge levels does not exist in the repository or via open REST APIs. Substituting training medians (9.97 m³/s) completely nullifies the model's predictive skill during active monsoon surges.
2. **Spatial Footprint & Covariate Shift:** `hathnikund_rf_v1` was trained on 91 coarse IMD 0.25° grid cells spanning a broad regional bounding box ($28.0^\circ\text{N}–31.0^\circ\text{N}, 76.5^\circ\text{E}–78.0^\circ\text{E}$) that includes dry downstream plains and excludes eastern glacial headwaters. Feeding 20-node high-relief Himalayan orographic rainfall directly into features expecting regional box averages induces an uncalibrated covariate distribution shift.

Coupled execution is therefore strictly permitted as an **experimental research benchmark** with user-entered morning gauge observations or historical replays, with explicit disclaimers separating historical observations, live meteorological feeds, and missing telemetry.

---

## 2. Task 1 — Model Feature Audit

### 2.1 Resolution of Feature Count (23 vs 11 Features)
An independent audit of `ml/models/hathnikund_rf_v1_metadata.json`, `ml/training/train_discharge_models.py`, and the serialized model artifact `ml/models/hathnikund_rf_v1.joblib` resolved the exact feature requirements:
* Serialized Estimator: `bundle["model"].n_features_in_ == 23`.
* A prior informal note in Phase 3E.1 hypothesized 11 features; the authentic model requires **exactly 23 features** in its strict operational allowlist (`OPERATIONAL_FEATURE_ALLOWLIST`).

### 2.2 Complete 23-Feature Allowlist Specification

| Feature Name | Category | Units | Lookback Window / Formulation | Training Median | Permutation Importance (Val) |
| :--- | :---: | :---: | :--- | :---: | :---: |
| `discharge_current_cumecs` | Discharge | $\text{m}^3/\text{s}$ | Current morning gauge snapshot $Q_{ds}(t)$ | 9.9688 | **0.2637 (Rank 1)** |
| `discharge_lag_1d_cumecs` | Discharge | $\text{m}^3/\text{s}$ | Lag 1 day ($t - 24\text{h}$) | 9.9688 | 0.0102 |
| `discharge_lag_2d_cumecs` | Discharge | $\text{m}^3/\text{s}$ | Lag 2 days ($t - 48\text{h}$) | 9.9688 | 0.0054 |
| `discharge_lag_3d_cumecs` | Discharge | $\text{m}^3/\text{s}$ | Lag 3 days ($t - 72\text{h}$) | 9.9688 | 0.0041 |
| `discharge_lag_7d_cumecs` | Discharge | $\text{m}^3/\text{s}$ | Lag 7 days ($t - 168\text{h}$) | 9.9688 | 0.0032 |
| `discharge_delta_1d_cumecs` | Discharge | $\text{m}^3/\text{s}$ | Rate of change: $Q_{ds}(t) - Q_{ds}(t - 24\text{h})$ | 0.0000 | **0.2047 (Rank 3)** |
| `discharge_delta_ratio_1d` | Discharge | ratio | Normalized: $(Q_t - Q_{t-1}) / (Q_{t-1} + 1.0)$ | 0.0000 | 0.0028 |
| `discharge_rolling_mean_3d_cumecs`| Discharge | $\text{m}^3/\text{s}$ | Trailing 3-day mean $[t-48\text{h}, t]$ | 9.9688 | 0.0061 |
| `discharge_rolling_mean_7d_cumecs`| Discharge | $\text{m}^3/\text{s}$ | Trailing 7-day mean $[t-144\text{h}, t]$ | 9.9688 | 0.0045 |
| `discharge_rolling_max_7d_cumecs` | Discharge | $\text{m}^3/\text{s}$ | Trailing 7-day peak $[t-144\text{h}, t]$ | 9.9688 | 0.0051 |
| `discharge_rolling_std_7d_cumecs` | Discharge | $\text{m}^3/\text{s}$ | Trailing 7-day sample std $[t-144\text{h}, t]$ | 0.0000 | 0.0021 |
| `inflow_current_cumecs` | Inflow | $\text{m}^3/\text{s}$ | Current upstream inflow $Q_{us}(t)$ | 118.2101 | **0.3027 (Rank 2)** |
| `inflow_release_ratio_current` | Inflow | ratio | Canal diversion index: $Q_{us}(t) / (Q_{ds}(t) + 1.0)$ | 8.4687 | 0.0089 |
| `rainfall_mean_d_minus_1_mm` | Rainfall | $\text{mm}/\text{day}$ | IMD 91-cell spatial mean ending 08:30 IST on $D-1$ | 0.0400 | 0.0098 |
| `rainfall_max_cell_d_minus_1_mm` | Rainfall | $\text{mm}/\text{day}$ | Peak cell rainfall among 91 cells on $D-1$ | 1.6400 | 0.0076 |
| `rainfall_accum_3d_prior_mm` | Rainfall | $\text{mm}$ | Unweighted sum: $\sum_{k=1}^3 RF_{mean}(D-k)$ | 1.0200 | **0.0137 (Rank 4)** |
| `rainfall_accum_7d_prior_mm` | Rainfall | $\text{mm}$ | Unweighted sum: $\sum_{k=1}^7 RF_{mean}(D-k)$ | 5.4900 | 0.0084 |
| `rainfall_max_cell_3d_prior_mm` | Rainfall | $\text{mm}/\text{day}$ | $\max_{k \in \{1,2,3\}} RF_{max}(D-k)$ | 11.6100 | **0.0160 (Rank 5)** |
| `day_of_year` | Calendar | integer | Calendar day index (1..366) | 185.0000 | 0.0065 |
| `month` | Calendar | integer | Calendar month index (1..12) | 7.0000 | 0.0031 |
| `sin_doy` | Calendar | $[-1, 1]$ | $\sin(2\pi \cdot \text{day\_of\_year} / 365.25)$ | -0.0215 | 0.0042 |
| `cos_doy` | Calendar | $[-1, 1]$ | $\cos(2\pi \cdot \text{day\_of\_year} / 365.25)$ | 0.0204 | 0.0039 |
| `is_monsoon` | Calendar | $\{0, 1\}$ | Binary flag: 1 if month $\in \{6,7,8,9\}$ else 0 | 0.0000 | 0.0052 |

### 2.3 Training Methodology and Governance Parameters
* **Target Variable:** `target_discharge_24h_cumecs` ($Q_{ds}(t + 24\text{h})$ in $\text{m}^3/\text{s}$). Next calendar day morning release at Hathnikund Barrage.
* **Forecast Horizon:** Strictly 24 hours.
* **Missing-Value Handling:** `SimpleImputer(strategy='median')` fitted strictly on the TRAIN partition (`2018-01-08` to `2021-12-31`). Zero lookahead or test set leakage.
* **Chronological Partitions:**
  - `TRAIN`: 2018–2021 (N=1,412 complete rows).
  - `VAL`: 2022 (N=322 complete rows) — used for hyperparameter tuning and permutation importance.
  - `HELD-OUT TEST`: 2023–2024 (N=611 complete rows) — includes the catastrophic July 2023 surge (8,343 m³/s).
* **Validation & Test Metrics:**
  - Validation (2022): MAE = 77.48 m³/s, RMSE = 485.06 m³/s, Skill vs Persistence = **+0.3202**.
  - Held-out Test (2023–2024): MAE = 95.82 m³/s, RMSE = 469.52 m³/s, Skill vs Persistence = **-0.2392** (structural tree leaf saturation at 4,120 m³/s during July 2023 peak).
* **Operational Classification:** `EXPERIMENTAL_RESEARCH_BENCHMARK`. Prohibited from autonomous flood warnings.

---

## 3. Task 2 — Temporal Alignment Analysis

### 3.1 Reporting Windows and Timezone Incommensurability
1. **India Standard Time (IST):** IST is UTC + 05:30.
2. **Official IMD Hydrometeorological Cycle:**
   - IMD defines daily rainfall for calendar date $D$ as the 24-hour accumulation ending at **08:30:00 IST** on date $D$.
   - In UTC, this window spans from $(D-1)\text{ 03:00:00 UTC}$ to $D\text{ 03:00:00 UTC}$.
3. **Open-Meteo Default Daily Accumulations:**
   - Open-Meteo queries requesting `"daily": "precipitation_sum"` with `"timezone": "Asia/Kolkata"` aggregate rainfall from **00:00:00 to 23:59:59 IST (midnight to midnight)**.
   - This introduces an **8.5-hour phase shift**:
     - Includes 15.5 hours from date $D-1$ after 08:30 IST.
     - Misses the first 8.5 hours of morning rainfall on date $D$.

### 3.2 Discrete Hourly Slicing Algorithm
To eliminate the 8.5-hour phase shift without interpolating or guessing, the `Rolling24hAccumulator` extracts 24 discrete hourly increments from the Open-Meteo hourly precipitation time series:
$$\text{Window}(D) = \{h \in \text{HourlyTimes} \mid (D-1)\text{ 08:30:00 IST} < h \le D\text{ 08:30:00 IST}\}$$
$$P_{24h, 08:30 IST} = \sum_{i=1}^{24} p_i$$

```python
# Implemented in ml/features/hydromet_adapter.py (Rolling24hAccumulator)
window_start = datetime.combine(prev_date, time(8, 30), tzinfo=IST_TZ)
window_end = datetime.combine(target_date_ist, time(8, 30), tzinfo=IST_TZ)
window_precip = [val for dt, val in parsed_entries if window_start < dt <= window_end]
```
If fewer than 24 valid hourly records exist within the window, the accumulator flags `is_complete_24h_window = False` and documents `missing_hours_count`. Unobserved intervals are **never silently imputed or zero-filled**.

---

## 4. Task 3 — Rainfall Feature Compatibility

### 4.1 Comparative Evaluation: Model Training vs Live Feeds

| Attribute | `hathnikund_rf_v1` Training Setup | Live Catchment Feed (`RainfallService`) | Scientific Verdict |
| :--- | :--- | :--- | :---: |
| **Provider** | IMD Pune (National Climate Centre) | Open-Meteo API (ECMWF IFS / DWD ICON blend) | **Incompatible** (Observation vs NWP Model) |
| **Spatial Extent** | $[28.0^\circ\text{N}–31.0^\circ\text{N}, 76.5^\circ\text{E}–78.0^\circ\text{E}]$ (Plains + Hills) | Catchment polygon $[30.3^\circ\text{N}–31.45^\circ\text{N}, 77.25^\circ\text{E}–78.55^\circ\text{E}]$ | **Domain Shift** (Plains included vs alpine basin) |
| **Sampling Structure**| 91 regular grid cells of 0.25° × 0.25° (~27 km) | 20 strategic elevational nodes (295 m to 5,800 m) | **Structural Mismatch** (Coarse grid vs point cluster) |
| **Accumulation Time** | 08:30 IST to 08:30 IST daily sum | 00:00 to 24:00 IST (requires hourly slicing) | **Conditional** (Aligned via `Rolling24hAccumulator`) |
| **3-Day Antecedent** | Linear sum: $P_{D-1} + P_{D-2} + P_{D-3}$ | Decayed index: $\sum_{i=1}^3 (0.85^i \cdot P_{t-i})$ | **Strictly Incompatible** ($Linear \ne Decayed$) |
| **7-Day Antecedent** | Linear sum: $\sum_{k=1}^7 P_{D-k}$ | Decayed index: $\sum_{i=1}^7 (0.85^i \cdot P_{t-i})$ | **Strictly Incompatible** ($Linear \ne Decayed$) |
| **Peak Cell Feature** | Max among 91 0.25° cells | Max among 20 point sampling nodes | **Variance Discrepancy** (91 cells vs 20 points) |

### 4.2 Proving the Inequality: Linear Sums vs API (Rule 4)
Rule 4 strictly commands: *"Do not assume API-3/7/14 are equivalent to the model's training features."*  
For any non-zero precipitation sequence $P_{t-i}$, the exponential decay factor $k = 0.85$ causes geometric attenuation:
$$\text{API}_3 = 0.85 P_{D-1} + 0.7225 P_{D-2} + 0.6141 P_{D-3} < P_{D-1} + P_{D-2} + P_{D-3} = \text{Linear Accumulation}_{3d}$$
For a uniform 20 mm/day event across 3 days:
* $\text{Linear Accumulation}_{3d} = 60.00\text{ mm}$
* $\text{API}_3 = 43.73\text{ mm}$ ($\Delta = -16.27\text{ mm}$, 27.1% underestimation)

For a 7-day event of 20 mm/day:
* $\text{Linear Accumulation}_{7d} = 140.00\text{ mm}$
* $\text{API}_7 = 72.88\text{ mm}$ ($\Delta = -67.12\text{ mm}$, 47.9% underestimation)

Plugging API-3/7/14 into linear accumulation features would severely under-represent antecedent soil saturation and bias runoff forecasts downward. The new adapter calculates **both** representations independently.

---

## 5. Task 4 & Task 5 — Inference Readiness & Forecast Safety

### 5.1 The Feature Preparation Adapter Architecture
The new module `ml/features/hydromet_adapter.py` provides four non-destructive engines:
1. `Rolling24hAccumulator`: Slices hourly Open-Meteo series to reconstruct the official 08:30 IST window.
2. `HydrometAntecedentCalculator`: Derives true linear sums (`rainfall_accum_3d_prior_mm`, `rainfall_accum_7d_prior_mm`) while maintaining separate API calculation routines.
3. `AstronomicalCalendarCalculator`: Generates deterministic seasonal terms (`day_of_year`, `month`, `sin_doy`, `cos_doy`, `is_monsoon`).
4. `DischargeFeatureCalculator`: Computes the 13 discharge/inflow predictors if operator/historical observations are supplied.
5. `HydrometCouplingAuditor`: Performs gatekeeping audits and blocks autonomous live promotion.
6. `HydrometFeatureAdapter`: Validates and assembles the exact 23-feature vector conforming to `OPERATIONAL_FEATURE_ALLOWLIST`.

### 5.2 API Additions
Two new endpoints have been added to `backend/app/api/routes/forecasting.py`:

#### 1. `GET /api/forecasting/hydromet-status`
Returns complete architectural and scientific audit data:
```json
{
  "service": "PRAVAAH Hydrometeorological Coupling Service",
  "version": "1.0.0",
  "milestone": "Phase 3E.2 — Hydro-Meteorological Feature Coupling",
  "coupling_status": "DISCONNECTED_FOR_AUTONOMOUS_OPERATIONS",
  "decision_rationale": "Autonomous live execution is blocked: Hathnikund discharge telemetry is unavailable in real-time...",
  "has_live_discharge_telemetry": false,
  "has_live_meteorological_feed": true,
  "sampling_nodes_count": 20,
  "temporal_alignment_summary": {
    "imd_reporting_window": "08:30 IST to 08:30 IST accumulation (ending 03:00 UTC)",
    "open_meteo_daily_window": "00:00 to 24:00 IST (midnight to midnight)",
    "phase_shift_hours": 8.5
  },
  "spatial_domain_comparison": {
    "training_dataset_footprint": "91 IMD grid cells across [28.0°N–31.0°N, 76.5°E–78.0°E] (Plains + Hills)",
    "live_sampling_footprint": "20 elevational point nodes across Upper Yamuna basin [30.3°N–31.45°N, 77.25°E–78.55°E]",
    "spatial_domain_match": false
  },
  "promoted_for_operational_disaster_warning": false
}
```

#### 2. `POST /api/forecasting/predict-coupled`
Executes coupled inference and transparently separates inputs:
* `historical_observations_used`: Lists discharge readings (operator-provided or verified historical dataset row).
* `live_meteorological_inputs_used`: Lists live catchment rainfall metrics (20-node mean, accumulations, peak node).
* `missing_or_imputed_inputs`: Explicitly lists telemetry gaps (e.g. `live_discharge_telemetry: UNAVAILABLE_LIVE`).
* `promoted_for_operational_disaster_warning: false`.
* `experimental_warning`: Explicitly prohibits using output as a flood warning or for Delhi evacuation.

---

## 6. Task 6 — Testing & Verification Register

### 6.1 Unit & Integration Test Summary

| Test Suite | File | Tests Run | Result | Key Invariants Verified |
| :--- | :--- | :---: | :---: | :--- |
| **Hydromet Coupling Unit Tests** | `ml/tests/test_hydromet_coupling.py` | 11 | **PASSED** | 08:30 IST slicing, Linear $\ne$ API proof, 23-feature schema order, negative input rejection |
| **Forecasting API Integration Tests** | `backend/tests/test_forecasting.py` | 9 | **PASSED** | Readiness, Model status, Predict, Sample forecast, Hydromet status, Predict-coupled (operator & telemetry-missing) |
| **Catchment Rainfall API Tests** | `backend/tests/test_catchment_rainfall.py` | 11 | **PASSED** | 20-node sampling, 24h/72h/168h forecast accumulations, API-3/7/14 indices |
| **Full Backend Test Suite** | `backend/tests/` | 78 | **PASSED** | Zero regressions across hydrology, spatial, routing, river, and weather modules |
| **Full ML Test Suite** | `ml/tests/` | 134 | **PASSED** | Zero regressions across baselines, models, routing, delineation, features |
| **Frontend Production Build** | `frontend/` | N/A | **PASSED** | Vite production bundle compiled in 852 ms with zero errors |

---

## 7. Files Modified & Created

### Created Files:
* `ml/features/hydromet_adapter.py`: Dedicated hydrometeorological feature adapter (24h accumulator, antecedent calculator, calendar calculator, discharge calculator, coupling auditor, feature assembler).
* `ml/tests/test_hydromet_coupling.py`: 11 unit tests covering temporal alignment, mathematical inequality proofs, and feature assembly.
* `docs/phase_3e_2_hydrometeorological_coupling.md`: This comprehensive scientific audit report.

### Modified Files:
* `backend/app/schemas/forecasting.py`: Added `HydrometCouplingStatusResponse`, `LiveCoupledForecastRequest`, `LiveCoupledForecastResponse`.
* `backend/app/services/forecasting.py`: Integrated `HydrometFeatureAdapter`, added `get_hydromet_status()` and `predict_coupled()`.
* `backend/app/api/routes/forecasting.py`: Added `GET /api/forecasting/hydromet-status` and `POST /api/forecasting/predict-coupled`.
* `backend/tests/test_forecasting.py`: Added 3 integration tests verifying status, operator predictions, and missing telemetry reporting.

---

## 8. Remaining Limitations & Recommendations for Phase 3E.3

1. **Hydrometric Telemetry Deficit:** Real-time discharge data for Hathnikund Barrage ($Q_{ds}$ and $Q_{us}$) cannot be acquired until Haryana Irrigation Department or CWC publishes an open telemetry API. Until then, operational discharge forecasting must remain research-gated.
2. **Retraining Requirement for 20-Node Grid:** To make legitimate operational use of the 20-node catchment rainfall grid, future development (Phase 4) should train a new model variant directly on the 20-node reanalysis time series rather than attempting to project 20-node data into the legacy 91-cell IMD model.
3. **Transition to Phase 3E.3:** With hydro-meteorological feature coupling audited and safely gated, Phase 3E.3 will proceed to connect the tabletop routing simulation to the interactive Leaflet GIS map.

---

## 9. Stop Condition & Review Acknowledgment
Phase 3E.2 is complete. All 7 strict rules have been upheld. Zero commits have been executed; working tree modifications remain intact. Standing by for review before commencing Phase 3E.3.

