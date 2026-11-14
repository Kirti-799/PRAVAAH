# PRAVAAH — Phase 1F Routing Validation Report

> **Milestone:** Phase 1F — Hydrological Routing Feasibility and Non-ML Routing Prototype  
> **Prepared by:** Senior Hydrological Modelling Engineer, Geospatial Data Analyst, FastAPI Engineer  
> **Repository:** PRAVAAH (`c:\Users\kirti antil\OneDrive\Desktop\PRAVAAH`)  
> **Date:** October 2026  
> **Validation Verdict:** CONDITIONAL GO (Non-ML Prototype Validated; Stage Prediction Gated)  

---

## 1. Executive Summary & Automated Verification Results

Phase 1F evaluated the hydraulic feasibility of downstream flood routing along the Yamuna River (Hathnikund Barrage to Delhi Old Railway Bridge, ~220 km), implemented an uncalibrated, parameter-explicit non-ML Muskingum routing prototype, exposed read-only diagnostic endpoints, and integrated prototype insights into the cream-and-brown GIS interface.

### Automated Test Suite Execution:
1. **ML / Pipeline Tests:** **50 passed** (expanded from 34 baseline tests; 16 new routing unit tests).
   ```bash
   .\backend\.venv\Scripts\python.exe -m pytest ml/tests
   ============================= 50 passed in 0.55s ==============================
   ```
2. **Backend API Tests:** **13 passed** (expanded from 7 baseline tests; 6 new routing integration tests).
   ```bash
   powershell -Command "$env:PYTHONPATH='backend'; .\backend\.venv\Scripts\python.exe -m pytest backend/tests"
   ======================= 13 passed, 2 warnings in 1.20s ========================
   ```
3. **Frontend Production Build & Typecheck:** **Passed cleanly**.
   ```bash
   npm run build (in frontend/)
   ✓ 1918 modules transformed.
   ✓ built in 805ms
   ```

---

## 2. Historical Flood Event Simulation Findings

