# Central Water Commission (CWC) Target Data Acquisition Checklist
## Historical Water-Level Series for Delhi Old Railway Bridge (Station 028-MDD)

> **Document ID:** `PRAVAAH-DOC-CWC-001`  
> **Milestone:** Phase 1D — Historical Data Completion and Final Dataset Assembly  
> **Target Gauge:** Yamuna River at Delhi Old Railway Bridge (ORB)  
> **CWC Site Identifier:** `028-MDD` (India-WRIS / WIMS ID: `CW1YAU000346`)  
> **Hydrological Basin:** Ganga Basin (Basin Code `002`) / Yamuna Sub-basin  
> **Administrative Jurisdiction:** Yamuna Basin Organisation (YBO), Central Water Commission  
> **Status:** **ACTIVE BLOCKER — FORMAL REQUISITION CHECKLIST**  

---

## 1. Executive Context & Objective

The objective of Project PRAVAAH's primary machine learning target is:
$$\hat{y}(t) = P\left( \max_{\tau \in [t+24\text{h}, t+48\text{h}]} \text{Stage}_{\text{ORB}}(\tau) \ge 205.33\,\text{m MSL} \;\middle|\; \mathcal{F}_t \right)$$

While upstream hydrological predictor data for Hathnikund Barrage (`2018-01-01` to `2025-08-12`, 5,192 records) and catchment meteorological data (IMD 0.25° gridded daily rainfall `2018–2024`) are available, continuous downstream target observations for non-flood periods remain omitted from unauthenticated open CKAN bulk CSV downloads on NWDP under transboundary classification guidelines.

Isolated peak readings reported in historical flood bulletins (e.g. July 2023 peak of 208.66 m MSL, August 2019 peak of 206.60 m MSL) prove that flood events occurred, but **they cannot train or validate a machine-learning classification model because non-flood periods (negative classes) are unobserved**.

This checklist provides the exact technical specifications, data schemas, institutional routes, and administrative procedures required to acquire continuous target stage observations from authorized sources without circumventing security or fabricating records.

---

## 2. Technical Specification of Required Target Dataset

To build a scientifically defensible training dataset adhering to `ml/data_processing/schema_contract.py`, the target export must satisfy the following technical parameters:

| Parameter | Specification | Engineering Rationale |
| :--- | :--- | :--- |
| **Station Name** | Delhi Old Railway Bridge (ORB) / Yamuna Bridge Delhi | Standard CWC reference cross-section for NCT Delhi flood risk management. |
| **Station Code** | `028-MDD` (CWC) / `CW1YAU000346` (WIMS) | Uniquely identifies the gauge within national registers. |
| **Geographic Coordinates** | Latitude $28.6625^\circ\text{N}$, Longitude $77.2489^\circ\text{E}$ | WGS84 coordinates of the Old Railway Bridge gauge post. |
| **Target Variable** | River Water Level / Stage Elevation | Primary physical state variable indicating flooding risk. |
| **Vertical Datum** | Mean Sea Level (MSL / GTS Datum) | Indian national Great Trigonometrical Survey datum. Stage values are absolute elevations in metres above MSL. |
| **Required Period** | **2018-01-01 00:00 UTC to 2024-12-31 23:59 UTC** (7 full calendar years) | Synchronizes with Hathnikund discharge archive (2018–2025) and IMD gridded rainfall (2018–2024). |
| **Observation Frequency** | **Hourly** during monsoon season (June 1 to October 31); **Daily** (08:00 IST / 08:30 IST) or hourly during dry season | Hourly resolution during monsoon captures diurnal peak crests that could recede between fixed daily morning readings. |
| **Measurement Unit** | Metres ($\text{m}$) | Standard CWC stage metric. Must not be converted without explicit verification of source units. |
| **Threshold Benchmarks** | Warning Mark: **204.50 m MSL**<br>Danger Mark: **205.33 m MSL**<br>Evacuation / High Risk: **206.00 m MSL**<br>Historic Highest Flood Level (HFL): **208.66 m MSL** (recorded 13 July 2023) | Fixed reference levels established by CWC and Delhi Disaster Management Authority (DDMA). |
| **Missing Value Sentinels** | Empty string `""`, `NaN`, `null`, `-999.0`, `-9999.0` | Missing values must be flagged as unobserved (`is_target_observed = False`); must **never** be interpreted as zero or non-flood. |
| **Export Format** | Tabular CSV or XLSX with explicit header row | Machine-readable for programmatic ingestion via `ml/data_processing/import_target_gauge.py`. |

