# -*- coding: utf-8 -*-
"""Runtime configuration for the Electricity Fee Management System.

All sensitive values are read from environment variables (see .env / .env.example).
The repository only ships config.example.py and .env.example — never real secrets.
"""
import os
from datetime import datetime

# ROOT = directory containing this file (project root)
ROOT = os.path.dirname(os.path.abspath(__file__))


def _abs(path, base=ROOT):
    """Resolve a possibly-relative path against the project root."""
    if not path:
        return path
    return path if os.path.isabs(path) else os.path.join(base, path)


def _bool(val, default=False):
    if val is None:
        return default
    return str(val).strip().lower() in ("1", "true", "yes", "y", "on")


def _int(val, default=0):
    try:
        return int(str(val).strip())
    except (TypeError, ValueError):
        return default


class Config:
    """Application configuration loaded from environment variables."""

    # ---- Core ----
    SECRET_KEY = os.getenv("SECRET_KEY", "elec-fee-dev-secret-change-me")
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = _int(os.getenv("PORT"), 8173)
    DEBUG = _bool(os.getenv("DEBUG"), False)

    # ---- Data dirs ----
    DATA_DIR = _abs(os.getenv("DATA_DIR", os.path.join("data")))
    DB_PATH = _abs(os.getenv("DB_PATH", os.path.join("data", "elec_fee.db")))
    UPLOAD_DIR = _abs(os.getenv("UPLOAD_DIR", os.path.join("data", "uploads")))
    SEED_DIR = _abs(os.getenv("SEED_DIR", os.path.join("data", "seed")))
    FRONTEND_DIST = _abs(
        os.getenv("FRONTEND_DIST", os.path.join("frontend", "dist"))
    )

    # ---- Sync ----
    # SYNC_SOURCE: "excel" (default, no DB credential needed) or "mysql"
    SYNC_SOURCE = os.getenv("SYNC_SOURCE", "excel")
    EXCEL_A_PATH = os.getenv(
        "EXCEL_A_PATH",
        r"C:\Users\Karry\Desktop\电费\电费结算登记表.xlsx",
    )
    EXCEL_B_PATH = os.getenv(
        "EXCEL_B_PATH",
        r"C:\Users\Karry\Desktop\电费\电费情况20260907.xlsx",
    )

    # ---- MySQL (read-only source, default OFF) ----
    MYSQL_HOST = os.getenv("MYSQL_HOST", "")
    MYSQL_PORT = _int(os.getenv("MYSQL_PORT"), 3306)
    MYSQL_USER = os.getenv("MYSQL_USER", "")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")  # placeholder, never commit
    MYSQL_DB = os.getenv("MYSQL_DB", "")
    MYSQL_TABLE = os.getenv("MYSQL_TABLE", "site_info_pro")

    # ---- Auth ----
    # Admin token gating for management APIs. If left empty, dev-mode opens the
    # endpoints but logs a warning (do NOT run like this in production).
    ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")
    SCAN_SECRET = os.getenv("SCAN_SECRET", SECRET_KEY)
    SCAN_TOKEN_TTL = _int(os.getenv("SCAN_TOKEN_TTL"), 86400)  # 24h in seconds
    BASE_URL = os.getenv("BASE_URL", "http://localhost:8173")

    # ---- Warn rules ----
    WARN_LEAD_DAYS = _int(os.getenv("WARN_LEAD_DAYS"), 7)
    CONTRACT_WARN_LEAD_DAYS = _int(os.getenv("CONTRACT_WARN_LEAD_DAYS"), 30)

    # ---- P2 integrations (config-gated) ----
    WECOM_WEBHOOK = os.getenv("WECOM_WEBHOOK", "")  # empty => skip push

    # ---- Scheduler (optional) ----
    SCHEDULE_SYNC = _bool(os.getenv("SCHEDULE_SYNC"), False)
    SCHEDULE_SYNC_HOUR = _int(os.getenv("SCHEDULE_SYNC_HOUR"), 8)

    @classmethod
    def ensure_dirs(cls):
        """Create data directories if missing."""
        for d in (cls.DATA_DIR, cls.UPLOAD_DIR, cls.SEED_DIR):
            try:
                os.makedirs(d, exist_ok=True)
            except OSError:
                pass

    @classmethod
    def summary(cls):
        return {
            "sync_source": cls.SYNC_SOURCE,
            "db_path": cls.DB_PATH,
            "excel_a": cls.EXCEL_A_PATH,
            "excel_b": cls.EXCEL_B_PATH,
            "warn_lead_days": cls.WARN_LEAD_DAYS,
            "admin_token_set": bool(cls.ADMIN_TOKEN),
            "wecom_set": bool(cls.WECOM_WEBHOOK),
            "schedule_sync": cls.SCHEDULE_SYNC,
            "now": datetime.now().isoformat(timespec="seconds"),
        }


# Load .env if present (python-dotenv)
try:
    from dotenv import load_dotenv

    load_dotenv(os.path.join(ROOT, ".env"))
    # Re-evaluate a few that may have changed after load_dotenv
    Config.SYNC_SOURCE = os.getenv("SYNC_SOURCE", Config.SYNC_SOURCE)
    Config.ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", Config.ADMIN_TOKEN)
    Config.WECOM_WEBHOOK = os.getenv("WECOM_WEBHOOK", Config.WECOM_WEBHOOK)
    Config.WARN_LEAD_DAYS = _int(os.getenv("WARN_LEAD_DAYS"), Config.WARN_LEAD_DAYS)
    Config.SCAN_TOKEN_TTL = _int(os.getenv("SCAN_TOKEN_TTL"), Config.SCAN_TOKEN_TTL)
    Config.SCHEDULE_SYNC = _bool(os.getenv("SCHEDULE_SYNC"), Config.SCHEDULE_SYNC)
except Exception:  # pragma: no cover - dotenv optional at import time
    pass
