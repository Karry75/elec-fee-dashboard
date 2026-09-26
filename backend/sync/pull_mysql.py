# -*- coding: utf-8 -*-
"""Pull master rows from mysql-dudu (read-only). Config-gated.

When SYNC_SOURCE != "mysql" or credentials are missing this returns an empty
list and logs a skip — the Excel fallback is the default path. The SQL columns
are expected to match the file-B Chinese headers (B_MAP), so the same mapping
is reused.
"""
from config import Config
from backend.sync.import_excel import B_MAP
from backend.util.helpers import is_empty, norm, parse_date, to_float
from backend.sync.import_excel import to_site_id


def _convert(field, value):
    if field in {
        "cabinet_count", "elec_price", "service_price", "share_ratio",
        "annual_site_fee", "deposit", "last_meter_reading",
        "total_amount", "settle_amount",
    }:
        return to_float(value)
    if field in {"last_read_date", "next_settle_date", "cooperate_time"}:
        return parse_date(value)
    return norm(value)


def pull_mysql():
    """Return list of canonical dicts from the MySQL master table, or []."""
    if Config.SYNC_SOURCE != "mysql":
        print("[sync] SYNC_SOURCE=%s -> skip mysql pull" % Config.SYNC_SOURCE)
        return []
    if not (Config.MYSQL_HOST and Config.MYSQL_USER and Config.MYSQL_DB):
        print("[sync] mysql credentials missing -> skip (excel fallback)")
        return []
    try:
        import pymysql
    except Exception as exc:
        print("[sync] pymysql unavailable: %s" % exc)
        return []

    rows = []
    try:
        conn = pymysql.connect(
            host=Config.MYSQL_HOST,
            port=Config.MYSQL_PORT,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM `%s`" % Config.MYSQL_TABLE)
            for r in cur.fetchall():
                out = {}
                for src, canon in B_MAP.items():
                    if src in r and r[src] is not None:
                        out[canon] = _convert(canon, r[src])
                if out.get("site_id"):
                    out["site_id"] = to_site_id(out["site_id"])
                    rows.append(out)
        conn.close()
        print("[sync] pulled %d rows from mysql" % len(rows))
    except Exception as exc:
        print("[sync][ERR] mysql pull failed: %s" % exc)
    return rows
