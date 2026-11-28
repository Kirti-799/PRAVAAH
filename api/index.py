"""
api/index.py - Vercel Serverless Function entry point for PRAVAAH API Root
Mapped directly by Vercel file-system routing to /api
"""

import sys
import os
import json
from pathlib import Path
from http.server import BaseHTTPRequestHandler

# Resolve repository root and backend directory
_api_dir = Path(__file__).resolve().parent
_repo_root = _api_dir.parent
_backend_dir = _repo_root / "backend"
_cwd = Path.cwd()

for p in [str(_backend_dir), str(_repo_root), str(_cwd), str(_cwd / "backend")]:
    if p not in sys.path:
        sys.path.insert(0, p)

os.environ.setdefault("ENVIRONMENT", "production")

try:
    from app.main import app
except Exception:
    app = None


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

        payload = {
            "service": "PRAVAAH",
            "version": "0.1.0",
            "status": "ok",
            "message": "PRAVAAH Intelligent Flood Prediction & Disaster Response System API is operational.",
            "health_endpoint": "/api/health",
            "assessment_endpoint": "/api/assessment/areas",
        }
        self.wfile.write(json.dumps(payload).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()
