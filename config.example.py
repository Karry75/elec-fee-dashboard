# -*- coding: utf-8 -*-
"""EXAMPLE configuration — copy to config.py and fill in real values, OR keep
config.py reading from environment via .env. Never commit real secrets.

This file is safe to commit. Real values go in .env (see .env.example).
"""

# Core
SECRET_KEY = "CHANGE-ME-use-a-long-random-string"
HOST = "0.0.0.0"
PORT = 8173
DEBUG = False

# Data directories (relative to project root)
DATA_DIR = "data"
UPLOAD_DIR = "data/uploads"
SEED_DIR = "data/seed"
FRONTEND_DIST = "frontend/dist"

# Sync source: "excel" (default, no DB credential needed) or "mysql"
SYNC_SOURCE = "excel"
EXCEL_A_PATH = r"C:\Users\Karry\Desktop\电费\电费结算登记表.xlsx"
EXCEL_B_PATH = r"C:\Users\Karry\Desktop\电费\电费情况20260907.xlsx"

# MySQL read-only source (only used when SYNC_SOURCE=mysql)
MYSQL_HOST = ""          # e.g. "192.168.1.x"
MYSQL_PORT = 3306
MYSQL_USER = ""
MYSQL_PASSWORD = ""      # placeholder — real value via .env only
MYSQL_DB = ""
MYSQL_TABLE = "site_info_pro"

# Auth
ADMIN_TOKEN = ""         # required for management APIs; set a strong token
SCAN_SECRET"***"
SCAN_TOKEN_TTL = 86400   # 24h
BASE_URL = "http://192.168.1.105:8173"

# Warn rules
WARN_LEAD_DAYS = 7
CONTRACT_WARN_LEAD_DAYS = 30

# P2 integrations (leave empty to skip)
WECOM_WEBHOOK = ""       # e.g. https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx

# Scheduler
SCHEDULE_SYNC = False
SCHEDULE_SYNC_HOUR = 8
