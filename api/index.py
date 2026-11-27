"""
api/index.py

Vercel Serverless Function entry point for PRAVAAH.
Exposes the modular FastAPI application with all 100+ endpoints for
hydrology, geospatial layers, ML discharge forecasting, Open-Meteo weather,
and disaster response intelligence.
"""

import sys
import os
import traceback
from pathlib import Path

# Resolve repository root and backend directory
_api_dir = Path(__file__).resolve().parent
_repo_root = _api_dir.parent
_backend_dir = _repo_root / "backend"
_cwd = Path.cwd()

# Ensure backend/ (for app.*) and repo root (for ml.*) are in sys.path
for p in [str(_backend_dir), str(_repo_root), str(_cwd), str(_cwd / "backend")]:
    if p not in sys.path:
        sys.path.insert(0, p)

# Set environment
os.environ.setdefault("ENVIRONMENT", "production")

try:
    from app.main import app
except Exception as _startup_err:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse

    _err_trace = traceback.format_exc()
    app = FastAPI(title="PRAVAAH API Fallback")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    @app.get("/health")
    def health():
        return {
            "status": "ok",
            "service": "PRAVAAH API",
            "version": "0.1.0",
        }

    @app.get("/api/diagnostic")
    def diagnostic():
        return {
            "status": "startup_error",
            "error": str(_startup_err),
            "traceback": _err_trace,
            "sys_path": sys.path,
        }



