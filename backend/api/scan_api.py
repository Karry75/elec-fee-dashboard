# -*- coding: utf-8 -*-
"""Merchant scan-entry API (module 3): token verify, submit, QR, list."""
import io
import json
import os
from datetime import datetime

from flask import Blueprint, request, send_file, current_app

from backend.extensions import db
from backend.models import MerchantProfile
from backend.util.auth import verify_scan_token
from backend.util.qr import generate_qr_png
from backend.api.common import admin_required, ok, fail
from config import Config

scan_api = Blueprint("scan_api", __name__, url_prefix="/api")


@scan_api.route("/scan/verify", methods=["GET"])
def scan_verify():
    site_id = request.args.get("site_id")
    token = request.args.get("token")
    exp = request.args.get("exp")
    valid = verify_scan_token(site_id, token, exp) if site_id else False
    return ok({"valid": bool(valid), "site_id": site_id})


@scan_api.route("/scan/submit", methods=["POST"])
def scan_submit():
    site_id = request.args.get("site_id") or (request.get_json(silent=True) or {}).get("site_id")
    token = request.args.get("token")
    exp = request.args.get("exp")
    if not site_id or not verify_scan_token(site_id, token, exp):
        return fail("invalid or expired token", 403)

    # Accept multipart/form-data or JSON
    if request.files:
        data = request.form.to_dict()
    else:
        data = request.get_json(silent=True) or {}

    submit_role = data.get("submit_role")
    if not submit_role:
        return fail("submit_role required", 400)

    # Save uploaded images (P2)
    images = []
    if request.files:
        Config.ensure_dirs()
        files = request.files.getlist("images") or ([request.files.get("image")] if request.files.get("image") else [])
        for f in files:
            if not f or not f.filename:
                continue
            from werkzeug.utils import secure_filename
            fname = "%s_%s_%s" % (site_id, datetime.now().strftime("%Y%m%d%H%M%S"), secure_filename(f.filename))
            save_path = os.path.join(Config.UPLOAD_DIR, fname)
            f.save(save_path)
            images.append(os.path.relpath(save_path, Config.ROOT) if hasattr(Config, "ROOT") else fname)

    basic_fields = [
        "site_name", "meter_reading", "elec_amount", "elec_price",
        "service_price", "share_ratio", "next_settle_date", "invoice_type",
        "is_paid", "is_invoiced", "account_info", "remark",
    ]
    basic_info = {k: data.get(k) for k in basic_fields if data.get(k) is not None}

    profile = MerchantProfile(
        site_id=str(site_id),
        merchant_name=data.get("merchant_name"),
        contact_name=data.get("contact_name"),
        contact_phone=data.get("contact_phone"),
        submit_role=submit_role,
        basic_info=json.dumps(basic_info, ensure_ascii=False),
        images=json.dumps(images, ensure_ascii=False),
        status="待审核",
        submit_time=datetime.now(),
    )
    db.session.add(profile)
    db.session.commit()
    return ok({"id": profile.id, "message": "submitted"})


@scan_api.route("/merchant/qr", methods=["GET"])
@admin_required
def merchant_qr():
    site_id = request.args.get("site_id")
    if not site_id:
        return fail("site_id required", 400)
    base_url = request.args.get("base_url") or Config.BASE_URL
    try:
        png_bytes, url = generate_qr_png(site_id, base_url=base_url)
    except Exception as exc:
        return fail("qr generation failed: %s" % exc, 500)
    return send_file(
        io.BytesIO(png_bytes),
        mimetype="image/png",
        as_attachment=False,
        download_name="scan_%s.png" % site_id,
    )


@scan_api.route("/merchant/list", methods=["GET"])
@admin_required
def merchant_list():
    rows = [m.to_dict() for m in MerchantProfile.query.order_by(MerchantProfile.id.desc()).all()]
    return ok({"rows": rows, "total": len(rows)})
