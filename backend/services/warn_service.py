# -*- coding: utf-8 -*-
"""Warn classification helpers for the electricity board (module 2)."""
from datetime import date

from backend.util.helpers import days_between, norm


def classify(station, lead_days=7):
    """Return warn metadata dict for a station dict/row."""
    need = norm(station.get("need_settle")) == "是"
    settled = norm(station.get("is_settled")) == "是"
    days = days_between(station.get("next_settle_date"), date.today())
    warn_flag = "否"
    warn_level = 0
    days_left = days
    if need and not settled and days is not None and days <= lead_days:
        warn_flag = "是"
        warn_level = 1 if days <= 0 else (2 if days <= 3 else 3)
    return {
        "warn_flag": warn_flag,
        "warn_level": warn_level,
        "days_left": days_left,
    }


def top_warns(stations, lead_days=7, limit=50):
    """Return stations currently in warn, sorted by urgency."""
    out = []
    for s in stations:
        c = classify(s, lead_days)
        if c["warn_flag"] == "是":
            item = dict(s)
            item.update(c)
            out.append(item)
    out.sort(key=lambda x: (x["warn_level"], x["days_left"] if x["days_left"] is not None else 999))
    return out[:limit]
