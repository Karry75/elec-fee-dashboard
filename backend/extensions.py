# -*- coding: utf-8 -*-
"""Shared Flask extensions (SQLAlchemy + optional scheduler)."""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def get_scheduler():
    """Lazily import APScheduler to avoid hard dependency at import time."""
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        return BackgroundScheduler()
    except Exception as exc:  # pragma: no cover
        print("[warn] APScheduler unavailable: %s" % exc)
        return None
