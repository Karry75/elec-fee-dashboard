# -*- coding: utf-8 -*-
"""Warn computation: settlement-due warnings + contract/deposit expiry (P2 T15)."""
import re
from datetime import date, datetime

from backend.extensions import db
from backend.models import StationMaster, WarnRecord
from backend.util.helpers import days_between, is_empty, norm, parse_date


def parse_contract_end(term):
    """Extract the end date (latest date) from a contract_term string."""
    if is_empty(term):
        return None
    dates = re.findall(r"\d{4}[-/.]\d{1,2}[-/.]\d{1,2}", str(term))
    if not dates:
        return None
    parsed = [parse_date(d) for d in dates]
    parsed = [p for p in parsed if p]
    return max(parsed) if parsed else None


def compute_warn(lead_days=7, contract_lead_days=30):
    """Recompute warn flags for all stations. Returns number of warn rows."""
    stations = StationMaster.query.all()
    # Rebuild warn records from scratch each run (snapshot semantics)
    WarnRecord.query.delete()
    db.session.commit()

    warn_count = 0
    today = date.today()

    for st in stations:
        warn_flag = "否"
        warn_level = 0

        # --- Settlement due rule (module 2) ---
        if norm(st.need_settle) == "是" and norm(st.is_settled) != "是":
            d = days_between(st.next_settle_date, today)
            if d is not None and d <= lead_days:
                warn_flag = "是"
                level = 1 if d <= 0 else (2 if d <= 3 else 3)
                warn_level = max(warn_level, level)
                reason = "结算逾期" if d <= 0 else "结算临期"
                db.session.add(WarnRecord(
                    site_id=st.site_id,
                    warn_level=level,
                    warn_reason=reason,
                    due_date=st.next_settle_date,
                    warn_date=today.isoformat(),
                    channel="board",
                ))
                warn_count += 1

        # --- Contract expiry rule (P2 T15) ---
        end = parse_contract_end(st.contract_term)
        if end:
            cd = (datetime.strptime(end, "%Y-%m-%d").date() - today).days
            if 0 <= cd <= contract_lead_days:
                warn_flag = "是"
                level = 1 if cd <= 0 else (2 if cd <= 7 else 3)
                warn_level = max(warn_level, level)
                db.session.add(WarnRecord(
                    site_id=st.site_id,
                    warn_level=level,
                    warn_reason="合同到期",
                    due_date=end,
                    warn_date=today.isoformat(),
                    channel="board",
                ))
                warn_count += 1

        st.warn_flag = warn_flag
        st.warn_level = warn_level

    db.session.commit()
    return warn_count