---

## 3. Authorised Acquisition Routes

The project team must execute one or more of the following official channels to obtain the continuous stage register:

```
                          Downstream Target Data Requisition Routes
                                             │
      ┌──────────────────────────────────────┼──────────────────────────────────────┐
      │                                      │                                      │
      ▼                                      ▼                                      ▼
[Route 1: India-WRIS / NWIC]      [Route 2: CWC Archival Request]         [Route 3: Delhi I&FC Dept]
• Register research account       • Official departmental letter          • State nodal department
• Submit API credential request   • To: Chief Engineer, YBO, CWC         • Daily gauge register copy
• Filter Site 028-MDD             • Sewa Bhawan, R.K. Puram               • Inter-agency flood room
```

### Route 1: India-WRIS / National Water Informatics Centre (NWIC) Portal
* **Portal URL:** `https://indiawris.gov.in/` and `https://nwdp.nwic.gov.in/`
* **Authority:** National Water Informatics Centre (NWIC), Department of Water Resources, RD & GR, Ministry of Jal Shakti.
* **Procedure:**
  1. Register an institutional research account at `https://indiawris.gov.in/wris/#/register`.
  2. Verify identity using institutional email credentials.
  3. Log in to the India-WRIS Data Download portal (`https://indiawris.gov.in/wris/#/DataDownload`).
  4. Select **Telemetry Data** $\rightarrow$ **Surface Water Level**.
  5. State: **Delhi**, Basin: **Ganga**, Sub-basin: **Yamuna Lower / Middle**, Station Name: **Delhi (Old Rly. Bridge)** (`028-MDD`).
  6. Select date range: `2018-01-01` to `2024-12-31`.
  7. If unauthenticated direct download displays "Data Restricted under Transboundary Basin Guidelines", submit a formal **Data Requisition Form** directly via the portal's **Request Custom Data** workflow citing research/public disaster decision-support usage.

### Route 2: Formal Departmental Requisition to CWC Yamuna Basin Organisation
* **Authority:** Chief Engineer, Yamuna Basin Organisation (YBO), Central Water Commission.
* **Address:** Central Water Commission, Sewa Bhawan, R.K. Puram, New Delhi – 110066.
* **Contact Entity:** Director, Hydrological Data Directorate / Monitoring & Appraisal Directorate, CWC.
* **Procedure:**
  1. Draft a formal letter of requisition on institutional letterhead addressed to the Chief Engineer, YBO.
  2. Reference: *Request for Historical Continuous River Stage Telemetry Records for Station 028-MDD (Yamuna at Delhi Old Railway Bridge) for Flood Modelling and Disaster Risk Reduction Research (2018–2024)*.
  3. Detail the exact requirement: Hourly and daily water level observations in metres above MSL from 01-Jan-2018 to 31-Dec-2024.
  4. Attach non-disclosure and research-only usage undertaking under the National Data Sharing and Accessibility Policy (NDSAP).
  5. Await official electronic transfer or secure repository dispatch.

### Route 3: Requisition via Delhi Irrigation & Flood Control Department (I&FC)
* **Authority:** Irrigation & Flood Control Department, Government of NCT of Delhi.
* **Address:** Office of the Chief Engineer (I&FC), L.M. Bund Office Complex, Shastri Nagar, Delhi – 110031.
* **Procedure:**
  1. The Delhi I&FC Department operates the Delhi Central Flood Control Room during monsoon periods and maintains physical gauge logs recorded every hour during alert phases at Old Railway Bridge.
  2. Submit a formal application to the Superintending Engineer / Nodal Officer, Flood Control Room.
  3. Request digitized copies of the **Daily Flood Situation Reports and Gauge Registers** for the Yamuna River at Old Railway Bridge covering the flood seasons (June–October) of 2018 through 2024.

