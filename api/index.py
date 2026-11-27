"""
api/index.py

Vercel Serverless Function entry point for PRAVAAH FastAPI backend.
Bridges Vercel Python runtime with the existing modular FastAPI application.
"""

import sys
from pathlib import Path

# Resolve repository root and backend directory
_api_dir = Path(__file__).resolve().parent
_repo_root = _api_dir.parent
_backend_dir = _repo_root / "backend"

# Ensure both backend/ (for app.*) and repo root (for ml.*) are in sys.path
for p in [str(_backend_dir), str(_repo_root)]:
    if p not in sys.path:
        sys.path.insert(0, p)

# Expose existing FastAPI instance for Vercel ASGI handler
from app.main import app
