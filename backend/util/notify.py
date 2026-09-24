# -*- coding: utf-8 -*-
"""P2 WeCom (企业微信) webhook push — config-gated, graceful skip when unset."""
import logging

import requests

from config import Config

logger = logging.getLogger("elec_fee.notify")


def push_wecom(text, timeout=5):
    """Push a markdown/text message to the configured WeCom webhook.

    Returns True if sent, False if skipped/failed. Never raises.
    """
    webhook = Config.WECOM_WEBHOOK
    if not webhook:
        logger.info("[wecom] WECOM_WEBHOOK not set -> skip push")
        return False
    try:
        resp = requests.post(
            webhook,
            json={"msgtype": "markdown", "markdown": {"content": text}},
            timeout=timeout,
        )
        if resp.status_code == 200 and '"errcode":0' in resp.text:
            logger.info("[wecom] push ok")
            return True
        logger.warning("[wecom] push returned %s: %s", resp.status_code, resp.text[:200])
        return False
    except Exception as exc:
        logger.warning("[wecom] push failed: %s", exc)
        return False
