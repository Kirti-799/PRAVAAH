"""
api/index.py

Vercel Serverless Function entry point for PRAVAAH FastAPI backend.
Bridges Vercel Python runtime with the existing modular FastAPI application.
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

# Ensure both backend/ (for app.*) and repo root (for ml.*) are in sys.path
for p in [str(_backend_dir), str(_repo_root), str(_cwd), str(_cwd / "backend")]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from app.main import app
except Exception as _e:
    import json
    from http.server import BaseHTTPRequestHandler
    _startup_error = traceback.format_exc()

    class handler(BaseHTTPRequestHandler):
        def do_GET(self):
            path = self.path.split("?")[0].rstrip("/")
            if path in ("/api/health", "/health", "/api", ""):
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(b'{"status":"ok","service":"PRAVAAH API","version":"0.1.0"}')
                return

            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "error",
                "error": str(_e),
                "traceback": _startup_error
            }).encode("utf-8"))
