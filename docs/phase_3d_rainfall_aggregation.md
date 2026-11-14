# Phase 3D.5 — Spatial Rainfall Aggregation & Antecedent Moisture Analysis

**Project**: PRAVAAH (Predictive Risk Assessment and Vulnerability Analysis for Adaptive Assistance & Humanitarian Response)  
**Scope**: Catchment-Wide Rainfall Aggregation & Antecedent Precipitation Index (API) Engine  
**Module**: `ml/spatial/rainfall.py` & `backend/app/services/rainfall_service.py`  
**Status**: OPERATIONAL & VERIFIED

---

## 1. Catchment-Scale Spatial Aggregation Engine

Given a set of $N$ valid spatial meteorological observation or forecast nodes within the delineated watershed boundary, PRAVAAH computes the spatial distribution statistics:

### Mathematical Formulations

1. **Catchment Mean Precipitation**:
   $$\bar{P} = \frac{1}{N} \sum_{i=1}^N P_i$$

2. **Spatial Variance & Standard Deviation**:
   $$\sigma_P = \sqrt{\frac{1}{N} \sum_{i=1}^N (P_i - \bar{P})^2}$$

3. **Spatial Extremes**:
   $$P_{\min} = \min_{i=1\dots N} P_i, \quad P_{\max} = \max_{i=1\dots N} P_i$$

4. **Spatial Coverage Percentage**:
   $$\text{Coverage \%} = \frac{N_{\text{valid}}}{N_{\text{total}}} \times 100\%$$

5. **Temporal Accumulations**:
   Multi-horizon forward rainfall totals across 24-hour, 72-hour, and 168-hour accumulation windows:
   $$A_{24\text{h}} = \frac{1}{N} \sum_{i=1}^N \sum_{h=1}^{24} P_{i, h}$$
   $$A_{72\text{h}} = \frac{1}{N} \sum_{i=1}^N \sum_{h=1}^{72} P_{i, h}$$
   $$A_{168\text{h}} = \frac{1}{N} \sum_{i=1}^N \sum_{h=1}^{168} P_{i, h}$$

---

## 2. Antecedent Precipitation Index (API) Methodology

Runoff generation in mountainous watersheds is highly non-linear and depends heavily on pre-existing soil moisture saturation. High rainfall on dry soil produces moderate runoff, whereas moderate rainfall on saturated soil triggers severe flash floods.

PRAVAAH implements the classic hydrological Antecedent Precipitation Index (Kohler & Linsley, 1951) with an exponential daily recession factor:

$$\text{API}_N = \sum_{i=1}^N k^i \cdot P_{t-i}$$

Where:
- $P_{t-i}$ is the daily precipitation depth accumulated $i$ days prior to the current time $t$.
- $k$ is the empirical recession/evapotranspiration decay factor, set to $k = 0.85$ (standard parameter for temperate Himalayan mountain catchments).
- $N$ is the antecedent history window length in days:
  - **API-3**: 3-day short-term topsoil saturation index.
  - **API-7**: 7-day intermediate sub-surface moisture index.
  - **API-14**: 14-day deep root zone and baseflow index.

### Mathematical Monotonicity Guarantee

Because $k^i > 0$ and $P_{t-i} \ge 0$, the index strictly satisfies:

$$\text{API}_3 \le \text{API}_7 \le \text{API}_{14}$$

This property is systematically verified in unit test `test_antecedent_precipitation_index_decay`.

---

## 3. Data Integrity & Leakage Prevention Guardrail

**CRITICAL POLICY**:
Although API-3, API-7, and API-14 provide valuable hydrological insights, they are **NOT** piped into the Phase 2B Random Forest discharge prediction model at this time.

Reasons:
1. Historical training data alignment: Adding these features to the ML feature vector would invalidate the 23-feature contract trained in Phase 2B.
2. Temporal leakage: Historical reanalysis gridded rainfall (IMD) has a 24–48 hour publication latency, making real-time ground observations unavailable at inference time unless NWP or satellite feeds are harmonized.
3. Feature engineering audit required before retraining (scheduled for Phase 4).

