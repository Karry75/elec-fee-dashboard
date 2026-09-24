# -*- coding: utf-8 -*-
"""Root entry point (Flask server). Port 8173, serves API + built SPA.

Usage:
  python serve.py                # production (serves frontend/dist if built)
  npm run dev                    # development (Vite dev server + proxy /api here)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from backend.app import create_app

app = create_app()


if __name__ == "__main__":
    print("[serve] elec-fee-dashboard on http://%s:%d  (sync_source=%s)" % (
        Config.HOST, Config.PORT, Config.SYNC_SOURCE))
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG, threaded=True)
