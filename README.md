# PRAVAAH

> **Predictive Risk Assessment and Vulnerability Analysis for Adaptive Assistance & Humanitarian Response**

PRAVAAH is an AI-powered, geospatial disaster-intelligence and humanitarian decision-support platform designed to anticipate flood emergencies, gauge community vulnerability, coordinate safe evacuation corridors, and simulate hydrological stress scenarios.

---

## 1. Problem Statement

Rapid-onset hydrological events and severe inundations frequently overwhelm traditional emergency management mechanisms. Disaster responders, local authorities, and humanitarian agencies typically grapple with:

- **Fragmented data silos:** Inability to unify rainfall forecasts, stream gauges, and digital elevation models (DEM) into real-time hazard spatial grids.
- **Blind exposure estimation:** Static population summaries failing to reflect demographic vulnerability (e.g., elderly, non-ambulatory populations) within dynamic inundation perimeters.
- **Impassable evacuation corridors:** Evacuation routes computed without continuous hazard feedback, routing vulnerable groups through flooded road segments.
- **Lack of counterfactual simulation:** Inability to test "what-if" operational contingencies (such as dam overflow or embankment failure) prior to emergency deployment.

---

## 2. Planned Core Capabilities

PRAVAAH is structured across four primary technical modules scheduled for phased implementation:

1. **Flood Risk Prediction:** Geospatial hazard assessment incorporating meteorological precipitation forecasts, hydrological river gauges, and digital elevation models (DEM) to classify multi-zone flood vulnerability.
2. **Population Impact Assessment:** Spatial demographic exposure analysis intersecting administrative census boundaries with predicted hazard extent polygons to quantify affected persons and prioritize vulnerable clusters.
3. **Shelters & Evacuation Routes:** Graph-based network analysis identifying candidate safe-zone shelters and determining non-inundated, lowest-risk evacuation corridors.
4. **What-If Scenario Simulation:** Counterfactual modeling engine enabling emergency planners to adjust rainfall surges and flood barrier conditions to evaluate contingency plans.

---

## 3. Current Implementation Status — Phase 0

> **CURRENT STATUS: PHASE 0 (Project Foundation & Development Environment)**  
> Only the system foundation, modular package layout, API communication pipeline, health verification endpoints, and responsive dashboard shell are operational.

### Explicit Safety & Data Integrity Disclaimer
- **No Mock or Fabricated Predictions:** Phase 0 does **not** display synthetic risk percentages, arbitrary danger zones, or fabricated population counts.
- **No Unverified Safety Claims:** The application does **not** declare any geographical point safe or suitable for sheltering.
- **Future Integration Requirement:** All future analytical predictions and exposure computations must be derived from verified hydrological data pipelines and validated machine learning models.

---

## 4. Technology Stack

### Backend
- **Python:** 3.12+ (tested on Python 3.14)
- **FastAPI:** Modern asynchronous web framework for RESTful APIs
- **Uvicorn:** ASGI web server with reload capabilities
- **Pydantic v2 & Pydantic-Settings:** Robust schema definition, type safety, and environment validation
- **Pytest & HTTPX:** Automated test suite and asynchronous HTTP client for testing

### Frontend
- **React 19:** Modern component-based user interface architecture
- **TypeScript:** Strict type safety and maintainable contracts
- **Vite:** High-performance next-generation frontend build tooling
- **Tailwind CSS:** Professional utility-first styling system
- **Lucide React:** Standardized iconography for technical dashboards

### Future Stack Compatibility (Phase 1+)
- **Spatial & Data:** Pandas, GeoPandas, Shapely, PyProj, PostGIS
- **ML / AI:** Scikit-learn, PyTorch / LightGBM
- **Routing:** NetworkX, OSRM
- **Mapping:** MapLibre GL JS

---

## 5. Repository Structure

```
PRAVAAH/
├── frontend/                     # React + TypeScript + Vite application
│   ├── public/                   # Static public assets
│   ├── src/
│   │   ├── components/
│   │   │   ├── common/           # FeatureCard, SystemStatusPanel, WorkspacePanel
│   │   │   └── layout/           # Header, Sidebar, AppLayout
│   │   ├── hooks/                # useHealthCheck custom hook
│   │   ├── pages/                # DashboardPage
│   │   ├── services/             # api.ts (backend client & health check)
│   │   ├── types/                # api.ts (TypeScript interfaces)
│   │   ├── utils/                # formatters.ts
│   │   ├── App.tsx               # Main application container
│   │   ├── index.css             # Tailwind base styles and theme
│   │   └── main.tsx              # Application entrypoint
│   ├── .env.example              # Frontend environment variables template
│   ├── package.json              # Frontend dependencies and scripts
│   ├── tsconfig.json             # TypeScript configuration
│   └── vite.config.ts            # Vite configuration with Tailwind plugin
│
├── backend/                      # FastAPI Python application
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/           # Versioned API route handlers (health.py)
│   │   │   └── __init__.py
│   │   ├── core/                 # Settings and application configuration
│   │   ├── schemas/              # Pydantic validation models (health.py)
│   │   ├── services/             # Business logic modules (future phases)
│   │   ├── __init__.py
│   │   └── main.py               # FastAPI entrypoint, CORS & routing
│   ├── tests/                    # Automated test suite (test_health.py)
│   ├── .env.example              # Backend environment variables template
│   └── requirements.txt          # Python dependencies
│
├── ml/                           # Planned: Machine learning pipeline
│   ├── data_processing/
│   ├── feature_engineering/
│   ├── training/
│   ├── evaluation/
│   └── artifacts/
│
├── geospatial/                   # Planned: Geospatial processing & GIS pipelines
│   ├── risk_mapping/
│   ├── population_impact/
│   └── routing/
│
├── simulation/                   # Planned: What-If simulation engine
│
├── data/                         # Data storage (git-ignored raw/processed data)
│   ├── raw/
│   ├── processed/
│   └── metadata/
│
├── docs/                         # Project architecture and technical documentation
├── .gitignore                    # Git exclusions
├── .env.example                  # Root environment template
└── README.md                     # Project documentation
```

