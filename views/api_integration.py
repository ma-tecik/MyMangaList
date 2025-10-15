from flask import Blueprint, jsonify, current_app as app
import utils.tasks as tasks
from typing import Any

integration_bp = Blueprint("api_integration", __name__, url_prefix="/integration")
integration_mu = Blueprint("api_integration_mu", __name__, url_prefix="/mu")
integration_dex = Blueprint("api_integration_dex", __name__, url_prefix="/dex")
integration_mal = Blueprint("api_integration_mal", __name__, url_prefix="/mal")
integration_bp.register_blueprint(integration_mu)
integration_bp.register_blueprint(integration_dex)
integration_bp.register_blueprint(integration_mal)


@integration_bp.before_request
def integration_check():
    if app.config.get("REDIS_DISABLED"):
        return jsonify({"result": "KO", "error": "Background tasks are disabled"}), 503
    return None


def _create_check(config_key, error_message):
    def check():
        config_value = app.config.get(config_key)
        if not config_value:
            return jsonify({"result": "KO", "error": error_message}), 503
        return None

    return check


integration_mu.before_request(_create_check("MU_INTEGRATION", "MU_INTEGRATION is disabled."))
integration_dex.before_request(_create_check("DEX_INTEGRATION", "DEX_INTEGRATION is disabled."))
integration_mal.before_request(_create_check("MAL_INTEGRATION", "MAL_INTEGRATION is disabled."))


@integration_bp.route("/tasks/<task_id>", methods=["GET"])
def task_status(task_id):
    try:
        celery = app.extensions["celery"]
        task = celery.AsyncResult(task_id)
        if task.state == "PENDING":
            return jsonify({"result": "OK", "state": task.state}), 200
        elif task.state == "SUCCESS":
            return jsonify({"result": "OK", "state": task.state, "task_result": str(task.result)}), 200
        elif task.state == "FAILURE":
            return jsonify({"result": "OK", "state": task.state, "error": str(task.result)}), 200
        else:
            return jsonify({"state": task.state}), 200
    except Exception as e:
        app.logger.error(e)
        return jsonify({"result": "KO", "error": "Internal server error"}), 500


def _handle_task(task_func: Any):
    try:
        task = task_func.delay(priority=1)
        return jsonify({"result": "OK", "task_id": task.id}), 202
    except Exception as e:
        app.logger.error(e)
        return jsonify({"result": "KO", "error": "Internal server error"}), 500


# MangaUpdates Integration endpoints
@integration_mu.route("/all", methods=["PUT"])
def mu_all():
    return _handle_task(tasks.mu_all_task)


@integration_mu.route("/update-ratings", methods=["PUT"])
def mu_ratings():
    return _handle_task(tasks.mu_update_ratings_task)


@integration_mu.route("/update-ongoing", methods=["PUT"])
def mu_ongoing():
    return _handle_task(tasks.mu_update_ongoing_task)


@integration_mu.route("/sync-lists", methods=["PUT"])
def mu_lists():
    return _handle_task(tasks.mu_sync_lists_task)


@integration_mu.route("/update-series", methods=["PUT"])
def mu_series():
    return _handle_task(tasks.mu_update_series_task)


# MangaDex Integration endpoints
@integration_dex.route("/all", methods=["PUT"])
def dex_all():
    return _handle_task(tasks.dex_all_task)


@integration_dex.route("/update-ratings", methods=["PUT"])
def dex_ratings():
    return _handle_task(tasks.dex_update_ratings_task)


@integration_dex.route("/sync-lists", methods=["PUT"])
def dex_lists():
    return _handle_task(tasks.dex_sync_lists_task)


@integration_dex.route("/fetch-ids", methods=["PUT"])
def dex_fetch_ids_api():
    return _handle_task(tasks.dex_fetch_ids_task)


# MyAnimeList Integration endpoints (TODO)
@integration_mal.route("", methods=["PUT"])
@integration_mal.route("/<n>", methods=["PUT"])
def mal(n=None):
    return jsonify({"result": "KO", "error": "Not implemented yet"}), 501