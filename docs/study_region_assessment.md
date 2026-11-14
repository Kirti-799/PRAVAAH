# PRAVAAH — Candidate Study Region Assessment

> **Milestone:** Phase 1A — Data Feasibility and Study Region Selection  
> **Author:** Data Engineering, Geospatial Analysis & ML Research Group  
> **Status:** Completed Assessment  
> **Date:** October 2026  

---

## 1. Executive Evaluation Framework

To establish a defensible supervised machine learning prototype for flood hazard prediction, the candidate study region must satisfy five fundamental criteria:

1. **Hydrological Controllability & Representativeness:** The hydrological domain must have clearly identifiable upstream controls, inflow sources, and physical boundaries rather than unbounded transboundary unmonitored catchments.
2. **Definitive Ground-Truth Flood Labels:** Objective, quantifiable flood thresholds (such as river stage danger levels tied to physical inundation) must exist with documented historical timestamps.
3. **High-Quality Synchronized Environmental Observations:** Daily or sub-daily river stage, upstream barrage/dam discharge, and gridded precipitation data must temporally overlap with historical flood occurrences.
4. **Data Acquisition Feasibility & Format Tractability:** Primary datasets must be accessible without non-disclosed proprietary licenses, multi-agency diplomatic barriers, or physical manual digitisation roadblocks.
5. **Spatial Scale Feasibility for Prototype Verification:** The spatial domain must be large enough to represent meaningful operational disaster intelligence, yet compact enough to prevent excessive computational overhead, severe cloud cover gaps in satellite validation, or extreme spatial heterogeneity.

Three candidate regions were evaluated under this framework:
* **Candidate A:** Mahanadi Basin, Odisha (Lower deltaic zone)
* **Candidate B:** Brahmaputra Basin, Assam (Middle valley reach)
* **Candidate C:** Yamuna Floodplain, Delhi-Haryana (Hathnikund to Okhla reach)

---

## 2. Comparative Evaluation Matrix

The availability and maturity of required datasets are categorized using strict status labels:
- **Confirmed:** Directly inspected official evidence or API/portal documentation confirms availability, resolution, and accessibility.
- **Partially confirmed:** Official evidence exists, but crucial operational details (e.g., historical archival depth, missing period frequency, or direct automated download access) remain unverified.
- **Unknown:** Insufficient evidence or unverified third-party claims.
- **Unavailable:** Official evidence confirms the required data cannot be obtained for the intended purpose under open/research terms.

