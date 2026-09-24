# -*- coding: utf-8 -*-
"""Root sync entry point. Exits with [OK]/[WARN] -> 0, [ERR] -> 1.

Usage:
  python run_sync.py                # uses SYNC_SOURCE from config (.env)
  python run_sync.py excel         # force excel source
  python run_sync.py mysql         # force mysql source
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.sync.run_sync import run_sync

if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else None
    status, message, code = run_sync(src)
    print("[sync] %s %s" % (status, message))
    sys.exit(code)
