# Phase 2C-B: Tabletop Scenario Simulation Architecture & User Guide

**Project:** PRAVAAH (Predictive Risk Assessment and Vulnerability Analysis for Adaptive Assistance & Humanitarian Response)  
**Milestone:** Phase 2C-B — Tabletop Scenario Simulation  
**Audit Date:** October 2026  
**Status:** Implemented & Verified in API and GIS Workstation  

---

## 1. Overview & Operational Purpose

The Tabletop Scenario Simulation Workstation is a scientific stress-testing interface integrated into PRAVAAH. It allows disaster management planners, hydrologists, and scientific engineers to explore hypothetical upstream flood-wave propagation scenarios across the 220 km Yamuna River reach from Hathnikund Barrage to Delhi Old Railway Bridge.

### Key Objectives:
- Provide transparent, mathematically reproducible flood-wave propagation experiments.
- Demonstrate channel storage attenuation and wave transit lag under varying flood profiles.
- Enable direct parameter sensitivity comparisons (e.g. $K=36\text{h}$ vs $K=48\text{h}$, $x=0.20$ vs $x=0.25$) while explicitly highlighting that parameter sensitivity is not parameter calibration.
- Enforce strict scientific discipline: outputs are purely simulated downstream discharge, with zero fabricated stage levels, zero false flood polygons, and zero automated evacuation recommendations.

---

## 2. API Specifications & Contracts

### 2.1 Presets & Catalog Endpoint
- **Method / Path:** `GET /api/hydrology/tabletop-presets`
- **Response Schema:** `TabletopPresetsResponse`
- **Output:**
  - `presets`: List of pre-configured hypothetical hydrographs (`PRESET_CONSTANT`, `PRESET_GRADUAL_RISE`, `PRESET_FLASH_PULSE`, `PRESET_SUSTAINED_HIGH`).
  - `documented_parameters`: Authoritative baseline ($K=36\text{h}, x=0.20$) and alternative heuristic ($K=48\text{h}, x=0.25$) with complete provenance and stability bounds.
  - `scientific_notice`: Explaining the non-operational nature of tabletop presets.

### 2.2 Tabletop Scenario Simulation Endpoint
- **Method / Path:** `POST /api/hydrology/tabletop-scenario`
- **Request Body (`TabletopScenarioRequest`):**
```json
{
  "scenario_id": "SCENARIO_USER_01",
  "scenario_name": "Hypothetical Flash Surge",
  "scenario_type": "PULSE",
  "scenario_description": "Single-day extreme cloudburst release test",
  "inflow_hydrograph": [400.0, 600.0, 6500.0, 1800.0, 800.0, 500.0, 400.0],
  "time_labels": ["Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6", "Day 7"],
  "initial_outflow_cumecs": null,
  "K_hours": 36.0,
  "x": 0.20,
  "dt_hours": 24.0,
  "subreaches": 1
}
```

- **Validation Rules & Status Codes:**
  - `200 OK`: Simulation successful; returns structured hydrographs, quantitative attenuation, transit lag, mass conservation, reproducibility hash, and explicit caveats.
  - `422 Unprocessable Content`:
    - Discharges $< 0\text{ m}^3/\text{s}$ ("violates physical non-negativity").
    - Non-finite numbers (NaN, $\pm\infty$).
    - Series length $< 2$.
    - Numerical instability: $\Delta t < 2Kx$ or $\Delta t > 2K(1-x)$.
  - `500 Internal Server Error`: Unhandled computational or execution failures.

- **Response Body (`TabletopScenarioResponse`):**
  - `scenario_id`: Unique identifier.
  - `reproducibility_hash`: Cryptographic SHA-256 fingerprint of inputs and parameters (`sha256:xxxxxxxxxxxx`).
  - `numerical_validity_status`: `"VALID"`.
  - `peak_inflow_discharge_cumecs`: Maximum input discharge.
  - `peak_simulated_outflow_discharge_cumecs`: Maximum routed discharge.
  - `peak_attenuation_cumecs` & `peak_attenuation_percent`: Quantified peak dampening.
  - `apparent_lag_hours` & `apparent_lag_steps`: Wave travel time between input and output peaks.
  - `mass_conservation_error_percent`: Continuity audit (typically $< 0.005\%$).
  - `time_series`: Point-by-point records with `observed_downstream_stage_m: null`.
  - `scientific_disclaimer`: Prominent safety notice.

---

## 3. Standard Tabletop Presets

| Preset ID | Scenario Name | Profile | Inflow Peak | Simulated Outflow Peak | Attenuation (%) | Transit Lag | Purpose / Invariant Verified |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| `PRESET_CONSTANT` | Constant Steady Inflow | Uniform $1,000\text{ m}^3/\text{s}$ for 7 days | $1,000\text{ m}^3/\text{s}$ | $1,000\text{ m}^3/\text{s}$ | $0.0\%$ | $0\text{ h}$ | **Steady-State Continuity:** Outflow equals inflow at all steps; error $< 10^{-4}\%$. |
| `PRESET_GRADUAL_RISE` | Gradually Rising Wave | Smooth rise $500 \to 4,500\text{ m}^3/\text{s}$ over 4 days, recession over 4 days | $4,500\text{ m}^3/\text{s}$ | $3,812.87\text{ m}^3/\text{s}$ | $15.27\%$ | $24\text{ h}$ | **Smooth Wave Propagation:** Moderate dispersion and wave delay typical of regional monsoon runoffs. |
| `PRESET_FLASH_PULSE` | Short-Duration Flash Pulse | Extreme 1-day spike to $6,500\text{ m}^3/\text{s}$ | $6,500\text{ m}^3/\text{s}$ | $4,258.12\text{ m}^3/\text{s}$ | $34.49\%$ | $24\text{ h}$ | **Dispersion Stress-Test:** Evaluates channel storage buffer under sharp pulses. |
| `PRESET_SUSTAINED_HIGH` | Sustained Elevated Plateau | Multi-day $4,000\text{–}4,200\text{ m}^3/\text{s}$ plateau | $4,200\text{ m}^3/\text{s}$ | $3,985.45\text{ m}^3/\text{s}$ | $5.11\%$ | $24\text{ h}$ | **Storage Saturation:** Prolonged high inflow exhausts reach storage, reducing % attenuation. |

---

## 4. Frontend Workstation Experience

The Tabletop Workstation is integrated directly into the cream-and-brown GIS workstation UI:
1. **Interactive Tab Navigation:** Toggle between the empirical *Historical Baseline* and the *Tabletop Simulation (Phase 2C-B)*.
2. **Real-Time Stability & Coefficient Feedback:** As $K$ or $x$ sliders move, computed $C_0, C_1, C_2$ and stability bounds ($2Kx \le \Delta t \le 2K(1-x)$) update dynamically.
3. **Preset Quick-Selector:** Instant loading of standard stress-test hydrographs or user custom sequences.
4. **Hydrograph Evolution Display:** Visual dual-bar comparison of Inflow vs Simulated Outflow across each time step.
5. **Scenario Comparison Mode:** Side-by-side evaluation of Baseline ($K=36\text{h}, x=0.20$) vs Alternative Heuristic ($K=48\text{h}, x=0.25$), visually demonstrating how travel time $K$ shifts the wave crest.
6. **Prominent Scientific Discipline Panel:** Constant visible reminder that outputs are simulated discharge, uncalibrated, and non-operational.