---

## 6. Prerequisites

Ensure the following tools are installed on your workstation:
- **Python:** 3.12 or higher (`python --version`)
- **Node.js:** 20.x or higher (`node --version`)
- **npm:** 10.x or higher (`npm --version`)
- **Git:** 2.x or higher (`git --version`)

---

## 7. Installation & Execution Guide

### Backend Setup

1. **Navigate to the backend directory and set up a virtual environment:**
   ```powershell
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
   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   ```powershell
   Copy-Item .env.example .env
   ```

5. **Start the FastAPI backend server:**
   ```powershell
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

   The backend will start at `http://127.0.0.1:8000`.

---

### Frontend Setup

1. **Open a new terminal, navigate to the frontend directory:**
   ```powershell
   cd frontend
   ```

2. **Install npm dependencies:**
   ```powershell
   npm install
   ```

3. **Configure environment:**
   ```powershell
   Copy-Item .env.example .env
   ```

4. **Launch the development server:**
   ```powershell
   npm run dev
   ```

   The frontend will be available at `http://localhost:5173`.

---

## 8. Environment Variable Configuration

### Backend (`backend/.env`)
| Variable | Default Value | Description |
|---|---|---|
| `PROJECT_NAME` | `"PRAVAAH API"` | Service identifier displayed across endpoints |
| `VERSION` | `"0.1.0"` | Current API semantic version |
| `ENVIRONMENT` | `"development"` | Active runtime environment |
| `API_V1_STR` | `"/api"` | Base API prefix for versioned endpoints |
| `ALLOWED_ORIGINS` | `"http://localhost:5173,http://127.0.0.1:5173"` | Whitelist for CORS requests |

### Frontend (`frontend/.env`)
| Variable | Default Value | Description |
|---|---|---|
| `VITE_API_BASE_URL` | `"http://localhost:8000"` | Base URL of the running FastAPI server |

---

## 9. Running Automated Tests

### Backend Tests
Execute pytest from the `backend/` directory with the virtual environment activated:
```powershell
cd backend
.venv\Scripts\pytest -v tests
```

Or from the repository root:
```powershell
backend\.venv\Scripts\pytest -v backend\tests -o pythonpath=backend
```

### Frontend Type Checking and Build Verification
Verify TypeScript contracts and generate a production bundle:
```powershell
cd frontend
npm run build
```

---

## 10. API Endpoints & Documentation

When the backend server is running (`http://127.0.0.1:8000`):

- **Interactive Swagger UI:** [http://127.0.0.1:8000/api/docs](http://127.0.0.1:8000/api/docs)
- **ReDoc Documentation:** [http://127.0.0.1:8000/api/redoc](http://127.0.0.1:8000/api/redoc)
- **OpenAPI Schema:** [http://127.0.0.1:8000/api/openapi.json](http://127.0.0.1:8000/api/openapi.json)
- **Root Identification:** `GET http://127.0.0.1:8000/`
  ```json
  {
    "service": "PRAVAAH API",
    "version": "0.1.0",
    "environment": "development",
    "message": "PRAVAAH API is operational. See documentation at /api/docs.",
    "docs_url": "/api/docs",
    "health_url": "/api/health"
  }
  ```
- **Health Verification:** `GET http://127.0.0.1:8000/api/health`
  ```json
  {
    "status": "ok",
    "service": "PRAVAAH API",
    "version": "0.1.0"
  }
  ```

---

## 11. Common Troubleshooting

1. **Frontend indicates "Backend Disconnected":**
   - Ensure the FastAPI server is running on port 8000 (`uvicorn app.main:app --host 127.0.0.1 --port 8000`).
   - Check that `VITE_API_BASE_URL` in `frontend/.env` matches the backend address (`http://localhost:8000`).
   - Verify CORS origins in `backend/.env` permit `http://localhost:5173`.
   - Click the "Retry Health Check" button on the dashboard.

2. **PowerShell execution policy blocks `.venv\Scripts\Activate.ps1`:**
   - Run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`
   - Or run python directly: `.venv\Scripts\python.exe -m uvicorn app.main:app --reload`

3. **Port 8000 or 5173 already in use:**
   - Terminate existing processes on the port or adjust the port argument in the launch command and update `.env`.

---

## 12. Planned Development Phases

- **Phase 0 (Completed):** Project Foundation, Development Environment, Health Verification API, Dashboard Shell.
- **Phase 1:** Inundation Data Ingestion & ML Flood-Risk Prediction Models.
- **Phase 2:** Geospatial Population Impact & Demographic Vulnerability Mapping.
- **Phase 3:** Evacuation Graph Network & Safe Shelter Optimization.
- **Phase 4:** What-If Disaster Scenario Simulation Engine.
- **Phase 5:** End-to-End Decision Support & Production Hardening.
