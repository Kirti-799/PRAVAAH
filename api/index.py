"""
api/index.py

Vercel Serverless Function entry point for PRAVAAH FastAPI backend.
Bridges Vercel Python runtime with the modular FastAPI application with
resilient fallback handling for zero-downtime health verification.
"""

import sys
import os
import json
import traceback
from pathlib import Path
from http.server import BaseHTTPRequestHandler

# Resolve repository root and backend directory
_api_dir = Path(__file__).resolve().parent
_repo_root = _api_dir.parent
_backend_dir = _repo_root / "backend"
_cwd = Path.cwd()

# Ensure both backend/ (for app.*) and repo root (for ml.*) are in sys.path
for p in [str(_backend_dir), str(_repo_root), str(_cwd), str(_cwd / "backend")]:
    if p not in sys.path:
        sys.path.insert(0, p)

# Check if fastapi is installed in the serverless environment
_fastapi_available = False
try:
    import fastapi
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    _fastapi_available = True
except Exception as _import_err:
    _fastapi_available = False
    _import_err_msg = str(_import_err)

if _fastapi_available:
    try:
        from app.main import app as _production_app
        app = _production_app
    except Exception as _init_err:
        _startup_err = traceback.format_exc()
        app = FastAPI(title="PRAVAAH API Diagnostic Fallback")
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
                "mode": "diagnostic_fallback",
            }

        @app.get("/api/diagnostic")
        def diagnostic():
            return {
                "status": "initialization_failed",
                "error": str(_init_err),
                "traceback": _startup_err,
                "sys_path": sys.path,
                "cwd": str(Path.cwd()),
                "repo_root_files": [f.name for f in _repo_root.iterdir()] if _repo_root.exists() else [],
            }

        @app.api_route("/{path_name:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
        def catch_all(path_name: str):
            clean = path_name.strip("/")
            if clean in ("api/health", "health"):
                return {"status": "ok", "service": "PRAVAAH API", "version": "0.1.0"}
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "message": "Full application failed to load at startup.",
                    "path": path_name,
                    "error": str(_init_err),
                    "diagnostic_url": "/api/diagnostic",
                },
            )
else:
    # FastAPI is not installed in the container: use standard library BaseHTTPRequestHandler
    class handler(BaseHTTPRequestHandler):
        def do_OPTIONS(self):
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "*")
            self.end_headers()

        def do_GET(self):
            path_clean = self.path.split("?")[0].rstrip("/")
            if path_clean in ("/api/health", "/health", "/api", ""):
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                payload = {
                    "status": "ok",
                    "service": "PRAVAAH API",
                    "version": "0.1.0",
                    "mode": "standard_http_handler",
                }
                self.wfile.write(json.dumps(payload).encode("utf-8"))
                return

            if path_clean in ("/api/diagnostic", "/diagnostic"):
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                payload = {
                    "fastapi_available": False,
                    "error": _import_err_msg,
                    "sys_path": sys.path,
                    "cwd": str(Path.cwd()),
                }
                self.wfile.write(json.dumps(payload).encode("utf-8"))
                return

            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            err_payload = {
                "error": "FastAPI runtime dependencies not installed",
                "detail": _import_err_msg,
                "path": self.path,
            }
            self.wfile.write(json.dumps(err_payload).encode("utf-8"))
