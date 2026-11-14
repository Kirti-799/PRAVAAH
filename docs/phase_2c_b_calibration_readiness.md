# Phase 2C-B: Hydraulic Calibration Readiness & Data Acquisition Register

**Project:** PRAVAAH (Predictive Risk Assessment and Vulnerability Analysis for Adaptive Assistance & Humanitarian Response)  
**Milestone:** Phase 2C-B — Calibration Readiness & Data Acquisition Register  
**Audit Date:** October 2026  
**Status:** Calibration Blocked | Physical Requirements Formally Cataloged  

---

## 1. Executive Statement on Calibration Status

As of Phase 2C-B, the hydrological routing implementation in PRAVAAH is **explicitly uncalibrated against real-world observations along the Yamuna corridor**.

While the mathematical implementation of the Muskingum storage equation is verified and numerically stable, empirical parameter optimization ($K, x$) and hydrodynamic modeling (1D/2D Saint-Venant) cannot proceed until missing downstream observation series and river geometry datasets are acquired.

Any operational claims regarding flood-wave arrival times, peak water levels (m MSL), or inundation boundaries at Delhi are **scientifically ungrounded** under current data availability.

---

## 2. Validation Readiness Hierarchy

Validation is not a monolithic binary; it comprises five distinct levels of scientific evidence. The table below delineates the exact status of each level:

| Validation Level | Core Scientific Question | Required Empirical Observations | Currently Available Evidence | Status | Next Required Action |
| :--- | :--- | :--- | :--- | :---: | :--- |
| **Level 1: Mathematical Verification** | Does the algorithmic implementation strictly adhere to analytical mass conservation and numerical stability bounds? | Closed-form analytical test fixtures, invariant boundary conditions, non-negativity assertions. | 12 deterministic unit tests in `ml/tests/test_routing_tabletop.py` + 6 API integration tests. | **VERIFIED** | Maintain automated CI regression test suite. |
| **Level 2: Historical Event Comparison** | Can the prototype qualitatively reproduce flood-wave attenuation and lag across documented historical episodes? | Upstream inflow release series across verified multi-day high-discharge episodes. | 10 verified historical episodes (2018–2024) in `historical_high_discharge_episodes.csv`. | **CONDITIONALLY FEASIBLE (Sensitivity Only)** | Use historical episodes strictly for exploratory sensitivity testing; clearly label outputs as simulated. |
| **Level 3: Parameter Calibration** | Can reach storage parameters ($K, x$) be objectively optimized to minimize error against observed downstream discharge? | Continuous, synchronized downstream discharge time-series at or near Delhi Old Railway Bridge. | **None.** Downstream observations at Hathnikund represent release at the *same barrage*, not at Delhi. | **BLOCKED** | Ingest continuous downstream discharge telemetry before attempting parameter fitting. |
| **Level 4: Independent Physical Validation** | Can simulated arrival timing and peak attenuation be corroborated against independent intermediate gauges along the 220 km reach? | Time-series from intermediate stations (e.g. Yamunanagar, Karnal, Panipat, Sonipat). | **None.** Intermediate gauges are unmetered or data is absent from repository. | **BLOCKED** | Coordinate with Haryana I&WRD to identify and digitize intermediate reach gauge data. |
| **Level 5: Operational Forecast Validation** | Can the system reliably forecast river stage (m MSL), danger mark breach, and inundation extent at Delhi? | Continuous sub-daily stage observations at CWC Station 028-MDD paired with a verified stage-discharge rating curve. | **None.** Delhi ORB stage observations are restricted; authoritative rating curve is absent. | **STRONGLY BLOCKED** | Strictly prohibit downstream water level prediction and automated emergency alerting. |

---

## 3. Data Acquisition Requirements Register

To transition PRAVAAH from an uncalibrated tabletop simulation prototype to an empirically calibrated hydrological or hydrodynamic routing model, the following empirical datasets must be acquired:

