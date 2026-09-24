# -*- coding: utf-8 -*-
"""Main data-integration board API + 待提单/注销 management (modules 1 & P2)."""
from flask import Blueprint, request, jsonify

from backend.extensions import db
from backend.models import StationMaster, PendingSubmit, CancelSite
from backend.util.helpers import norm
from backend.api.common import ok, fail

dashboard_api = Blueprint("dashboard_api", __name__, url_prefix="/api")


def _base_query(filters):
    q = StationMaster.query
    city = norm(filters.get("city"))
    if city:
        q = q.filter(StationMaster.city == city)
    prop = norm(filters.get("property"))
    if prop:
        q = q.filter(StationMaster.property_name == prop)
    need = norm(filters.get("need_settle"))
    if need:
        q = q.filter(StationMaster.need_settle == need)
    paid = norm(filters.get("is_paid"))
    if paid:
        q = q.filter(StationMaster.is_paid == paid)
    return q


@dashboard_api.route("/dashboard", methods=["GET"])
def dashboard():
    filters = {
        "city": request.args.get("city"),
        "property": request.args.get("property"),
        "need_settle": request.args.get("need_settle"),
        "is_paid": request.args.get("is_paid"),
    }
    source = norm(request.args.get("source"))  # A / B
    q_search = norm(request.args.get("q"))
    diff_only = request.args.get("diff_only") in ("1", "true", "yes")
    try:
        page = max(1, int(request.args.get("page", 1)))
        page_size = min(500, max(10, int(request.args.get("page_size", 50))))
    except ValueError:
        page, page_size = 1, 50

    rows = [s.to_dict() for s in _base_query(filters).all()]

    # In-memory refinements (source / search / diff)
    if source in ("A", "B"):
        rows = [
            r for r in rows
            if source in (r.get("source_flag") or {}).values()
        ]
    if q_search:
        rows = [
            r for r in rows
            if q_search in str(r.get("site_name", "")) or q_search in str(r.get("property_name", ""))
            or q_search in str(r.get("site_id", ""))
        ]
    if diff_only:
        rows = [r for r in rows if r.get("diff_fields")]

    total = len(rows)
    start = (page - 1) * page_size
    page_rows = rows[start:start + page_size]

    # Summary stats
    warn_summary = {
        "total": total,
        "pending": sum(1 for r in rows if norm(r.get("pending_flag")) == "是"),
        "cancel": sum(1 for r in rows if norm(r.get("cancel_flag")) == "是"),
        "diff": sum(1 for r in rows if r.get("diff_fields")),
    }
    return ok({
        "rows": page_rows,
        "total": total,
        "page": page,
        "page_size": page_size,
        "filters": {k: norm(v) for k, v in filters.items() if norm(v)},
        "warn_summary": warn_summary,
    })


@dashboard_api.route("/pending", methods=["GET"])
def pending_list():
    rows = [p.to_dict() for p in PendingSubmit.query.all()]
    return ok({"rows": rows, "total": len(rows)})


@dashboard_api.route("/cancel", methods=["GET"])
def cancel_list():
    rows = [c.to_dict() for c in CancelSite.query.all()]
    return ok({"rows": rows, "total": len(rows)})