| Assessment Dimension | Candidate A: Mahanadi Basin (Odisha) | Candidate B: Brahmaputra Basin (Assam) | Candidate C: Yamuna Floodplain (Delhi-Haryana) | Evidence & Source Documentation |
| :--- | :--- | :--- | :--- | :--- |
| **1. Historical Flood-Event Records** | **Partially confirmed** (Disaster summaries published by OSDMA at district level; lacks georeferenced flood perimeter time-series) | **Partially confirmed** (ASDMA Daily Situation Reports via DRIMS publish revenue-circle village counts; narrative PDF format) | **Confirmed** (Exact historical stage benchmarks at CWC Old Railway Bridge Delhi: Warning 204.50m, Danger 205.33m, Evacuation 206.00m; discrete events: 1978, 2010, 2013, 2019, 2023, 2025) | [CWC Delhi ORB Benchmark Records](https://ffm.cwc.gov.in/), [ASDMA Flood Reporting](https://asdma.assam.gov.in/), [OSDMA Disaster Data](https://www.osdma.org/) |
| **2. Historical Rainfall Data** | **Confirmed** (IMD 0.25° gridded daily rainfall covers the entire basin: 1901–2024) | **Confirmed** (IMD 0.25° gridded daily rainfall available, but severe rain-shadow and interpolation errors in adjacent Himalayan catchments) | **Confirmed** (IMD 0.25° gridded daily rainfall covers upper catchment in Himachal/Uttarakhand and NCR plains: 1901–2024) | [IMD Pune Gridded Data Portal](https://imdpune.gov.in/cmpg/Griddata/Rainfall_25_Bin.html) |
| **3. River Level & Discharge Observations** | **Partially confirmed** (CWC stations at Hirakud, Khairmal, Mundali available on NWDP, but regulated multi-tributary dam discharges create complex routing lags) | **Partially confirmed** (CWC stations at Dibrugarh, Tezpur, Guwahati; however, heavy gauge submergence and channel shifts cause missing records during peak floods) | **Confirmed** (Hourly/daily discharge from Hathnikund Barrage and continuous river gauge stages at Old Railway Bridge Delhi via CWC/NWDP) | [National Water Data Portal (NWIC)](https://nwdp.nwic.gov.in/), [India-WRIS](https://indiawris.gov.in/) |
| **4. Administrative & Basin Boundaries** | **Confirmed** (Survey of India / Odisha district and block boundaries available via Bhuvan / Survey of India) | **Confirmed** (Assam state, district, and revenue circle boundaries available via Bhuvan / Survey of India) | **Confirmed** (Delhi NCT revenue sub-divisions, ward boundaries, and Yamuna River floodplain demarcated by DDA/DDMA) | [Survey of India Geoportal](https://onlinemaps.surveyofindia.gov.in/), [Bhuvan ISRO](https://bhuvan.nrsc.gov.in/) |
| **5. Elevation & Topographic Data** | **Confirmed** (Copernicus DEM GLO-30 and NASA SRTM 30m; elevation changes from Eastern Ghats to coastal delta) | **Confirmed** (Copernicus DEM GLO-30 and NASA SRTM 30m; extreme gradient from Himalayas to Brahmaputra valley floor) | **Confirmed** (Copernicus DEM GLO-30 and NASA SRTM 30m; high topographic consistency across Delhi-NCR plain) | [Copernicus DEM GLO-30](https://spacedata.copernicus.eu/), [USGS LP DAAC SRTM](https://lpdaac.usgs.gov/products/srtmgl1v003/) |
| **6. Spatial Compatibility** | **Partially confirmed** (Large basin area ~141,589 km²; 0.25° rainfall resolution averages over heterogeneous hilly sub-catchments) | **Partially confirmed** (Valley width 10–20 km; complex braided bars; 0.25° rainfall coarse relative to steep tributary funnels) | **Confirmed** (Catchment area from Hathnikund to Delhi ~20,000 km²; upstream travel time of 48–50h directly couples upstream rainfall/barrage discharge to Delhi stage) | Hydro-meteorological travel time studies: [Delhi I&FC / CWC technical reports](https://ffm.cwc.gov.in/) |
| **7. Temporal Overlap of Key Data** | **Partially confirmed** (Hirakud operational releases and CWC telemetry overlap reliably from 2014 onward; older events lack automated telemetry) | **Partially confirmed** (ASDMA DRIMS active from 2014; tributary gauge data prior to 2015 has frequent telemetry dropouts) | **Confirmed** (Continuous hourly/daily hydrological overlap between Hathnikund discharge, CWC Delhi ORB gauge, and IMD rainfall from 2010 to 2024) | [NWDP Hydrological Archives](https://nwdp.nwic.gov.in/) |
| **8. Data Acquisition & Processing Burden** | **Moderate** (Requires integrating dam rule curves, multi-weir diversions, and estuarine tidal backwater effects at mouth) | **High** (Massive transboundary ungauged inflows from Tibet/China; dynamic riverbed shifting; heavy multi-tributary data pipelines) | **Low to Moderate** (Single primary upstream regulatory barrage, well-instrumented transit corridor, single focal downstream stage index) | CWC River Basin Reports (Yamuna vs Brahmaputra vs Mahanadi) |
| **9. Licensing & Usage Restrictions** | **Confirmed** (Government open data under NDSAP; non-commercial research access) | **Confirmed** (Government open data under NDSAP; non-commercial research access) | **Confirmed** (Government open data under NDSAP; non-commercial research access) | [National Data Sharing and Accessibility Policy](https://data.gov.in/) |
| **10. Suitability for Supervised ML Prototype** | **Conditional (Phase 2+)** | **Unsuitable for Phase 1 Prototype** | **Recommended (Phase 1 Prototype Target)** | Comparative Hydrological Complexity Analysis |

---

## 3. In-Depth Candidate Analysis

### Candidate A: Mahanadi Basin, Odisha (Lower Delta Reach)
* **Hydrological Dynamics:** The Mahanadi basin covers approximately 141,589 km² across Chhattisgarh and Odisha. While Hirakud Dam regulates upper catchment outflow, downstream uncontrolled tributaries (Tel, Ong, Suktel) enter below Hirakud and contribute massive unmonitored flash discharges into Mundali/Naraj barrage before distributing across the delta.
* **Flood Label Deficiencies:** While OSDMA maintains damage statistics, flood incidence is historically reported as aggregate administrative summaries (e.g., number of blocks affected, crop loss in hectares). Establishing a daily binary or ordinal ground-truth flood label for specific geospatial grid cells requires extensive hydraulic back-calculation.
* **Tidal Confounding:** The lower delta is vulnerable to estuarine backwater surges driven by Bay of Bengal cyclonic depressions, creating a multi-hazard confounder that cannot be isolated with pure precipitation-stage modeling in a Phase 1 prototype.
* **Suitability Verdict:** *Conditional for Phase 2.* Excellent case study once the core modeling architecture is proven, but too hydrodynamically complex for the initial prototype.

### Candidate B: Brahmaputra Basin, Assam
* **Hydrological Dynamics:** The Brahmaputra is one of the world's largest braided river systems, with channel widths exceeding 10–20 km in Assam. It is fed by over 50 major Himalayan and south-bank tributaries.
* **Transboundary Data Black Hole:** A critical percentage of the upper basin runoff originates in the Yarlung Tsangpo in Tibet (China) and ungauged high-altitude catchments in Arunachal Pradesh. Rainfall and streamflow data in these headwaters are either classified, sparse, or subject to significant geopolitical reporting delays.
* **Severe Braided Morphology:** The riverbed shifts continuously due to massive sediment transport, rendering static digital elevation models (DEM) inaccurate for cross-sectional hydraulic capacity within 1–2 monsoon seasons.
* **Suitability Verdict:** *Unsuitable for Phase 1 Prototype.* High risk of model failure due to unobserved upstream boundary inflows and dynamic channel bathymetry.

### Candidate C: Yamuna Floodplain, Delhi-Haryana (Recommended Study Region)
* **Hydrological Dynamics:** The sub-basin from Hathnikund Barrage (Yamunanagar, Haryana) through Sonipat/Panipat down to the Old Railway Bridge (ORB) and Okhla Barrage in Delhi covers an elongated river corridor (~220 km river stretch).
* **Clear Upstream-Downstream Hydrodynamic Coupling:** Water released from the Hathnikund Barrage follows a well-documented transit corridor with an established transit lag of **48 to 50 hours** to reach Delhi ORB. This physical hydrodynamic delay provides a natural, physically grounded 48-hour prediction horizon.
* **Unambiguous Ground-Truth Flood Benchmarks:** The CWC Old Railway Bridge station (Station Code: 028-MDD) has authoritative, non-fabricated physical stage benchmarks:
  - *Normal flow:* Below 204.50 m
  - *Warning Mark:* **204.50 m** (Alert issued to floodplain settlements)
  - *Danger Mark:* **205.33 m** (River overbanks into lower terraces)
  - *Evacuation Mark:* **206.00 m** (Active administrative relocation required)
  - *Historic Peak (July 13, 2023):* **208.66 m** (Catastrophic urban inundation of ITO, Red Fort area, and Yamuna Bazar)
* **High Data Harmonization:**
  - Upstream barrage release logs (in cusecs) recorded hourly/daily at Hathnikund.
  - River water level (stage in metres) recorded at Delhi ORB.
  - Precipitation monitored by IMD gridded daily rainfall covering the upper catchment (Yamuna basin in Himachal, Uttarakhand, and Haryana plains).
  - High-resolution static elevation from Copernicus DEM 30m with minimal canopy interference compared to tropical coastal forests.
* **Operational Value:** Delivers actionable disaster intelligence for one of India's most densely populated urban floodplains (National Capital Region).

---

## 4. Final Recommendation

**Recommended Region:** **Yamuna Floodplain Reach (Hathnikund Barrage to Delhi Old Railway Bridge / Okhla)**  
**Geographical Scope:** Upper-Middle Yamuna River Basin, encompassing Yamunanagar, Karnal, Panipat, Sonipat districts (Haryana) and the National Capital Territory (NCT) of Delhi.  
**Justification:** Candidate C presents the highest empirical data availability, unambiguous official benchmark labels, a physically grounded 48-hour hydrodynamic lag, and manageable spatial complexity, ensuring a reliable supervised learning pipeline without synthetic fabrication.
