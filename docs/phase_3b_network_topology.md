# Phase 3B: River Network Topology & Station Chainage Specification

**Project:** PRAVAAH (Predictive Risk Assessment and Vulnerability Analysis for Adaptive Assistance & Humanitarian Response)  
**Milestone:** Phase 3B — River Hydrography & Network Integration  
**Implementation Modules:** `ml/spatial/hydrography.py`, `backend/app/services/spatial.py`, `backend/app/schemas/spatial.py`  

---

## 1. Topological Graph Formulation

To enable graph-based hydraulic routing, connectivity checks, and confluence identification, PRAVAAH represents the hydrographic reach network as a graph $G = (V, E)$ implemented via **NetworkX**:

- **Nodes ($V$):** Reach endpoints, confluence junctions, bifurcation points, and canal diversions. Coordinates are snapped within a configurable metric tolerance ($\Delta = 10\text{ m}$) to account for vertex digitization drift.
- **Edges ($E$):** Hydrographic reach segments connecting two nodes.
  - Attributes: `feature_id`, `name`, `waterway_class`, `length_m`, `length_km`, `flow_direction_verified` (`bool`), `provenance`.

---

## 2. Topological Diagnostics & Scientific Metrics

`HydrographyProcessor.build_network_topology()` calculates essential topological invariants:

### 2.1 Connected Components & Giant Component
- Identifies isolated waterways versus the contiguous river network.
- Computes the size of the **giant connected component** and its ratio relative to the total node population:
  $$\text{Giant Ratio} = \frac{|V_{\text{giant}}|}{|V_{\text{total}}|}$$
- High fragmentation indicates missing connecting reaches or data boundary clipping.

### 2.2 Node Degree & Confluence Classification
- **Confluence Junctions ($\text{deg}(v) \ge 3$):** Points where tributaries merge into the main channel (e.g., Hindon confluence) or where major diversions occur (Western and Eastern Yamuna Canals at Hathnikund).
- **Through-flow Nodes ($\text{deg}(v) = 2$):** Normal intermediate vertex connections between consecutive reaches.
- **Dead-end Terminals ($\text{deg}(v) = 1$):** River source origins, canal termini, or unmapped boundary cutoffs.

### 2.3 Braids & Closed Cycles
- Alluvial sandbed rivers frequently exhibit anabranching channels, island bars, and secondary flood channels.
- Cycle basis analysis (`nx.cycle_basis`) identifies closed loops and multichannel braids.

---

## 3. Flow Direction Guardrail

> [!WARNING]
> **CRITICAL SCIENTIFIC GUARDRAIL:** In standard OpenStreetMap and GIS shapefiles, polyline coordinate order represents the sequence in which the cartographer digitized the line, which may or may not match true hydraulic flow direction.
> PRAVAAH treats the reach network graph as **undirected** (`flow_direction_verified = False`). Flow direction is never assumed from vertex digitization order alone without hydraulic drop or hydrodynamic verification.

---

## 4. Downstream River Chainage (Stationing)

River chainage establishes a 1D curvilinear coordinate system measuring cumulative downstream distance (in kilometers) along the Yamuna thalweg from Hathnikund Barrage down to Delhi.

### 4.1 Calculation Methodology (`compute_river_chainage`)
1. **Thalweg Extraction:** Merges continuous `main_river` reaches into an authoritative thalweg line in `EPSG:32643` (UTM Zone 43N).
2. **Direction Alignment:** Verifies that index 0 corresponds to the northernmost upstream point (Hathnikund Barrage, Northing $\approx 3,355,000\text{ m}$). If inverted, coordinates are reversed so chainage accumulates strictly downstream.
3. **Cumulative Station Generation:** Computes metric chainage stations at regular intervals ($\Delta d = 5.0\text{ km}$) and tags key hydrological landmark reaches:
   - **KM 0.0:** Hathnikund Barrage (Upstream Inflow Origin)
   - **KM ~45.0:** Kalanaur Reach / Yamunanagar
   - **KM ~105.0:** Mawi Reach / Panipat
   - **KM ~175.0:** Wazirabad Barrage Entry
   - **KM ~205.0:** Delhi Old Railway Bridge (CWC Station 028-MDD)
   - **KM ~220.0:** Okhla Barrage / Terminal Corridor Reach

### 4.2 Disconnection Refusal Guardrail
If the main channel exhibits critical geometric breaks (`status == DISCONNECTED`), the chainage engine explicitly refuses to compute chainage (`status: "DISCONNECTED_REFUSED"`).
- Synthetic straight-line distances are **never** substituted for missing river segments.
- Limitations and exact gap locations are reported directly to the operator.
