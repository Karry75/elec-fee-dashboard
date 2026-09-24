# -*- coding: utf-8 -*-
"""Unified sync orchestrator: pull -> merge -> upsert -> compute_warn -> log.

Callable both from the CLI (run_sync.py) and the import API. Requires a Flask
app context for database access.
"""
import os
import traceback
from datetime import datetime

from config import Config
from backend.extensions import db
from backend.models import (
    StationMaster, SyncLog, PendingSubmit, CancelSite,
)
from backend.sync.import_excel import read_excel_a, read_excel_b
from backend.sync.pull_mysql import pull_mysql
from backend.sync.merge_view import merge_view
from backend.sync.compute_warn import compute_warn
from backend.util.notify import push_wecom


def _file_exists(path):
    return bool(path) and os.path.isfile(path)


def _upsert_stations(merged):
    existing = {s.site_id: s for s in StationMaster.query.all()}
    count = 0
    for rec in merged:
        sid = rec.get("site_id")
        if not sid:
            continue
        obj = existing.get(sid)
        if obj is None:
            obj = StationMaster(site_id=sid)
            db.session.add(obj)
        for k, v in rec.items():
            if hasattr(obj, k):
                setattr(obj, k, v)
        count += 1
    db.session.commit()
    return count


def _replace_table(model, rows):
    model.query.delete()
    db.session.commit()
    for r in rows:
        db.session.add(model(**r))
    db.session.commit()


def run_sync(source=None):
    """Run a full sync. Returns (status, message, exit_code)."""
    from backend.app import create_app

    app = create_app()
    with app.app_context():
        Config.ensure_dirs()
        src = source or Config.SYNC_SOURCE
        rows_pulled = 0
        status = "[OK]"
        message_parts = []

        try:
            # ---- 1. Pull ----
            if src == "mysql":
                b_rows = pull_mysql()
                a_main, pending, cancel = ([], [], [])
                if _file_exists(Config.EXCEL_A_PATH):
                    a_main, pending, cancel = read_excel_a(Config.EXCEL_A_PATH)
            else:
                b_rows = []
                if _file_exists(Config.EXCEL_B_PATH):
                    b_rows = read_excel_b(Config.EXCEL_B_PATH)
                else:
                    message_parts.append("Excel B not found: %s" % Config.EXCEL_B_PATH)
                a_main, pending, cancel = ([], [], [])
                if _file_exists(Config.EXCEL_A_PATH):
                    a_main, pending, cancel = read_excel_a(Config.EXCEL_A_PATH)
                else:
                    message_parts.append("Excel A not found: %s" % Config.EXCEL_A_PATH)

            rows_pulled = len(b_rows) + len(a_main)

            # ---- 2. Merge ----
            merged = merge_view(b_rows, a_main, pending, cancel)
            rows_merged = _upsert_stations(merged)

            # ---- 3. Pending / Cancel tables ----
            _replace_table(PendingSubmit, [
                {k: v for k, v in p.items() if k in (
                    "site_id", "site_name", "note", "status", "raw")}
                for p in pending
            ])
            _replace_table(CancelSite, [
                {k: v for k, v in c.items() if k in (
                    "site_id", "site_name", "account_no", "meter_no",
                    "meter_sn", "status", "raw")}
                for c in cancel
            ])

            # ---- 4. Compute warn ----
            warn_count = compute_warn(Config.WARN_LEAD_DAYS, Config.CONTRACT_WARN_LEAD_DAYS)

            # ---- 5. Status decision ----
            if rows_merged == 0:
                status = "[ERR]"
                message_parts.append("no rows merged")
            else:
                diff_total = sum(
                    1 for m in merged if m.get("diff_fields") not in (None, "[]", "")
                )
                if pending or cancel or diff_total:
                    status = "[WARN]"
                message_parts.append(
                    "merged=%d diff_rows=%d pending=%d cancel=%d warns=%d"
                    % (rows_merged, diff_total, len(pending), len(cancel), warn_count)
                )

                # ---- 6. WeCom push (P2) ----
                if warn_count > 0:
                    summary = ("## ⚡ 电费结算预警\n"
                               f"> 共 {warn_count} 条预警（提前 {Config.WARN_LEAD_DAYS} 天）\n"
                               f"> 数据合并 {rows_merged} 条，待提单 {len(pending)} 条，需注销 {len(cancel)} 条\n"
                               f"> 同步时间 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
                    push_wecom(summary)

            # ---- 7. Sync log ----
            db.session.add(SyncLog(
                sync_time=datetime.now(),
                source=src,
                rows_pulled=rows_pulled,
                rows_merged=rows_merged,
                warn_recomputed=warn_count,
                status=status,
                message="; ".join(message_parts) or "ok",
            ))
            db.session.commit()

        except Exception as exc:  # pragma: no cover
            status = "[ERR]"
            message_parts.append("exception: %s" % exc)
            traceback.print_exc()
            try:
                db.session.add(SyncLog(
                    sync_time=datetime.now(),
                    source=src,
                    rows_pulled=rows_pulled,
                    rows_merged=0,
                    warn_recomputed=0,
                    status=status,
                    message="; ".join(message_parts),
                ))
                db.session.commit()
            except Exception:
                pass

    exit_code = 1 if status == "[ERR]" else 0
    return status, "; ".join(message_parts) or "ok", exit_code
