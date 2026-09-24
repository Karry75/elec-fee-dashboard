# -*- coding: utf-8 -*-
"""Import / sync API (triggers the unified sync; admin-gated)."""
from flask import Blueprint, request

from backend.models import SyncLog
from backend.api.common import admin_required, ok, fail
from backend.sync.run_sync import run_sync

import_api = Blueprint("import_api", __name__, url_prefix="/api")


@import_api.route("/import/excel", methods=["POST"])
@admin_required
def import_excel():
    """Trigger a sync from the local Excel files (default path)."""
    status, message, _ = run_sync("excel")
    return ok({"status": status, "message": message})


@import_api.route("/import/sync", methods=["POST"])
@admin_required
def import_sync():
    """Trigger a sync using the configured SYNC_SOURCE (excel | mysql)."""
    source = request.get_json(silent=True) or {}
    src = source.get("source")
    status, message, _ = run_sync(src)
    return ok({"status": status, "message": message})


@import_api.route("/sync/status", methods=["GET"])
def sync_status():
    log = SyncLog.query.order_by(SyncLog.id.desc()).first()
    if not log:
        return ok({"last": None})
    return ok({"last": log.to_dict()})
