# 🌊 PRAVAAH

### Predictive Risk Assessment & Adaptive Assistance for Hazards
> **Predictive Risk Assessment and Vulnerability Analysis for Adaptive Assistance & Humanitarian Response**

**Predict. Prepare. Protect.**

PRAVAAH is an AI-powered, geospatial disaster-intelligence and humanitarian decision-support platform designed to anticipate flood emergencies along the Upper-to-Middle Yamuna corridor (Hathnikund Barrage to Delhi Old Railway Bridge / Okhla), assess infrastructure vulnerability, coordinate safe evacuation corridors, and simulate hydrological stress scenarios.

---

## 🎯 Problem Statement

Rapid-onset hydrological events and severe inundations frequently overwhelm traditional emergency management mechanisms. Disaster responders, local authorities, and humanitarian agencies typically grapple with:

- **Fragmented data silos:** Inability to unify rainfall forecasts, stream gauges, and digital elevation models (DEM) into real-time hazard spatial grids.
- **Blind exposure estimation:** Static population summaries failing to reflect demographic vulnerability within dynamic inundation perimeters.
- **Impassable evacuation corridors:** Evacuation routes computed without continuous hazard feedback, routing vulnerable groups through flooded road segments.
- **Lack of counterfactual simulation:** Inability to test "what-if" operational contingencies (such as upstream barrage surges or embankment breaches) prior to emergency deployment.

PRAVAAH addresses these challenges through an integrated platform that transforms geographical, meteorological, and hydrological data into actionable intelligence for disaster preparedness and response.

---

## 💡 Key Features

### 🔴 High-Risk Area Identification
- Estimate upstream discharge and corridor flood risk using environmental, geographical, and historical telemetry.
- Visualize risk zones through an interactive full-screen GIS map (Leaflet + OpenStreetMap + Copernicus elevation contours).
- Identify vulnerable infrastructure and corridor monitoring stations from Hathnikund Barrage (Km 0.00) down to Delhi Old Railway Bridge (Km 251.05).

### 🟢 Lower-Risk Area Identification & Emergency Shelters
- Identify comparatively lower-risk zones for evacuation staging and temporary refuge.
- Map candidate relief shelters (e.g. DDMA relief centers) with verified coordinates, capacities, and emergency amenities.
- Clearly badge illustrative prototype datasets to prevent unauthorized deployment before official administrative accreditation.

### 🔄 What-If Disaster Simulation
- Interactive 5-step Muskingum tabletop scenario simulation.
- Simulate peak inflow surges (2,500 m³/s to historic 10,194 m³/s peaks) and evaluate downstream wave attenuation and travel lag times (~48 to 62 hours).
- Inspect physical hydrograph comparisons, mass conservation compliance, and numerical stability criteria ($2Kx < \Delta t \le 2K(1-x)$).

### 🗺️ Geospatial Decision Support
- D8 depression-conditioned watershed morphometry for the 11,112–11,365 km² Upper Yamuna catchment.
- Spatially distributed precipitation analysis across IMD 0.25° grid nodes and Open-Meteo live atmospheric forecasting.
- Designated evacuation corridors with elevation profiles and distance to mainstem river channel.

---

## ⚙️ How It Works

```text
Environmental & Geographical Data
 (IMD Gridded Rainfall, Copernicus GLO-30 DEM, Haryana I&WRD Discharge)
               ↓
      Data Ingestion & Validation
 (Leakage Prevention, Geodetic CRS Alignment, NoData Masking)
               ↓
       AI/ML Risk Assessment & Hydrology
 (Random Forest 24h Discharge Forecasting, Muskingum 1D Routing)
               ↓
      Geospatial Intelligence
 (Catchment Delineation, River Chainage, Evacuation Topology)
               ↓
      What-If Scenario Simulation
 (Inflow Surges, Attenuation Modeling, Lag Evaluation)
               ↓
     Interactive Decision Dashboard
 (5 Unified Workspaces: Overview, Flood Map, Simulation, Disaster, Terrain)
```

---

## 🛠️ Technology Stack

| Component | Technologies |
|---|---|
| **Frontend** | React 19, TypeScript, Vite, Tailwind CSS, Lucide React |
| **Interactive GIS & Mapping** | Leaflet, React-Leaflet, OpenStreetMap Carto |
| **Backend API** | Python 3.12+, FastAPI, Uvicorn, Pydantic v2, HTTPX |
| **Machine Learning & AI** | Scikit-learn (RandomForestRegressor), Joblib, NumPy, Pandas |
| **Geospatial & Hydrology** | GeoPandas, Shapely, PyProj, Rasterio, D8 Flow Routing |
| **Testing & Quality Assurance** | Pytest (87 backend tests, 144 ML tests, 100% pass rate) |

---

## 📂 Repository Structure

