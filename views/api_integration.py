from flask import Blueprint, jsonify, current_app as app
from utils.common_code import base36
from utils.mangaupdates_integration import mu_get_data_for_all, mu_update_ratings, mu_update_ongoing, mu_sync_lists, \
    mu_update_series
from utils.mangadex_integration import dex_start, dex_update_ratings, dex_sync_lists, dex_sync_lists_forced
from time import sleep

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
        if s == 2:
            sleep(5)
            mu_lists()
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

        s = mu_update_series(data)
        if s:
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
        to_update = dex_sync_lists(lists)
        if to_update and app.config["DEX_INTEGRATION_FORCED"] == "1":
            dex_sync_lists_forced(tokens, headers, to_update)
        return "", 204
    except Exception as e:
        app.logger.error(e)
    return jsonify({"result": "KO", "error": "Internal error"}), 500


# MyAnimeList Integration endpoints (TODO)
@integration_mal.route("", methods=["PUT"])
def mal():
    pass
