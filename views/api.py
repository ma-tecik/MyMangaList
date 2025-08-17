from flask import Blueprint, jsonify, current_app as app
from views.api_external import api_external_bp
from views.api_series import api_series_bp
from views.api_authors import api_authors_bp
from views.api_h import api_h_bp
import sqlite3

# Blueprints
api_bp = Blueprint("api", __name__, url_prefix="/api/v1")
api_bp.register_blueprint(api_external_bp)
api_bp.register_blueprint(api_series_bp)
api_bp.register_blueprint(api_authors_bp)
api_bp.register_blueprint(api_h_bp)


@api_bp.route("/ping", methods=["GET"])
def ping():
    return "pong", 200


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

        for k, v in {"Plan to Read": "plan_to_read", "Reading": "reading", "Completed": "completed",
                     "One-shot": "one_shots", "Dropped": "dropped", "On hold": "on_hold", "Ongoing": "ongoing"}.items():
            cursor.execute("SELECT COUNT(*) FROM series WHERE status = ?", (k,))
            data["series_by_status"][v] = cursor.fetchone()[0]

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
            "mu_username": db.get("mu_username"),
            "mu_password": bool(db.get("mu_password")),
            "dex_integration": bool(int(db.get("dex_integration", 0))),
            "dex_token": bool(db.get("dex_token")),
            "mal_integration": bool(int(db.get("mal_integration", 0))),
        }
        conn.close()
        return jsonify({"result": "OK", "data": data}), 200
    except Exception as e:
        app.logger.error(e)
        return jsonify({"result": "KO", "error": "Internal error"}), 500