### Route 4: Right to Information (RTI) Act Requisition (Contingency)
* **Authority:** Central Public Information Officer (CPIO), Central Water Commission.
* **Procedure:**
  - In the event of administrative delay via academic channels, file an online RTI request at `https://rtionline.gov.in/`.
  - Public Authority: *Ministry of Jal Shakti, Department of Water Resources $\rightarrow$ Central Water Commission*.
  - Subject: Historical daily and hourly water level observations of CWC Station 028-MDD (Delhi Old Railway Bridge) for 2018–2024 in machine-readable electronic format (CSV/Excel).

---

## 4. Input File Schema Contract for Downstream Gauge Data

When the downstream target data export is acquired, it must be saved unmodified to:
`data/raw/hydrological/cwc_delhi_orb_water_level_historical.csv`

The dedicated target importer (`ml/data_processing/import_target_gauge.py`) enforces the following tabular schema:

```csv
timestamp_utc,station_id,station_name,water_level_m,warning_level_m,danger_level_m,agency,quality_flag
2018-07-28T08:00:00Z,028-MDD,Delhi Old Railway Bridge,205.44,204.50,205.33,CWC,VERIFIED
2018-07-28T09:00:00Z,028-MDD,Delhi Old Railway Bridge,205.52,204.50,205.33,CWC,VERIFIED
```

### Ingestion Validation Invariants:
1. **Timestamp Parsing:** All timestamps must parse to UTC ISO 8601 strings (`YYYY-MM-DDTHH:MM:SSZ`).
2. **Duplicate Detection:** Zero duplicate timestamps are permitted. If duplicates exist in source exports, they must be resolved or reported as schema errors.
3. **Unit Validation:** Water levels must fall within physically plausible stage limits ($195.0\text{ m} \le \text{Stage} \le 215.0\text{ m MSL}$).
4. **Missing Values Preserved:** Unrecorded timestamps must register `None` (empty) in processed tables; they must **never** be filled with zero ($0.0\text{ m}$) or forward-filled across day boundaries.

---

## 5. Execution Tracking Matrix

| Step | Action Item | Responsible Role | Status | Evidence / Artifact |
| :---: | :--- | :--- | :---: | :--- |
| **1** | Define CWC target gauge technical specifications and schema | Senior Data Engineer | **COMPLETED** | `docs/cwc_target_data_acquisition_checklist.md` |
| **2** | Implement reusable validation importer for CWC gauge exports | ML Pipeline Developer | **COMPLETED** | `ml/data_processing/import_target_gauge.py` |
| **3** | Implement automated unit test suite using synthetic fixtures | Validation Engineer | **COMPLETED** | `ml/tests/test_target_importer.py` |
| **4** | Submit Route 1 (India-WRIS / NWIC) credentialed request | Project Lead | PENDING USER | Registration portal application |
| **5** | Submit Route 2 (CWC YBO Sewa Bhawan) formal requisition | Project Lead | PENDING USER | Official letter submission |
| **6** | Ingest verified export into production repository | Senior Data Engineer | BLOCKED | Awaiting authorized export file |
| **7** | Execute end-to-end dataset assembly with real target ground truth | ML Pipeline Developer | BLOCKED | `ml/data_processing/assemble_dataset.py` |

---

## 6. Strict Prohibition Warning

> [!CAUTION]
> 1. **Do not fabricate downstream gauge observations.** Under no circumstances should synthetic or random stage values be placed in `data/raw/` or `data/processed/` production paths.
> 2. **Do not treat unobserved periods as non-flood classes.** An unobserved day is strictly unobserved (`is_target_observed = False`); converting it to `0` introduces lethal false-negative bias into predictive models.
> 3. **Model training (Phase 2) remains gated** until this checklist is fulfilled with authentic historical observations for Station `028-MDD`.
