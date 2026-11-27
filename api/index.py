"""
api/index.py

Vercel Serverless Function entry point for PRAVAAH FastAPI backend.
Bridges Vercel Python runtime with the existing modular FastAPI application.
"""

import sys
import os
import traceback
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Resolve repository root and backend directory
_api_dir = Path(__file__).resolve().parent
_repo_root = _api_dir.parent
_backend_dir = _repo_root / "backend"
_cwd = Path.cwd()

# Ensure backend/ (for app.*) and repo root (for ml.*) are in sys.path
for p in [str(_backend_dir), str(_repo_root), str(_cwd), str(_cwd / "backend")]:
    if p not in sys.path:
        sys.path.insert(0, p)

# Expose existing FastAPI instance for Vercel ASGI handler
try:
    from app.main import app
except Exception as e:
    _startup_err = traceback.format_exc()
    app = FastAPI(title="PRAVAAH Startup Diagnostic")

    @app.api_route("/{path_name:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    def diagnostic_fallback(path_name: str):
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "PRAVAAH backend failed to initialize on Vercel Python runtime.",
                "error": str(e),
                "traceback": _startup_err,
                "sys_path": sys.path,
                "cwd": str(Path.cwd()),
                "file": __file__,
                "repo_root_exists": _repo_root.exists(),
                "backend_dir_exists": _backend_dir.exists(),
                "repo_root_files": [f.name for f in _repo_root.iterdir()] if _repo_root.exists() else [],
            },
        )
