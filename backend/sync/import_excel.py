# -*- coding: utf-8 -*-
"""Excel import: read file A (结算登记表) and file B (网点/商户总库).

All values are mapped to the canonical snake_case schema used by StationMaster.
A is the supplementary source (補 last_read_date precision, 待提单, 注销);
B is the master source (bigger, richer).
"""
import re

import pandas as pd

from backend.util.helpers import is_empty, norm, parse_date, to_float


def to_site_id(value):
    """Normalize a site id to a clean string (handles float 23111639.0)."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, float):
        value = int(value)
    s = str(value).strip()
    if is_empty(s):
        return None
    return s


# --- Column mapping: Chinese header -> canonical field ---
A_MAIN_MAP = {
    "物业名称": "property_name",
    "网点ID": "site_id",
    "网点名称": "site_name",
    "最后一次结算度数": "last_meter_reading",
    "最后一次结算抄表日期": "last_read_date",
    "结算周期": "settle_cycle",
    "换电柜数量": "cabinet_count",
    "换电柜类型": "cabinet_type",
    "电单价": "elec_price",
    "服务费单价": "service_price",
    "分成比例": "share_ratio",
    "年度场地费": "annual_site_fee",
    "场地/电费押金": "deposit",
    "合同期限": "contract_term",
    "发票类型": "invoice_type",
    "是否付款": "is_paid",
    "是否已开发票/收据": "is_invoiced",
    "收款账户信息": "account_info",
    "备注": "remark",
}

B_MAP = {
    "商户ID": "merchant_id",
    "商户名称": "merchant_name",
    "网点id": "site_id",
    "网点名称": "site_name",
    "网点行业": "industry",
    "审核状态": "audit_status",
    "合作时间": "cooperate_time",
    "合同期限": "contract_term",
    "物业公司名称": "property_name",
    "换电柜sn": "cabinet_sn",
    "换电柜数量": "cabinet_count",
    "换电柜类型": "cabinet_type",
    "电费单价": "elec_price",
    "服务费单价": "service_price",
    "分成比例": "share_ratio",
    "年度场地费": "annual_site_fee",
    "场地/电费押金": "deposit",
    "最近结算时间": "last_read_date",
    "最后一次结算度数": "last_meter_reading",
    "下次结算时间": "next_settle_date",
    "是否要结算电费": "need_settle",
    "总金额": "total_amount",
    "结算金额": "settle_amount",
    "独立电表状态": "meter_status",
    "电费结算方式": "settle_method",
    "电费结算周期": "settle_cycle",
    "发票类型": "invoice_type",
    "是否付款": "is_paid",
    "是否已开发票/收据": "is_invoiced",
    "收款账户信息": "account_info",
    "城市": "city",
    "区域": "district",
    "街道": "street",
    "社区": "community",
    "详细地址": "address",
    "备注": "remark",
}

# Fields that are numeric
NUMERIC_FIELDS = {
    "cabinet_count", "elec_price", "service_price", "share_ratio",
    "annual_site_fee", "deposit", "last_meter_reading",
    "total_amount", "settle_amount",
}
# Fields that are dates
DATE_FIELDS = {"last_read_date", "next_settle_date", "cooperate_time"}


def _convert(field, value):
    if field in NUMERIC_FIELDS:
        return to_float(value)
    if field in DATE_FIELDS:
        return parse_date(value)
    return norm(value)


def _map_row(row, mapping):
    out = {}
    for src, canon in mapping.items():
        if src in row and row[src] is not None:
            out[canon] = _convert(canon, row[src])
    if "site_id" in out:
        out["site_id"] = to_site_id(out["site_id"])
    return out


def read_excel_a(path):
    """Return (main_rows, pending_rows, cancel_rows) from file A."""
    main_rows = []
    pending_rows = []
    cancel_rows = []

    # --- 总表 (main) ---
    df = pd.read_excel(path, sheet_name="总表", header=0, dtype=object)
    df = df.where(pd.notna(df), None)
    for _, r in df.iterrows():
        row = _map_row(r.to_dict(), A_MAIN_MAP)
        if row.get("site_id"):
            main_rows.append(row)

    # --- 8月待提单 (no header) ---
    try:
        dp = pd.read_excel(path, sheet_name="8月待提单", header=None, dtype=object)
        dp = dp.where(pd.notna(dp), None)
        for _, r in dp.iterrows():
            vals = list(r.values)
            site_name = norm(vals[0]) if len(vals) > 0 else None
            note = norm(vals[1]) if len(vals) > 1 else None
            status = norm(vals[2]) if len(vals) > 2 else None
            combined = " ".join([str(v) for v in vals if v is not None])
            m = re.search(r"网点ID[:：]\s*(\d+)", combined)
            site_id = m.group(1) if m else None
            # site name fallback: a value that is not the status note
            if not site_name and status and "已提单" in (status or ""):
                site_name = None
            pending_rows.append({
                "site_id": site_id,
                "site_name": site_name,
                "note": note,
                "status": status,
                "raw": combined,
            })
    except Exception as exc:
        print("[warn] 8月待提单 sheet read failed: %s" % exc)

    # --- 南方电网需注销 (no header) ---
    try:
        dc = pd.read_excel(path, sheet_name="南方电网需注销", header=None, dtype=object)
        dc = dc.where(pd.notna(dc), None)
        for _, r in dc.iterrows():
            vals = list(r.values)
            site_id = to_site_id(vals[0]) if len(vals) > 0 else None
            site_name = norm(vals[1]) if len(vals) > 1 else None
            account_no = norm(vals[2]) if len(vals) > 2 else None
            meter_no = norm(vals[4]) if len(vals) > 4 else None
            status = norm(vals[5]) if len(vals) > 5 else None
            cancel_rows.append({
                "site_id": site_id,
                "site_name": site_name,
                "account_no": account_no,
                "meter_no": meter_no,
                "status": status or "已注销",
                "raw": " ".join([str(v) for v in vals if v is not None]),
            })
    except Exception as exc:
        print("[warn] 南方电网需注销 sheet read failed: %s" % exc)

    return main_rows, pending_rows, cancel_rows


def read_excel_b(path):
    """Return list of canonical dicts from file B (master source)."""
    df = pd.read_excel(path, sheet_name=0, header=0, dtype=object)
    df = df.where(pd.notna(df), None)
    rows = []
    for _, r in df.iterrows():
        row = _map_row(r.to_dict(), B_MAP)
        if row.get("site_id"):
            rows.append(row)
    return rows
