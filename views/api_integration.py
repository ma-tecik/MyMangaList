from flask import Blueprint, request, jsonify, current_app as app
from utils.mangaupdates_integration import mu_update_ratings, mu_updates_ongoing

integration_bp = Blueprint("api_integration", __name__, url_prefix="/integration")
integration_mu = Blueprint("api_integration_mu", __name__, url_prefix="/mu")
integration_dex = Blueprint("api_integration_dex", __name__, url_prefix="/dex")
integration_mal = Blueprint("api_integration_mal", __name__, url_prefix="/mal")
integration_bp.register_blueprint(integration_mu)
integration_bp.register_blueprint(integration_dex)
integration_bp.register_blueprint(integration_mal)


@integration_mu.route("/update-ratings", methods=["PUT"])
def mu_ratings():
    try:
        if not app.config["MU_INTEGRATION"]:
            return jsonify({"error": "MU_INTEGRATION is disabled"}), 400
        s = mu_update_ratings()
        if s:
            return "", 204
    except Exception as e:
        app.logger.error(e)
    return jsonify({"result": "KO", "error": "Internal error", "message": "Did you set up mu lists right?"}), 500

@integration_mu.route("/update-ongoing", methods=["PUT"])
def mu_ongoing():
    try:
        if not app.config["MU_INTEGRATION"]:
            return jsonify({"error": "MU_INTEGRATION is disabled"}), 400
        s = mu_updates_ongoing()
        if s:
            return "", 204
    except Exception as e:
        app.logger.error(e)
    return jsonify({"result": "KO", "error": "Internal error", "message": "Did you set up mu lists right?"}), 500

@integration_mu.route("/sync-lists", methods=["PUT"])
def mu_lists():
    pass

@integration_dex.route("", methods=["PUT"])
def dex():
    pass


@integration_mal.route("", methods=["PUT"])
def mal():
    pass
