# -*- coding: utf-8 -*-
"""SQLAlchemy 2.0 ORM models for the local SQLite store.

StationMaster is a local snapshot of the merged view (B/DB master + A/Excel
supplements). MerchantProfile, WarnRecord, SyncLog and PendingWriteback are
supporting entities. All JSON-ish fields are stored as TEXT and (de)serialized
in code to remain portable across SQLite versions.
"""
import json
from datetime import datetime

from backend.extensions import db


def _json_dump(value):
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False)


def _json_load(value):
    if value is None or value == "":
        return None
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return None


class StationMaster(db.Model):
    """Merged master view keyed by site_id (网点ID)."""

    __tablename__ = "station_master"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    site_id = db.Column(db.String(32), unique=True, index=True, nullable=False)
    site_name = db.Column(db.String(255))
    merchant_id = db.Column(db.String(64))
    merchant_name = db.Column(db.String(255))
    property_name = db.Column(db.String(255), index=True)
    city = db.Column(db.String(64), index=True)
    district = db.Column(db.String(64))
    street = db.Column(db.String(128))
    community = db.Column(db.String(128))
    address = db.Column(db.String(512))
    industry = db.Column(db.String(64))
    audit_status = db.Column(db.String(32))
    cooperate_time = db.Column(db.String(32))
    contract_term = db.Column(db.Text)
    cabinet_sn = db.Column(db.Text)
    cabinet_count = db.Column(db.Float)
    cabinet_type = db.Column(db.String(64))
    elec_price = db.Column(db.Float)
    service_price = db.Column(db.Float)
    share_ratio = db.Column(db.Float)
    annual_site_fee = db.Column(db.Float)
    deposit = db.Column(db.Float)
    last_meter_reading = db.Column(db.Float)
    last_read_date = db.Column(db.String(32))
    next_settle_date = db.Column(db.String(32))
    settle_cycle = db.Column(db.String(32))
    need_settle = db.Column(db.String(8))  # 是/否
    is_settled = db.Column(db.String(8), default="否")  # 是/否
    total_amount = db.Column(db.Float)
    settle_amount = db.Column(db.Float)
    meter_status = db.Column(db.String(64))
    settle_method = db.Column(db.String(32))
    invoice_type = db.Column(db.String(32))
    is_paid = db.Column(db.String(8))  # 是/否
    is_invoiced = db.Column(db.String(8))  # 是/否
    account_info = db.Column(db.Text)
    remark = db.Column(db.Text)
    # field-level source map: {"field": "A"|"B"|"SYS"}
    source_flag = db.Column(db.Text)
    # list of fields where A and B both had values and differed
    diff_fields = db.Column(db.Text)
    warn_flag = db.Column(db.String(8), default="否")  # 是/否
    warn_level = db.Column(db.Integer, default=0)  # 0 none,1 urgent,2 high,3 medium
    pending_flag = db.Column(db.String(8), default="否")  # 待提单 是/否
    pending_note = db.Column(db.Text)
    cancel_flag = db.Column(db.String(8), default="否")  # 注销 是/否
    cancel_note = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self, include_meta=True):
        d = {
            "id": self.id,
            "site_id": self.site_id,
            "site_name": self.site_name,
            "merchant_id": self.merchant_id,
            "merchant_name": self.merchant_name,
            "property_name": self.property_name,
            "city": self.city,
            "district": self.district,
            "street": self.street,
            "community": self.community,
            "address": self.address,
            "industry": self.industry,
            "audit_status": self.audit_status,
            "cooperate_time": self.cooperate_time,
            "contract_term": self.contract_term,
            "cabinet_sn": self.cabinet_sn,
            "cabinet_count": self.cabinet_count,
            "cabinet_type": self.cabinet_type,
            "elec_price": self.elec_price,
            "service_price": self.service_price,
            "share_ratio": self.share_ratio,
            "annual_site_fee": self.annual_site_fee,
            "deposit": self.deposit,
            "last_meter_reading": self.last_meter_reading,
            "last_read_date": self.last_read_date,
            "next_settle_date": self.next_settle_date,
            "settle_cycle": self.settle_cycle,
            "need_settle": self.need_settle,
            "is_settled": self.is_settled,
            "total_amount": self.total_amount,
            "settle_amount": self.settle_amount,
            "meter_status": self.meter_status,
            "settle_method": self.settle_method,
            "invoice_type": self.invoice_type,
            "is_paid": self.is_paid,
            "is_invoiced": self.is_invoiced,
            "account_info": self.account_info,
            "remark": self.remark,
            "warn_flag": self.warn_flag,
            "warn_level": self.warn_level,
            "pending_flag": self.pending_flag,
            "pending_note": self.pending_note,
            "cancel_flag": self.cancel_flag,
            "cancel_note": self.cancel_note,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_meta:
            d["source_flag"] = _json_load(self.source_flag)
            d["diff_fields"] = _json_load(self.diff_fields) or []
        return d


class MerchantProfile(db.Model):
    """Merchant / property / agent submitted profiles via scan form."""

    __tablename__ = "merchant_profile"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    site_id = db.Column(db.String(32), index=True)
    merchant_name = db.Column(db.String(255))
    contact_name = db.Column(db.String(64))
    contact_phone = db.Column(db.String(32))
    submit_role = db.Column(db.String(16))  # 物业/业务员/商户
    basic_info = db.Column(db.Text)  # JSON
    images = db.Column(db.Text)  # JSON list of uploaded file paths
    status = db.Column(db.String(16), default="待审核")
    submit_time = db.Column(db.DateTime, default=datetime.now)
    sync_time = db.Column(db.DateTime)

    def to_dict(self):
        return {
            "id": self.id,
            "site_id": self.site_id,
            "merchant_name": self.merchant_name,
            "contact_name": self.contact_name,
            "contact_phone": self.contact_phone,
            "submit_role": self.submit_role,
            "basic_info": _json_load(self.basic_info),
            "images": _json_load(self.images) or [],
            "status": self.status,
            "submit_time": self.submit_time.isoformat() if self.submit_time else None,
            "sync_time": self.sync_time.isoformat() if self.sync_time else None,
        }


class WarnRecord(db.Model):
    """Early-warning records (settlement due / contract expiry)."""

    __tablename__ = "warn_record"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    site_id = db.Column(db.String(32), index=True)
    warn_level = db.Column(db.Integer, default=0)
    warn_reason = db.Column(db.String(64))
    due_date = db.Column(db.String(32))
    warn_date = db.Column(db.String(32))
    is_notified = db.Column(db.String(8), default="否")
    channel = db.Column(db.String(16))
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "site_id": self.site_id,
            "warn_level": self.warn_level,
            "warn_reason": self.warn_reason,
            "due_date": self.due_date,
            "warn_date": self.warn_date,
            "is_notified": self.is_notified,
            "channel": self.channel,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class SyncLog(db.Model):
    """Audit log of each sync run."""

    __tablename__ = "sync_log"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sync_time = db.Column(db.DateTime, default=datetime.now)
    source = db.Column(db.String(16))  # excel / mysql
    rows_pulled = db.Column(db.Integer, default=0)
    rows_merged = db.Column(db.Integer, default=0)
    warn_recomputed = db.Column(db.Integer, default=0)
    status = db.Column(db.String(8))  # [OK] / [WARN] / [ERR]
    message = db.Column(db.Text)

    def to_dict(self):
        return {
            "id": self.id,
            "sync_time": self.sync_time.isoformat() if self.sync_time else None,
            "source": self.source,
            "rows_pulled": self.rows_pulled,
            "rows_merged": self.rows_merged,
            "warn_recomputed": self.warn_recomputed,
            "status": self.status,
            "message": self.message,
        }


class PendingWriteback(db.Model):
    """Queue of field edits awaiting write-back to the source DB (P1)."""

    __tablename__ = "pending_writeback"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    site_id = db.Column(db.String(32), index=True)
    field_name = db.Column(db.String(32))
    old_value = db.Column(db.Text)
    new_value = db.Column(db.Text)
    operator = db.Column(db.String(64))
    status = db.Column(db.String(16), default="待回写")  # 待回写/已回写/失败/待DBA授权
    created_at = db.Column(db.DateTime, default=datetime.now)
    applied_at = db.Column(db.DateTime)

    def to_dict(self):
        return {
            "id": self.id,
            "site_id": self.site_id,
            "field_name": self.field_name,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "operator": self.operator,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "applied_at": self.applied_at.isoformat() if self.applied_at else None,
        }


class PendingSubmit(db.Model):
    """待提单 (pending submission list) parsed from Excel sheet A."""

    __tablename__ = "pending_submit"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    site_id = db.Column(db.String(32), index=True)
    site_name = db.Column(db.String(255))
    note = db.Column(db.Text)
    status = db.Column(db.String(64))
    raw = db.Column(db.Text)

    def to_dict(self):
        return {
            "id": self.id,
            "site_id": self.site_id,
            "site_name": self.site_name,
            "note": self.note,
            "status": self.status,
            "raw": self.raw,
        }


class CancelSite(db.Model):
    """南方电网需注销网点 (sites to be cancelled)."""

    __tablename__ = "cancel_site"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    site_id = db.Column(db.String(32), index=True)
    site_name = db.Column(db.String(255))
    account_no = db.Column(db.String(64))
    meter_no = db.Column(db.String(64))
    meter_sn = db.Column(db.String(64))
    status = db.Column(db.String(32))
    raw = db.Column(db.Text)

    def to_dict(self):
        return {
            "id": self.id,
            "site_id": self.site_id,
            "site_name": self.site_name,
            "account_no": self.account_no,
            "meter_no": self.meter_no,
            "meter_sn": self.meter_sn,
            "status": self.status,
            "raw": self.raw,
        }


def json_dump(value):
    return _json_dump(value)


def json_load(value):
    return _json_load(value)
