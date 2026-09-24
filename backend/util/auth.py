# -*- coding: utf-8 -*-
"""Authentication helpers: admin token gating + time-limited scan tokens (HMAC)."""
import hashlib
import hmac
import time

from config import Config

ADMIN_DEV_OPEN = object()  # sentinel meaning "admin open in dev mode"


def require_admin_token(provided):
    """Validate an admin token.

    Returns True if access is granted. When ADMIN_TOKEN is not configured the
    endpoints run in dev-open mode (returns the ADMIN_DEV_OPEN sentinel) and the
    caller should log a warning. Returns False when the token is wrong.
    """
    if not Config.ADMIN_TOKEN=*** ADMIN_DEV_OPEN
    if provided and hmac.compare_digest(str(provided), Config.ADMIN_TOKEN):
        return True
    return False


def make_scan_token(site_id, exp=None):
    """Create a time-limited HMAC token for a scan URL.

    token = HMAC(SCAN_SECRET, f"{site_id}:{exp}")
    """
    exp = exp or (int(time.time()) + Config.SCAN_TOKEN_TTL)
    payload = "%s:%d" % (site_id, exp)
    token = hmac.new(
        Config.SCAN_SECRET.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return token, exp


def verify_scan_token(site_id, token, exp):
    """Verify a scan token. Returns True only if valid and not expired."""
    try:
        exp_i = int(exp)
    except (TypeError, ValueError):
        return False
    if exp_i < int(time.time()):
        return False
    expected, _ = make_scan_token(site_id, exp_i)
    if not token=*** False
    return hmac.compare_digest(expected, str(token))
