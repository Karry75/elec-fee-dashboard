# -*- coding: utf-8 -*-
"""Value/date helpers shared across the sync and API layers."""
from datetime import date, datetime

# Tokens that mean "empty / not applicable" in the source data.
_EMPTY_TOKENS = {"", "-", "/", "无", "none", "null", "nan", "na", "未提供", "暂无"}


def is_empty(value):
    """Return True if a value should be treated as empty."""
    if value is None:
        return True
    if isinstance(value, float):
        import math
        return math.isnan(value)
    s = str(value).strip()
    return s.lower() in _EMPTY_TOKENS


def norm(value):
    """Normalize a value for comparison / display (empty -> None)."""
    if is_empty(value):
        return None
    s = str(value).replace("\t", "").replace("\r", "").replace("\n", " ").strip()
    return s if s else None


def to_float(value):
    """Best-effort float conversion. Returns None on failure."""
    if is_empty(value):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip()
    # strip trailing % and currency-ish chars
    for ch in ("%", "元", "￥", "¥", ",", " "):
        s = s.replace(ch, "")
    try:
        return float(s)
    except ValueError:
        return None


def parse_date(value):
    """Parse many date formats into ISO 'YYYY-MM-DD' string, else None.

    Handles: datetime/date, pandas Timestamp, 'YYYY-MM-DD', 'YYYY/MM/DD',
    'YYYYMMDD'. Returns None when unparseable.
    """
    if value is None or (isinstance(value, str) and is_empty(value)):
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    # pandas Timestamp
    if hasattr(value, "date") and callable(getattr(value, "date")):
        try:
            return value.date().isoformat()
        except Exception:
            pass
    s = str(value).strip()
    if is_empty(s):
        return None
    # try YYYYMMDD
    if s.isdigit() and len(s) == 8:
        try:
            return datetime.strptime(s, "%Y%m%d").date().isoformat()
        except ValueError:
            return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s[:19] if " " in s else s, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def days_between(iso_date, from_date=None):
    """Return (iso_date - from_date).days or None if unparseable."""
    if is_empty(iso_date):
        return None
    d = parse_date(iso_date)
    if d is None:
        return None
    base = from_date or date.today()
    return (datetime.strptime(d, "%Y-%m-%d").date() - base).days


def safe_get(row, key, default=None):
    """Case-insensitive get from a dict-like row."""
    if row is None:
        return default
    if key in row:
        return row[key]
    lk = key.lower()
    for k, v in row.items():
        if k is not None and str(k).lower() == lk:
            return v
    return default


def iso_now():
    return datetime.now().isoformat(timespec="seconds")
