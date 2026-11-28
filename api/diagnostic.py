"""
api/diagnostic.py - Direct Vercel Serverless Function for Diagnostic Checks

Mapped directly by Vercel file-system routing to /api/diagnostic.
"""

import json
import sys
import os
import traceback
from pathlib import Path
from http.server import BaseHTTPRequestHandler

# Set paths
_repo_root = Path(__file__).resolve().parent.parent
_backend_dir = _repo_root / "backend"
_cwd = Path.cwd()

for p in [str(_backend_dir), str(_repo_root), str(_cwd), str(_cwd / "backend")]:
    if p not in sys.path:
        sys.path.insert(0, p)

os.environ.setdefault("ENVIRONMENT", "production")

_app_import_status = "untested"
_app_import_error = None
try:
    from app.main import app
    _app_import_status = "success"
except Exception as e:
    _app_import_status = "failed"
    _app_import_error = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

        task_files = []
        try:
            task_files = os.listdir("/var/task")
        except Exception as e:
            task_files = [str(e)]

        payload = {
            "status": "operational",
            "python_version": sys.version,
            "environment": os.environ.get("ENVIRONMENT", "production"),
            "sys_path": sys.path[:5],
            "app_import_status": _app_import_status,
            "app_import_error": _app_import_error,
            "task_files": task_files,
        }
        self.wfile.write(json.dumps(payload, indent=2).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()
