# PRAVAAH — Machine Learning Readiness Checklist

> **Milestone:** Phase 1D — Historical Data Completion and Final Dataset Assembly  
> **Prepared by:** Machine Learning Validation Group & Hydrological Data Engineering  
> **Date:** October 2026  
> **Evaluation Target:** Phase 2 Supervised Flood Hazard Classifier (24–48h Prediction Window)  

---

## 1. Readiness Dimension Checklist

| Dimension | Engineering Requirement | Status | Detailed Evidence / Current State |
| :--- | :--- | :--- | :--- |
| **1. Upstream Predictor Data** | Continuous historical discharge time-series with zero nulls for the primary upstream regulatory node. | **READY** | Hathnikund Barrage daily discharge (2018–2025, 5,192 records) verified in [`data/processed/hydrological/haryana_hathnikund_discharge_daily_2018_2025.csv`](file:///c:/Users/kirti%20antil/OneDrive/Desktop/PRAVAAH/data/processed/hydrological/haryana_hathnikund_discharge_daily_2018_2025.csv). 0 nulls, 0 duplicates. |
| **2. Downstream Target Observations** | Continuous daily/hourly water level time-series for reference cross-section across non-flood and flood periods. | **BLOCKED** | Delhi Old Railway Bridge (CWC Station 028-MDD) data for non-flood periods is restricted under CWC transboundary basin policies on open NWDP CKAN endpoints. Formal checklist prepared in [`docs/cwc_target_data_acquisition_checklist.md`](file:///c:/Users/kirti%20antil/OneDrive/Desktop/PRAVAAH/docs/cwc_target_data_acquisition_checklist.md). |
| **3. Ground-Truth Target Benchmark** | Authoritative, physically verifiable flood stage threshold tied to official disaster management benchmarks. | **READY** | CWC Danger Mark (**205.33 m MSL**) at Delhi ORB verified via CWC bulletins, DDMA operational advisories, and NWIC station registers. |
| **4. Meteorological Predictor Data** | Multi-year historical daily precipitation covering the contributing catchment. | **READY** | 7 full calendar years (**2018–2024, 2,557 days**) of official IMD Pune 0.25° gridded daily rainfall downloaded (178 MB) and extracted across provisional Upper Yamuna bounding box (91 cells, 232,687 cell records). Verified in [`data/processed/rainfall/gridded/`](file:///c:/Users/kirti%20antil/OneDrive/Desktop/PRAVAAH/data/processed/rainfall/gridded/). |
| **5. Temporal Alignment Engine** | Time-series pairing with forward prediction window and strict prevention of target leakage. | **READY** | Implemented in [`ml/data_processing/align_data.py`](file:///c:/Users/kirti%20antil/OneDrive/Desktop/PRAVAAH/ml/data_processing/align_data.py) and extended in [`ml/data_processing/assemble_dataset.py`](file:///c:/Users/kirti%20antil/OneDrive/Desktop/PRAVAAH/ml/data_processing/assemble_dataset.py); verified for 24–48h horizon and IMD 08:30 IST cut-off gating. |
| **6. Event Clustering & Completeness** | Automated detection of gaps and grouping of consecutive exceedance timestamps into distinct multi-day episodes. | **READY** | Implemented in [`ml/data_processing/event_analysis.py`](file:///c:/Users/kirti%20antil/OneDrive/Desktop/PRAVAAH/ml/data_processing/event_analysis.py); verified to group breaches separated by $\le 48\text{h}$ into single episodes. |
| **7. Non-ML Baseline Benchmarks** | Deterministic heuristics (Persistence, Recent-Trend, Lag Correlation) for performance floor comparisons. | **READY** | Implemented in [`ml/evaluation/baselines.py`](file:///c:/Users/kirti%20antil/OneDrive/Desktop/PRAVAAH/ml/evaluation/baselines.py); verified on synthetic test fixtures across 4 unit tests. |
| **8. Dataset Contract & Validator** | Formal schema enforcement verifying data types, value bounds, and target segregation before training. | **READY** | Implemented in [`ml/data_processing/schema_contract.py`](file:///c:/Users/kirti%20antil/OneDrive/Desktop/PRAVAAH/ml/data_processing/schema_contract.py); verified with 5 unit tests in [`ml/tests/test_schema_contract.py`](file:///c:/Users/kirti%20antil/OneDrive/Desktop/PRAVAAH/ml/tests/test_schema_contract.py). |
| **9. Chronological Split Protocol** | Time-based forward-chaining evaluation plan with purge buffers preventing temporal leakage. | **READY** | Protocol defined: Train (2018–2021), 48h Purge, Val (2022), 48h Purge, Test (2023–2024). Class imbalance metrics (PR-AUC, Brier score) specified. |
| **10. Code & Pipeline Testing** | Comprehensive automated test suite passing across all data processing and evaluation components. | **READY** | **31 passed in 0.56s** across `ml/tests`; **3 passed in 0.77s** across `backend/tests`. |

---

## 2. Summary Status & Decision Gate

* **Ready Dimensions:** 9 / 10
* **In Progress Dimensions:** 0 / 10
* **Blocked Dimensions:** 1 / 10 (Downstream continuous target stage register)

### Gate Verdict:
$$\mathbf{CONDITIONAL\; GO}$$

**Condition for Model Training Gate:**  
Training of machine learning models (Phase 2) remains strictly gated until **Dimension 2 (Downstream Target Observations)** is resolved via India-WRIS credentials or CWC archival register requisition as outlined in [`docs/cwc_target_data_acquisition_checklist.md`](file:///c:/Users/kirti%20antil/OneDrive/Desktop/PRAVAAH/docs/cwc_target_data_acquisition_checklist.md).

