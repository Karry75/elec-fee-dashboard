# -*- coding: utf-8 -*-
"""Expense board API + Excel export (module 4)."""
import io

from flask import Blueprint, request, send_file

from backend.services.stats_service import build_report, export_workbook
from backend.api.common import ok

expense_api = Blueprint("expense_api", __name__, url_prefix="/api")


@expense_api.route("/expense", methods=["GET"])
def expense():
    filters = {
        "city": request.args.get("city"),
        "property": request.args.get("property"),
        "settle_method": request.args.get("settle_method"),
        "need_settle": request.args.get("need_settle"),
        "is_paid": request.args.get("is_paid"),
    }
    report = build_report({k: v for k, v in filters.items() if v})
    return ok(report)


@expense_api.route("/expense/export", methods=["GET"])
def expense_export():
    filters = {
        "city": request.args.get("city"),
        "property": request.args.get("property"),
        "settle_method": request.args.get("settle_method"),
        "need_settle": request.args.get("need_settle"),
        "is_paid": request.args.get("is_paid"),
    }
    wb = export_workbook({k: v for k, v in filters.items() if v})
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return send_file(
        buf,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="电费支出看板导出.xlsx",
    )
