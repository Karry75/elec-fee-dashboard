# -*- coding: utf-8 -*-
"""Electricity fee board API + drill-down detail (module 2)."""
from flask import Blueprint, request

from backend.extensions import db
from backend.models import (
    StationMaster, MerchantProfile, WarnRecord, PendingSubmit, CancelSite,
)
from backend.services.warn_service import classify, top_warns
from backend.util.helpers import norm
from backend.api.common import ok
from config import Config

board_api = Blueprint("board_api", __name__, url_prefix="/api")


def _board_query(filters):
    q = StationMaster.query
    city = norm(filters.get("city"))
    if city:
        q = q.filter(StationMaster.city == city)
    prop = norm(filters.get("property"))
    if prop:
        q = q.filter(StationMaster.property_name == prop)
    status = norm(filters.get("status"))
    if status == "warn":
        q = q.filter(StationMaster.warn_flag == "是")
    elif status == "need":
        q = q.filter(StationMaster.need_settle == "是")
    elif status == "settled":
        q = q.filter(StationMaster.is_settled == "是")
    elif status == "unsettled":
        q = q.filter(StationMaster.is_settled != "是")
    elif status == "pending":
        q = q.filter(StationMaster.pending_flag == "是")
    elif status == "cancel":
        q = q.filter(StationMaster.cancel_flag == "是")
    month = norm(filters.get("next_settle_month"))
    if month:
        q = q.filter(StationMaster.next_settle_date.like("%s%%" % month))
    return q


@board_api.route("/board", methods=["GET"])
def board():
    filters = {
        "city": request.args.get("city"),
        "property": request.args.get("property"),
        "status": request.args.get("status"),
        "next_settle_month": request.args.get("next_settle_month"),
    }
    q_search = norm(request.args.get("q"))
    rows = [s.to_dict(include_meta=False) for s in _board_query(filters).all()]
    if q_search:
        rows = [
            r for r in rows
            if q_search in str(r.get("site_name", "")) or q_search in str(r.get("property_name", ""))
            or q_search in str(r.get("site_id", ""))
        ]
    # classify each row
    for r in rows:
        r.update(classify(r, Config.WARN_LEAD_DAYS))

    warns = top_warns(rows, Config.WARN_LEAD_DAYS)
    summary = {
        "total": len(rows),
        "warn_count": len(warns),
        "need_settle": sum(1 for r in rows if norm(r.get("need_settle")) == "是"),
        "unsettled": sum(1 for r in rows if norm(r.get("is_settled")) != "是"),
    }
    return ok({
        "rows": rows,
        "warn_list": warns,
        "summary": summary,
        "filters": {k: norm(v) for k, v in filters.items() if norm(v)},
        "lead_days": Config.WARN_LEAD_DAYS,
    })


@board_api.route("/board/<site_id>", methods=["GET"])
def board_detail(site_id):
    st = StationMaster.query.filter_by(site_id=site_id).first()
    if not st:
        return ok({"station": None, "message": "not found"})
    station = st.to_dict()
    station.update(classify(station, Config.WARN_LEAD_DAYS))
    profiles = [m.to_dict() for m in MerchantProfile.query.filter_by(site_id=site_id).all()]
    warns = [w.to_dict() for w in WarnRecord.query.filter_by(site_id=site_id).all()]
    pending = [p.to_dict() for p in PendingSubmit.query.filter_by(site_id=site_id).all()]
    cancel = [c.to_dict() for c in CancelSite.query.filter_by(site_id=site_id).all()]
    return ok({
        "station": station,
        "merchant_profiles": profiles,
        "warn_records": warns,
        "pending": pending,
        "cancel": cancel,
    })