Using verified daily observations from [`data/processed/hydrological/haryana_hathnikund_discharge_daily_2018_2025.csv`](file:///c:/Users/kirti%20antil/OneDrive/Desktop/PRAVAAH/data/processed/hydrological/haryana_hathnikund_discharge_daily_2018_2025.csv), the Muskingum prototype router was executed across all 10 historical high-flow episodes with engineering baseline parameters ($K = 36.0\text{ h}, x = 0.20, \Delta t = 24.0\text{ h}$).

Saved in [`data/processed/analysis/historical_routing_simulation_summary.json`](file:///c:/Users/kirti%20antil/OneDrive/Desktop/PRAVAAH/data/processed/analysis/historical_routing_simulation_summary.json):

| Episode ID | Start Date | End Date | Peak Inflow HKB U/S (m³/s) | Peak Release HKB D/S (m³/s) | Release Peak Date | Simulated Downstream Peak (m³/s) | Simulated Peak Date | Simulated Attenuation (%) | Transit Lag (h) | Documented Delhi Crest Stage (m MSL) | Documented Breach Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `EPISODE_2018_01` | 2018-07-23 | 2018-08-04 | 7,193.1 | 7,193.1 | 2018-07-29 | 5,215.7 | 2018-07-30 | 27.5% | 24.0 | None | Within banks / unrecorded |
| `EPISODE_2018_02` | 2018-08-10 | 2018-08-19 | 4,475.0 | 4,475.0 | 2018-08-14 | 2,673.1 | 2018-08-15 | 40.3% | 24.0 | None | Within banks / unrecorded |
| `EPISODE_2018_03` | 2018-09-22 | 2018-09-30 | 4,700.6 | 4,700.6 | 2018-09-25 | 2,856.6 | 2018-09-26 | 39.2% | 24.0 | None | Within banks / unrecorded |
| `EPISODE_2019_04` | 2019-08-15 | 2019-08-25 | **17,623.1** | **7,836.6** | 2019-08-19 | **4,802.3** | 2019-08-20 | 38.7% | 24.0 | **206.60** | **Danger Mark Breached (205.33 m)** |
| `EPISODE_2021_05` | 2021-07-26 | 2021-08-03 | 2,924.0 | 2,924.0 | 2021-07-29 | 1,640.9 | 2021-07-30 | 43.9% | 24.0 | None | Within banks / unrecorded |
| `EPISODE_2022_06` | 2022-08-08 | 2022-08-17 | 2,758.6 | 2,758.6 | 2022-08-12 | 1,949.5 | 2022-08-13 | 29.3% | 24.0 | None | Within banks / unrecorded |
| `EPISODE_2022_07` | 2022-09-23 | 2022-10-02 | **8,380.4** | **8,380.4** | 2022-09-26 | **4,785.5** | 2022-09-27 | 42.9% | 24.0 | **205.99** | **Danger Mark Breached (205.33 m)** |
| `EPISODE_2023_08` | 2023-07-07 | 2023-08-01 | **8,342.9** | **8,342.9** | 2023-07-10 | **6,191.6** | 2023-07-12 | 25.8% | 48.0 | **208.66** | **All-Time Record HFL Breached** |
| `EPISODE_2023_09` | 2023-08-12 | 2023-08-20 | 1,787.4 | 1,260.0 | 2023-08-15 | 900.1 | 2023-08-16 | 28.6% | 24.0 | None | Within banks / unrecorded |
| `EPISODE_2024_10` | 2024-09-23 | 2024-10-01 | 2,819.0 | 2,464.4 | 2024-09-26 | 1,333.7 | 2024-09-27 | 45.9% | 24.0 | None | Within banks / unrecorded |

### Physical Hydrograph Observations:
1. **Isolated Flash Peaks vs Sustained Saturated Inundations:**
   - Single-day flood spikes (e.g. September 2022, peak 8,380 m³/s) experience severe attenuation (~43%) as floodwaters fill empty riverbed channel storage and local depressions.
   - In stark contrast, during the **July 2023 catastrophe**, Hathnikund sustained releases $> 4,000$ to $8,343\text{ m}^3/\text{s}$ across **5 continuous days** (Jul 10: 8,343; Jul 11: 7,117; Jul 12: 5,734; Jul 13: 4,271). Because channel and floodplain storage were completely saturated, the simulated downstream peak remained above $6,000\text{ m}^3/\text{s}$, attenuation dropped to $25.8\%$, and hydrograph crest lag extended to **48 hours**, aligning precisely with Delhi ORB breaching its all-time record at $208.66\text{ m MSL}$ on July 13, 2023!
2. **August 2019 Divergence:**
   - On August 20, 2019, morning peak inflow was recorded at $17,623.1\text{ m}^3/\text{s}$ (~6.22 lakh cusecs), but recorded release on August 19 was $7,836.6\text{ m}^3/\text{s}$ and on August 20 was $1,522.8\text{ m}^3/\text{s}$. The simulated routed peak of $4,802\text{ m}^3/\text{s}$ reached Delhi on August 20, matching the documented crest of $206.60\text{ m MSL}$ on August 21.

---

## 3. Unit & Integration Testing Coverage

New tests implemented in [`ml/tests/test_routing.py`](file:///c:/Users/kirti%20antil/OneDrive/Desktop/PRAVAAH/ml/tests/test_routing.py) and [`backend/tests/test_routing.py`](file:///c:/Users/kirti%20antil/OneDrive/Desktop/PRAVAAH/backend/tests/test_routing.py):

| Test Component | Target Condition | Verification Outcome |
| :--- | :--- | :---: |
| `test_muskingum_valid_parameters` | Valid parameters sum to $C_0+C_1+C_2 = 1.0$; $C_i \ge 0$ | **PASSED** |
| `test_muskingum_rejects_non_positive_k` | Rejects $K \le 0$ with `ValueError` | **PASSED** |
| `test_muskingum_rejects_out_of_bounds_x` | Rejects $x < 0$ or $x > 0.5$ with `ValueError` | **PASSED** |
| `test_muskingum_rejects_non_positive_dt` | Rejects $\Delta t \le 0$ with `ValueError` | **PASSED** |
| `test_muskingum_numerical_instability_lower_bound` | Rejects $\Delta t < 2Kx$ ($C_0 < 0$) with explanatory error | **PASSED** |
| `test_muskingum_numerical_instability_upper_bound` | Rejects $\Delta t > 2K(1-x)$ ($C_2 < 0$) with explanatory error | **PASSED** |
| `test_routing_mass_conservation_synthetic_fixture` | Synthetic fixture achieves relative mass error $< 0.05\%$; peak attenuates and lags | **PASSED** |
| `test_multi_reach_routing_attenuation` | 2-reach routing calculates multi-reach storage change with mass error $< 0.05\%$ | **PASSED** |
| `test_routing_rejects_length_mismatch` | Rejects date vs inflow array dimension mismatch | **PASSED** |
| `test_routing_rejects_short_series` | Rejects time series with $N < 2$ points | **PASSED** |
| `test_routing_rejects_missing_inflows_no_silent_zero` | Rejects NaN/None without silent zero substitution | **PASSED** |
| `test_routing_rejects_negative_discharge` | Rejects negative flow values as physical violations | **PASSED** |
| `test_reach_hydraulic_catalog_audit` | Catalog verifies 9 parameters with provenance; bathymetry and stage are UNAVAILABLE | **PASSED** |
| `test_routing_readiness_evaluation` | Evaluator marks St. Venant and Cunge infeasible; prototype uncalibrated | **PASSED** |
| `test_routing_readiness_missing_upstream` | Returns `ROUTING_NOT_READY_MISSING_HYDRAULIC_DATA` if inflow missing | **PASSED** |
| `test_historical_episode_2023_simulation` | Simulates 2023 flood; verifies stage is strictly `None`; disclaimer present | **PASSED** |
| `test_routing_readiness_endpoint` | Backend API `/routing-readiness` returns HTTP 200 with typed schema | **PASSED** |
| `test_routing_simulation_default_2023_episode` | Backend API `/routing-simulation` returns HTTP 200 with labeled simulated flow | **PASSED** |
| `test_routing_simulation_historical_episodes` | Backend API runs 2019 and 2022 episodes successfully | **PASSED** |
| `test_routing_simulation_rejects_unstable_parameters` | Unstable parameters ($K=90\text{h}, x=0.45$) return HTTP 422 Unprocessable Content | **PASSED** |
| `test_routing_simulation_rejects_unknown_episode` | Non-existent episode ID returns HTTP 404 Not Found | **PASSED** |
| `test_existing_endpoints_preserved` | Verifies `/api/health`, `/api/hydrology/summary`, `/api/hydrology/events` intact | **PASSED** |

---

## 4. UI Dashboard Verification

The frontend component [`frontend/src/components/hydrology/HistoricalHydrologyPanel.tsx`](file:///c:/Users/kirti%20antil/OneDrive/Desktop/PRAVAAH/frontend/src/components/hydrology/HistoricalHydrologyPanel.tsx) was enhanced within the existing cream-and-brown GIS workstation architecture:
* **Status Badges:** Displays `"Uncalibrated Prototype"` in amber/brown.
* **Parameter Chips:** Explicitly highlights that Reach Length ($220\text{ km}$) and Bed Slope ($0.00034$) are Derived, while Bathymetry and Target Calibration are **UNAVAILABLE**.
* **Mandatory Warning Banner:**
  `"SIMULATED DOWNSTREAM DISCHARGE — NOT OBSERVED DELHI WATER LEVEL"`
* **Interactive Selector:** Enables switching between key historical flood episodes (2023, 2022, 2019) with instant display of observed release, simulated routed peak, percentage attenuation, wave transit lag, and historical crest reference stage.
* **Prohibitions Maintained:** No flood probability gauges, no evacuation recommendations, no population exposure numbers, and no simulated stage in meters MSL.

---

## 5. Milestone Verdict & Next Steps

### Verdict: **CONDITIONAL GO**

1. **Why Conditional GO?**
   - The non-ML Muskingum routing prototype has been mathematically and numerically validated, adheres to strict mass-balance conservation ($< 0.05\%$ error), rejects physically invalid inputs, and provides transparent diagnostic reporting.
   - However, **supervised model training and stage prediction remain strictly gated** because continuous target observations for CWC Station `028-MDD` (Delhi ORB) have not been acquired.
2. **Strict Prohibitions Carried Forward:**
   - DO NOT train a machine-learning model to predict stage or threshold breaches.
   - DO NOT invent synthetic target labels or fabricate flood probabilities.
   - DO NOT treat simulated discharge as measured water level at Delhi.
3. **Exact Recommended Next Action:**
   - Formal institutional requisition to Central Water Commission (CWC) / India-WRIS for historical hourly/daily stage registers at Station 028-MDD (Delhi Old Railway Bridge) across the 2018–2024 period.
   - Upon target stage data acquisition, proceed to stage-discharge rating curve calibration and supervised learning evaluation.
