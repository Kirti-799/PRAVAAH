"""
api/diagnostic.py - Direct Vercel Serverless Function for Diagnostic Checks
Mapped directly by Vercel file-system routing to /api/diagnostic.
"""

import json
import sys
import os
from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

        payload = {
            "status": "operational",
            "version": "0.1.0-audit-verified",
            "python_version": sys.version,
            "environment": os.environ.get("ENVIRONMENT", "production"),
            "sys_path": sys.path[:5],
        }
        self.wfile.write(json.dumps(payload, indent=2).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()
