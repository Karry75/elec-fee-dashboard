# -*- coding: utf-8 -*-
"""Shared API helpers: admin-token gating and JSON responses."""
import functools

from flask import request, jsonify

from backend.util.auth import require_admin_token, ADMIN_DEV_OPEN


def admin_check():
    """Validate admin token from header/query/body.

    Returns (True, None) when granted. When ADMIN_TOKEN is unset the endpoint
    runs in dev-open mode (granted, with a warning). Otherwise returns
    (False, (message, status_code)).
    """
    provided = (
        request.headers.get("X-Admin-Token")
        or request.args.get("token")
        or (request.get_json(silent=True) or {}).get("token")
    )
    res = require_admin_token(provided)
    if res is True:
        return True, None
    if res is ADMIN_DEV_OPEN:
        print("[warn] admin endpoint used in DEV-OPEN mode (ADMIN_TOKEN not set)")
        return True, None
    return False, ("admin token required", 403)


def admin_required(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        ok, err = admin_check()
        if not ok:
            return jsonify({"ok": False, "message": err[0]}), err[1]
        return f(*args, **kwargs)
    return wrapper


def ok(data=None, message="ok"):
    return jsonify({"ok": True, "message": message, "data": data})


def fail(message="error", code=400, data=None):
    return jsonify({"ok": False, "message": message, "data": data}), code
