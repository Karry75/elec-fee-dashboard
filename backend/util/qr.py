# -*- coding: utf-8 -*-
"""QR code generation for scan-form URLs (module 3)."""
import io
import time

import qrcode

from config import Config
from backend.util.auth import make_scan_token


def build_scan_url(site_id, base_url=None, ttl=None):
    """Build the mobile scan-form URL carrying a time-limited token."""
    base_url = base_url or Config.BASE_URL
    token, exp = make_scan_token(site_id, exp=None if ttl is None else int(time.time()) + ttl)
    return "%s/scan?site_id=%s&exp=%d&token=%s" % (base_url.rstrip("/"), site_id, exp, token)


def generate_qr_png(site_id, base_url=None):
    """Return PNG bytes of the QR code for a site's scan URL."""
    url = build_scan_url(site_id, base_url=base_url)
    qr = qrcode.QRCode(version=4, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=8, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue(), url