| Data Item | Description & Parameters | Primary Provenance & Authority | Current Status | Criticality for Calibration |
| :--- | :--- | :--- | :---: | :--- |
| **1. CWC Station 028-MDD Continuous Stage** | Hourly / daily water level ($h(t)$ in m MSL) at Delhi Old Railway Bridge (2018–2025). | Central Water Commission (CWC) Lower Yamuna Division | **UNAVAILABLE** (Telemetry restricted under transboundary data policy) | **Absolute Blocker** for calibrating flood wave arrival time and crest magnitude at Delhi. |
| **2. Downstream Rating Curve / Discharges** | Authoritative stage-discharge relationship ($Q = f(h)$) for Delhi ORB across low, medium, and extreme flood flows. | Central Water Commission (CWC) / Delhi I&FC Department | **UNAVAILABLE** | **Absolute Blocker** for converting simulated downstream discharge (cumecs) to water level (m MSL). |
| **3. High-Resolution Bathymetry & Cross-Sections** | Surveyed channel cross-sections ($A(y), B(y)$) spaced every 500 m to 1 km along the 220 km corridor, including bridge piers. | Survey of India / Haryana I&WRD / National Water Informatics Centre (NWIC) | **UNAVAILABLE** | **Required for 1D/2D Hydrodynamic Modeling** (HEC-RAS, Telemac, Saint-Venant). |
| **4. Sub-Daily Hathnikund Release Logs** | Hourly discharge releases and gate opening schedules at Hathnikund Barrage during flood events ($Q > 2,000\text{ m}^3/\text{s}$). | Haryana Irrigation and Water Resources Department (I&WRD) | **UNAVAILABLE** (Only daily aggregated totals exist in repository) | **Required for Fine-Grained Flood Wave Routing** (daily averaging dampens sub-daily flash flood peaks). |
| **5. Lateral Flash Tributary Inflows** | Discharge hydrographs for Som River, Pathrala River, and major agricultural return drains discharging downstream of Hathnikund. | Haryana I&WRD / CWC | **UNAVAILABLE** (Tributaries unmetered or data unacquired) | **Essential for Mass Balance Accuracy**; tributary surges can add $>1,000\text{ m}^3/\text{s}$ unaccounted inflow. |
| **6. Intermediate Barrage Sluice Operations** | Operational gate opening logs, backwater pond levels, and sluice jam reports for Wazirabad and ITO Barrages. | Delhi Jal Board (Wazirabad) / Delhi I&FC & Haryana (ITO) | **UNAVAILABLE** | **Critical Boundary Condition**; barrage gate jamming heavily distorts upstream water levels at Delhi ORB. |
| **7. Spatial Manning's Roughness Field ($n$)** | Calibrated roughness coefficients for main channel ($0.030\text{–}0.040$) and overbank floodplain ($0.050\text{–}0.085$). | Field acoustic Doppler current profiler (ADCP) surveys and aerial DTM land cover classification. | **UNAVAILABLE** | **Required for Calibrated Hydrodynamic Modeling**. |
| **8. Satellite-Observed Flood Inundation Extent** | High-resolution SAR (Sentinel-1 / RISAT-1) water surface masks for historical peak events (e.g. July 2023, August 2019). | NRSC / ISRO Disaster Management Support Programme | **UNAVAILABLE** in repository | **Required for Independent Spatial Validation** of inundation boundaries. |

---

## 4. Minimum Conditions for Operational Model Promotion

Under the scientific governance of PRAVAAH, no routing model shall be designated as "Operational" or used for automated emergency alerting until the following minimum criteria are objectively satisfied:

1. **Continuous Target Validation:** Acquisition of at least 3 distinct multi-day high-flow events with continuous, verified downstream stage records at CWC Station 028-MDD.
2. **Empirical Objective Function Optimization:** Calibration of routing parameters ($K, x$ or Manning's $n$) achieving:
   - Nash-Sutcliffe Efficiency ($\text{NSE}$) $\ge 0.80$ on validation events.
   - Peak timing error $|\Delta t_{\text{peak}}| \le 6\text{ hours}$.
   - Peak crest magnitude error $\le 10\%$.
3. **Dual-Model Corroboration:** Cross-validation between hydrological storage routing (Muskingum) and hydrodynamic 1D/2D Saint-Venant equations.
4. **Independent Peer Audit:** Scientific review and sign-off by a qualified hydrological modeling engineer and regional disaster management authority.

Until these criteria are satisfied, all simulation outputs remain classified as **Tabletop Exploratory Simulations**.
