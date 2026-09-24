# -*- coding: utf-8 -*-
"""Flask application factory for the Electricity Fee Management System.

Serves the React SPA from frontend/dist in production and all /api blueprints.
Dev mode: run `npm run dev` (Vite proxies /api to this server on PORT).
"""
import os

from flask import Flask, request, send_from_directory, jsonify, abort

from config import Config
from backend.extensions import db


def create_app():
    app = Flask(__name__, static_folder=None)
    app.config["SECRET_KEY"] = Config.SECRET_KEY
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///%s" % os.path.abspath(Config.DB_PATH)
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024  # 20MB uploads
    db.init_app(app)

    Config.ensure_dirs()
    with app.app_context():
        db.create_all()

    # ---- Register API blueprints ----
    from backend.api.dashboard_api import dashboard_api
    from backend.api.import_api import import_api
    from backend.api.board_api import board_api
    from backend.api.expense_api import expense_api
    from backend.api.scan_api import scan_api
    from backend.api.writeback_api import writeback_api

    for bp in (dashboard_api, import_api, board_api, expense_api, scan_api, writeback_api):
        app.register_blueprint(bp)

    @app.route("/api/health", methods=["GET"])
    def health():
        return jsonify({"ok": True, "service": "elec-fee-dashboard", "config": Config.summary()})

    # ---- SPA fallback (serve built frontend) ----
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_spa(path):
        if request.path.startswith("/api"):
            abort(404)
        dist = os.path.abspath(Config.FRONTEND_DIST)
        if path:
            candidate = os.path.join(dist, path)
            if os.path.isfile(candidate):
                return send_from_directory(dist, path)
        index = os.path.join(dist, "index.html")
        if os.path.isfile(index):
            return send_from_directory(dist, "index.html")
        return ("Frontend not built. Run `cd frontend && npm install && npm run build`, "
                "or use `npm run dev` for development.", 200)

    # ---- Optional daily sync scheduler ----
    if Config.SCHEDULE_SYNC:
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            from backend.sync.run_sync import run_sync
            sched = BackgroundScheduler()
            sched.add_job(
                lambda: run_sync(),
                "cron", hour=Config.SCHEDULE_SYNC_HOUR, minute=0,
            )
            sched.start()
            print("[scheduler] daily sync scheduled at %02d:00" % Config.SCHEDULE_SYNC_HOUR)
        except Exception as exc:
            print("[scheduler] disabled: %s" % exc)

    return app
