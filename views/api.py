from flask import Blueprint
from views.api_external import external_bp
from views.api_series import series_bp

# Blueprints
api_bp = Blueprint("api", __name__, url_prefix="/api/v1")
api_bp.register_blueprint(external_bp)
api_bp.register_blueprint(series_bp)

@api_bp.route("/ping", methods=["GET"])
def ping():
    return "pong" , 200
