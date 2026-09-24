# -*- coding: utf-8 -*-
"""Write-back queue API (P1): enqueue edits, list, and (gated) apply."""
from datetime import datetime

from flask import Blueprint, request

from backend.extensions import db
from backend.models import PendingWriteback, StationMaster
from backend.api.common import admin_required, ok, fail
from config import Config

writeback_api = Blueprint("writeback_api", __name__, url_prefix="/api")

# Canonical field -> MySQL column (used only when write-back is enabled)
WRITEABLE_MAP = {
    "settle_method": "电费结算方式",
    "last_meter_reading": "最后一次结算度数",
    "settle_amount": "结算金额",
}


@writeback_api.route("/admin/writeback", methods=["GET"])
@admin_required
def list_writeback():
    rows = [w.to_dict() for w in PendingWriteback.query.order_by(PendingWriteback.id.desc()).all()]
    return ok({"rows": rows, "total": len(rows)})


@writeback_api.route("/admin/writeback", methods=["POST"])
@admin_required
def enqueue_writeback():
    data = request.get_json(silent=True) or {}
    site_id = data.get("site_id")
    field_name = data.get("field_name")
    new_value = data.get("new_value")
    operator = data.get("operator", "admin")
    if not site_id or not field_name:
        return fail("site_id and field_name required", 400)

    st = StationMaster.query.filter_by(site_id=str(site_id)).first()
    old_value = data.get("old_value")
    if old_value is None and st and hasattr(st, field_name):
        old_value = getattr(st, field_name)

    item = PendingWriteback(
        site_id=str(site_id),
        field_name=field_name,
        old_value=str(old_value) if old_value is not None else None,
        new_value=str(new_value),
        operator=operator,
        status="待回写",
    )
    db.session.add(item)
    db.session.commit()
    return ok({"id": item.id, "message": "queued"})


@writeback_api.route("/admin/writeback/apply", methods=["POST"])
@admin_required
def apply_writeback():
    """Apply queued write-backs. Gated by MySQL config + DBA authorization.

    Without MySQL credentials the items are marked '待DBA授权' (no destructive
    action) and a clear log line is emitted. This keeps the default run safe.
    """
    data = request.get_json(silent=True) or {}
    item_id = data.get("id")
    q = PendingWriteback.query.filter_by(status="待回写")
    if item_id:
        q = q.filter_by(id=item_id)
    items = q.all()

    mysql_ok = bool(Config.MYSQL_HOST and Config.MYSQL_USER and Config.MYSQL_DB)
    applied, authorized, failed = 0, 0, 0

    for it in items:
        if mysql_ok and Config.MYSQL_PASSWORD:
            try:
                import pymysql
                col = WRITEABLE_MAP.get(it.field_name)
                if not col:
                    it.status = "失败"
                    it.applied_at = datetime.now()
                    failed += 1
                    continue
                conn = pymysql.connect(
                    host=Config.MYSQL_HOST, port=Config.MYSQL_PORT,
                    user=Config.MYSQL_USER, password=Config.MYSQL_PASSWORD,
                    database=Config.MYSQL_DB, charset="utf8mb4",
                )
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE `%s` SET `%s`=%%s WHERE `网点id`=%%s" % (Config.MYSQL_TABLE, col),
                        (it.new_value, it.site_id),
                    )
                conn.commit()
                conn.close()
                it.status = "已回写"
                it.applied_at = datetime.now()
                applied += 1
            except Exception as exc:
                print("[writeback][ERR] %s" % exc)
                it.status = "失败"
                it.applied_at = datetime.now()
                failed += 1
        else:
            # No MySQL credentials -> require DBA authorization, do not write.
            it.status = "待DBA授权"
            authorized += 1
            print("[writeback] item %s marked 待DBA授权 (no mysql credential)" % it.id)

    db.session.commit()
    return ok({
        "applied": applied,
        "authorized": authorized,
        "failed": failed,
        "mysql_enabled": mysql_ok,
        "message": "applied=%d authorized=%d failed=%d" % (applied, authorized, failed),
    })
