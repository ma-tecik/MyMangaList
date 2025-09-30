from flask import Blueprint, jsonify, request, session, current_app as app
from views.api_external import api_external_bp
from views.api_series import api_series_bp
from views.api_authors import api_authors_bp
from views.api_h import api_h_bp
from views.api_integration import integration_bp
from utils.settings import update_settings
import sqlite3

# Blueprints
api_bp = Blueprint("api", __name__, url_prefix="/api/v1")
api_bp.register_blueprint(api_external_bp)
api_bp.register_blueprint(api_series_bp)
api_bp.register_blueprint(api_authors_bp)
api_bp.register_blueprint(api_h_bp)
api_bp.register_blueprint(integration_bp)


@api_bp.route("/ping", methods=["GET"])
def ping():
    return "pong", 200


@api_bp.route("/login", methods=["POST"])
def login():
    try:
        password = request.form.get("password")
        if password == app.config["PASSWORD"]:
            session["logged_in"] = True
            session.permanent = True
            return jsonify({"result": "OK"}), 200
        else:
            return jsonify({"result": "KO", "error": "Invalid password"}), 401
    except Exception as e:
        app.logger.error(e)
    return jsonify({"result": "KO", "error": "Internal error"}), 500

@api_bp.route("/auth", methods=["HEAD"])
def auth_check():
    try:
        return "", 204
    except Exception as e:
        app.logger.error(e)
    return "", 500

@api_bp.route("/status", methods=["GET"])
def status():
    try:
        conn = sqlite3.connect("data/mml.sqlite3")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        data = {
            "series_total": 0,
            "series_by_status": {},
            "series_by_type": {},
            "authors": 0,
            "h": 0,
            "mu_integration": False,
            "dex_integration": False,
            "mal_integration": False,
        }

        cursor.execute("SELECT COUNT(*) FROM series")
        data["series_total"] = cursor.fetchone()[0]

        for i in ("plan-to", "reading", "completed", "one-shots", "dropped", "on-hold", "ongoing"):
            cursor.execute("SELECT COUNT(*) FROM series WHERE status = ?", (i,))
            data["series_by_status"][i.lower()] = cursor.fetchone()[0]

        for i in ("Manga", "Manhwa", "Manhua", "OEL", "Vietnamese", "Malaysian", "Indonesian",
                  "Novel", "Artbook", "Other"):
            cursor.execute("SELECT COUNT(*) FROM series WHERE type = ?", (i,))
            data["series_by_type"][i.lower()] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM authors")
        data["authors"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM nhentai_ids")
        c = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM schale_ids")
        data["h"] = c + cursor.fetchone()[0]

        data["mu_integration"] = bool(app.config.get("MU_INTEGRATION"))
        data["dex_integration"] = bool(app.config.get("DEX_INTEGRATION"))
        data["mal_integration"] = bool(app.config.get("MAL_INTEGRATION"))

        conn.close()
        return jsonify({"result": "OK", "data": data}), 200

    except Exception as e:
        app.logger.error(e)
        return jsonify({"result": "KO", "error": "Internal error"}), 500


@api_bp.route("/settings", methods=["GET"])
def get_settings():
    try:
        conn = sqlite3.connect("data/mml.sqlite3")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM settings")
        db = {r[0]: r[1] for r in cursor.fetchall()}
        data = {
            "main_rating": db["main_rating"],
            "title_languages": db["title_languages"],
            "mu_integration": bool(int(db.get("mu_integration", 0))),
            "mu_automation": bool(int(db.get("mu_automation", 0))),
            "mu_username": db.get("mu_username"),
            "mu_password": bool(db.get("mu_password")),
            "mu_lists": {
                "plan-to": int(db.get("mu_list_plan-to")),
                "reading": int(db.get("mu_list_reading")),
                "completed": int(db.get("mu_list_completed")),
                "one-shots": int(db.get("mu_list_one-shots")),
                "dropped": int(db.get("mu_list_dropped")),
                "on-hold": int(db.get("mu_list_on-hold")),
                "ongoing": int(db.get("mu_list_ongoing")),
            },
            "dex_fetch_ids": bool(int(db.get("dex_fetch_ids", 0))),
            "dex_integration": bool(int(db.get("dex_integration", 0))),
            "dex_integration_forced": bool(int(db.get("dex_integration_forced", 0))),
            "dex_automation": bool(int(db.get("dex_automation", 0))),
            "dex_username": db.get("dex_username"),
            "dex_password": bool(db.get("dex_password")),
            "dex_client_id": db.get("dex_token"),
            "dex_secret": bool(db.get("dex_secret")),
            "mal_integration": bool(int(db.get("mal_integration", 0))),
            "mal_automation": bool(int(db.get("mal_automation", 0))),
            "mal_client_id": db.get("mal_client_id"),
        }
        conn.close()
        return jsonify({"result": "OK", "data": data}), 200
    except Exception as e:
        app.logger.error(e)
        return jsonify({"result": "KO", "error": "Internal error"}), 500


@api_bp.route("/settings", methods=["PUT"])
def api_update_settings():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"result": "KO", "error": "Missing data"}), 400
        update_settings(data)
        return "", 204
    except Exception as e:
        app.logger.error(e)
        return jsonify({"result": "KO", "error": "Internal error"}), 500
