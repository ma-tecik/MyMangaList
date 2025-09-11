from flask import Blueprint, jsonify, current_app as app
from utils.common_code import base36
from utils.mangaupdates_integration import mu_get_data_for_all, mu_update_ratings, mu_update_ongoing, mu_sync_lists, \
    mu_update_series
from utils.mangadex_integration import dex_start, dex_update_ratings, dex_sync_lists
import sqlite3

integration_bp = Blueprint("api_integration", __name__, url_prefix="/integration")
integration_mu = Blueprint("api_integration_mu", __name__, url_prefix="/mu")
integration_dex = Blueprint("api_integration_dex", __name__, url_prefix="/dex")
integration_mal = Blueprint("api_integration_mal", __name__, url_prefix="/mal")
integration_bp.register_blueprint(integration_mu)
integration_bp.register_blueprint(integration_dex)
integration_bp.register_blueprint(integration_mal)


# MangaUpdates Integration endpoints
@integration_mu.route("/update-ratings", methods=["PUT"])
def mu_ratings():
    try:
        if not app.config["MU_INTEGRATION"]:
            return jsonify({"error": "MU_INTEGRATION is disabled"}), 400
        data, _ = mu_get_data_for_all()
        if data:
            s = mu_update_ratings(data)
            if s:
                return "", 204
    except Exception as e:
        app.logger.error(e)
    return jsonify({"result": "KO", "error": "Internal error", "message": "Did you set up mu lists correctly?"}), 500


@integration_mu.route("/update-ongoing", methods=["PUT"])
def mu_ongoing():
    try:
        if not app.config["MU_INTEGRATION"]:
            return jsonify({"error": "MU_INTEGRATION is disabled"}), 400
        s = mu_update_ongoing()
        if s:
            return "", 204
    except Exception as e:
        app.logger.error(e)
    return jsonify({"result": "KO", "error": "Internal error", "message": "Did you set up mu lists correctly?"}), 500


@integration_mu.route("/sync-lists", methods=["PUT"])
def mu_lists():
    try:
        if not app.config["MU_INTEGRATION"]:
            return jsonify({"error": "MU_INTEGRATION is disabled"}), 400
        data, headers = mu_get_data_for_all()
        if data:
            s = mu_sync_lists(data, headers)
            if s:
                return "", 204
    except Exception as e:
        app.logger.error(e)
    return jsonify({"result": "KO", "error": "Internal error", "message": "Did you set up mu lists correctly?"}), 500


@integration_mu.route("/update-series", methods=["PUT"])
def mu_series():
    try:
        if not app.config["MU_INTEGRATION"]:
            return jsonify({"error": "MU_INTEGRATION is disabled"}), 400
        data, _ = mu_get_data_for_all()
        if not data:
            return jsonify(
                {"result": "KO", "error": "Internal error", "message": "Did you set up mu lists correctly?"}), 502

        db = {}
        for i in data:
            for m in data[i]:
                db[base36(m["record"]["id"])] = m["metadata"]["series"]["last_updated"]["timestamp"]

        conn = sqlite3.connect("data/mml.sqlite3")
        cursor = conn.cursor()
        cursor.execute("SELECT id_mu, timestamp_mu FROM series WHERE timestamp_mu IS NOT NULL and integration = 1")

        to_update = []
        for m in cursor.fetchall():
            if m[1] not in db or m[2] == db[m[1]]:
                continue
            to_update.append(m[1])

        if not to_update:
            conn.close()
            return "", 204

        s = mu_update_series(to_update, cursor)
        if s:
            conn.commit()
            conn.close()
            return "", 204
    except Exception as e:
        app.logger.error(e)
    return jsonify({"result": "KO", "error": "Internal error", "message": "Did you set up mu lists correctly?"}), 500


# MangaDex Integration endpoints
@integration_dex.route("/update-ratings", methods=["PUT"])
def dex_ratings():
    try:
        if not app.config["DEX_INTEGRATION"]:
            return jsonify({"error": "DEX_INTEGRATION is disabled"}), 400
        tokens, headers, lists = dex_start()
        if not headers:
            return jsonify({"error": "Failed to authenticate with Mangadex"}), 502
        s = dex_update_ratings(headers, lists)
        if s:
            return "", 204
    except Exception as e:
        app.logger.error(e)
    return jsonify({"result": "KO", "error": "Internal error"}), 500


@integration_dex.route("/sync-lists", methods=["PUT"])
def dex_lists():
    try:
        if not app.config["DEX_INTEGRATION"]:
            return jsonify({"error": "DEX_INTEGRATION is disabled"}), 400
        tokens, headers, lists = dex_start()
        if not headers:
            return jsonify({"error": "Failed to authenticate with Mangadex"}), 502
        forced_sync = True if app.config["DEX_INTEGRATION_FORCED"] == "1" else False
        s = dex_sync_lists(headers, lists, forced_sync)
        if s:
            return "", 204
    except Exception as e:
        app.logger.error(e)
    return jsonify({"result": "KO", "error": "Internal error"}), 500


# MyAnimeList Integration endpoints (TODO)
@integration_mal.route("", methods=["PUT"])
def mal():
    pass
