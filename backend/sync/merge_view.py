# -*- coding: utf-8 -*-
"""Merge B (master) and A (supplementary) into the station_master view.

Rules:
- B is the master data source (richer).
- A supplements `last_read_date` precision (A wins there) and fills fields
  where B is empty.
- `need_settle` is derived from `settle_method` when not present in source.
- Field-level source is recorded in `source_flag`; conflicts (A and B both
  present and differing) are collected into `diff_fields` for UI highlighting.
- 待提单 / 注销 marks from Excel sheet A are applied to flags.
"""
import json

from backend.util.helpers import is_empty, norm


def derive_need_settle(settle_method):
    m = norm(settle_method)
    if m in ("不结算",):
        return "否"
    if m in ("-", "", "无"):
        return "否"
    return "是"


def _index_by_id_and_name(rows):
    by_id, by_name = {}, {}
    for r in rows:
        sid = r.get("site_id")
        if sid:
            by_id.setdefault(sid, r)
        name = norm(r.get("site_name"))
        if name:
            by_name.setdefault(name.lower(), r)
    return by_id, by_name


def merge_view(b_rows, a_rows, pending_rows, cancel_rows):
    """Return list of merged station dicts ready for UPSERT."""
    a_by_id, a_by_name = _index_by_id_and_name(a_rows)
    pend_by_id, pend_by_name = _index_by_id_and_name(pending_rows)
    canc_by_id, canc_by_name = _index_by_id_and_name(cancel_rows)

    merged = {}

    for b in b_rows:
        sid = b.get("site_id")
        if not sid:
            continue
        record = dict(b)
        source_map = {}
        b_provided = set()
        for fld, val in record.items():
            if val is not None:
                b_provided.add(fld)
                source_map[fld] = "B"

        diff = []
        a = a_by_id.get(sid) or a_by_name.get(norm(record.get("site_name")), None)
        if a:
            for fld, aval in a.items():
                if aval is None:
                    continue
                if fld == "last_read_date":
                    # A is more precise -> prefer A
                    if fld in b_provided and norm(record.get(fld)) != norm(aval):
                        diff.append(fld)
                    record[fld] = aval
                    source_map[fld] = "A"
                else:
                    if fld in b_provided:
                        if norm(record.get(fld)) != norm(aval):
                            diff.append(fld)
                        # B wins, keep B value
                    else:
                        record[fld] = aval
                        source_map[fld] = "A"

        if is_empty(record.get("need_settle")):
            record["need_settle"] = derive_need_settle(record.get("settle_method"))
            source_map["need_settle"] = "SYS"

        record["source_flag"] = json.dumps(source_map, ensure_ascii=False)
        record["diff_fields"] = json.dumps(sorted(set(diff)), ensure_ascii=False)
        merged[sid] = record

    # Sites present only in A (not in B)
    for sid, a in a_by_id.items():
        if sid in merged:
            continue
        record = dict(a)
        source_map = {fld: "A" for fld, v in record.items() if v is not None}
        if is_empty(record.get("need_settle")):
            record["need_settle"] = derive_need_settle(record.get("settle_method"))
            source_map["need_settle"] = "SYS"
        record["source_flag"] = json.dumps(source_map, ensure_ascii=False)
        record["diff_fields"] = json.dumps([], ensure_ascii=False)
        merged[sid] = record

    # Apply 待提单 / 注销 flags
    for sid, record in merged.items():
        name = norm(record.get("site_name"))
        pend = pend_by_id.get(sid) or (pend_by_name.get(name) if name else None)
        if pend:
            record["pending_flag"] = "是"
            record["pending_note"] = (pend.get("note") or "")
        canc = canc_by_id.get(sid) or (canc_by_name.get(name) if name else None)
        if canc:
            record["cancel_flag"] = "是"
            record["cancel_note"] = (canc.get("status") or "已注销")

    return list(merged.values())