```
PRAVAAH/
├── backend/                      # FastAPI Python backend application
│   ├── app/
│   │   ├── api/routes/           # API endpoints (hydrology, forecasting, spatial, routing, disaster, weather)
│   │   ├── core/                 # App configuration & CORS settings
│   │   ├── integrations/         # Weather & rainfall live service adapters
│   │   ├── schemas/              # Pydantic request/response data contracts
│   │   └── services/             # Domain business logic & analytical services
│   ├── tests/                    # Automated backend API test suite (87 tests)
│   └── requirements.txt          # Python dependencies
├── frontend/                     # React + TypeScript + Vite single-page application
│   ├── src/
│   │   ├── components/
│   │   │   ├── layout/           # Header, Sidebar, AppLayout
│   │   │   ├── map/              # InteractiveGISMap, MapToolbar, GeospatialWorkspace
│   │   │   └── workspaces/       # Overview, FloodMap, Simulation, DisasterResponse, TerrainInsights
│   │   ├── services/             # Client API service connectors
│   │   ├── types/                # TypeScript interface definitions
│   │   └── pages/                # LandingPage, DashboardPage
│   ├── package.json              # Frontend npm dependencies
│   └── vercel.json               # SPA routing rewrite configuration for Vercel
├── ml/                           # Hydrological modeling & spatial processing engine
│   ├── data_processing/          # Historical discharge, IMD rainfall, and event extractors
│   ├── features/                 # Hydrometeorological feature engineering pipeline
│   ├── models/                   # Pre-trained Random Forest model artifact & metadata
│   ├── routing/                  # 1D Muskingum routing & spatial wave simulation
│   ├── spatial/                  # D8 watershed delineation, DEM acquisition, and hydrography
│   └── tests/                    # Automated ML & routing test suite (144 tests)
├── data/
│   ├── metadata/                 # Data dictionary & dataset inventories
│   └── processed/                # Production runtime datasets (GeoJSON, CSV, JSON ~3.5 MB)
├── docs/                         # Scientific validation reports & engineering architecture docs
├── .gitignore                    # Production deployment exclude rules
└── README.md                     # Project documentation
```

---

## 🚀 Prerequisites

Ensure the following tools are installed on your workstation:
- **Python:** 3.11 or higher (`python --version`)
- **Node.js:** 20.x or higher (`node --version`)
- **npm:** 10.x or higher (`npm --version`)
- **Git:** 2.x or higher (`git --version`)

---

## 💻 Installation & Execution Guide

### 1. Backend Setup

1. **Navigate to the backend directory and set up a virtual environment:**
   ```bash
   cd backend
   python -m venv .venv
   ```

2. **Activate the virtual environment:**
   - **Windows PowerShell:**
     ```powershell
     .venv\Scripts\Activate.ps1
     ```
   - **macOS / Linux:**
     ```bash
     source .venv/bin/activate
     ```

3. **Install dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Start the FastAPI backend server:**
   ```bash
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

   The backend will start at `http://127.0.0.1:8000`. Interactive documentation is available at `http://127.0.0.1:8000/api/docs`.

---

### 2. Frontend Setup

1. **Open a new terminal and navigate to the frontend directory:**
   ```bash
   cd frontend
   npm install
   ```

2. **Launch the development server:**
   ```bash
   npm run dev
   ```

   The application will be live at `http://localhost:5173`.

---

## ⚙️ Environment Configuration

### Backend Configuration (`backend/.env`)
| Variable | Default Value | Description |
|---|---|---|
| `PROJECT_NAME` | `"PRAVAAH API"` | Service identifier displayed across endpoints |
| `VERSION` | `"0.1.0"` | Current API semantic version |
| `ENVIRONMENT` | `"development"` | Active runtime environment |
| `API_V1_STR` | `"/api"` | Base API prefix for versioned endpoints |
| `ALLOWED_ORIGINS` | `"http://localhost:5173,http://127.0.0.1:5173"` | Whitelist for CORS requests |

### Frontend Configuration (`frontend/.env`)
| Variable | Default Value | Description |
|---|---|---|
| `VITE_API_BASE_URL` | `"http://127.0.0.1:8000"` | Base URL of the running FastAPI server |

---

## 🧪 Running Automated Tests

### Backend API Tests (87 tests)
```bash
python -m pytest backend/tests/ -v
```

### ML Pipeline & Hydrological Routing Tests (144 tests)
```bash
python -m pytest ml/tests/ -v
```

### Frontend Type Checking & Production Build
```bash
cd frontend
npm run build
```

---

## 🌍 Potential Applications

PRAVAAH is designed to support:
- **Disaster Management Authorities:** Central and state emergency operation centers (e.g. DDMA, SDMA, NDMA).
- **Hydrological Engineers:** Operational flood forecasting along the Yamuna river basin.
- **Evacuation & Relief Coordinators:** Identifying non-flooded egress routes and planning shelter distribution.
- **Municipal Infrastructure Planners:** Assessing flood barrier impacts and counterfactual surge scenarios.

---

## 🔮 Development Roadmap & Future Scope

- **Phase 0 (Completed):** Project Foundation, Development Environment, Modular API, and Dashboard Shell.
- **Phase 1 (Completed):** Historical Inundation & Discharge Ingestion (2018–2025 Haryana I&WRD).
- **Phase 2 (Completed):** Machine Learning Discharge Forecasting (Random Forest $R^2=0.81$, 466.2 m³/s 24h lead).
- **Phase 3 (Completed):** DEM Processing, Catchment Delineation (Copernicus GLO-30 30m), River Topology, and 1D Muskingum Routing.
- **Phase 4 (Completed):** UI/UX Unification into 5 Primary Workspaces and Production Deployment Hardening.
- **Future Scope:**
  - Multi-satellite SAR flood inundation extent integration (Sentinel-1 GRD).
  - High-resolution hydrodynamic 2D shallow-water inundation modeling (HEC-RAS / LISFLOOD-FP).
  - Multi-hazard cascading risk assessment (urban drainage backflow, bridge scour, embankment breaches).

---

## ⚠️ Responsible Use & Scientific Integrity

- **Decision Support Tool:** PRAVAAH is intended as an analytical decision-support and scenario evaluation platform. It does not replace statutory administrative emergency directives or official evacuation orders issued by authorized disaster management agencies.
- **Upstream vs Downstream Distinction:** Upstream discharge forecasts at Hathnikund Barrage represent volumetric flow rates ($m^3/s$) and do not directly equate to downstream stage elevations ($m\text{ MSL}$) at Delhi Old Railway Bridge.
- **Data Authenticity:** Prototype relief shelters and candidate evacuation corridors are explicitly marked as illustrative to uphold scientific integrity and public safety.
