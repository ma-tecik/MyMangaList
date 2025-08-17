from flask import Flask, jsonify, request
from views.api import api_bp
from views.misc import misc_bp
from utils.settings import first_run, get_settings, update_settings
import logging
import os

app = Flask(__name__)

# Configure logging
logging.getLogger().handlers.clear()
log_dir = "data/logs"
os.makedirs(log_dir, exist_ok=True)
file_handler = logging.FileHandler(os.path.join(log_dir, "app.log"))
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s in %(module)s.%(funcName)s: %(message)s",
                                            datefmt="%Y-%m-%d %H:%M:%S"))
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s in %(module)s.%(funcName)s: %(message)s",
                                               datefmt="%Y-%m-%d %H:%M:%S"))
app.logger.setLevel(logging.INFO)
app.logger.addHandler(console_handler)
app.logger.addHandler(file_handler)

if not os.path.isfile("data/mml.sqlite3"):
    os.makedirs("data/thumbnails", exist_ok=True)
    first_run()

get_settings(app)

# Blueprints
app.register_blueprint(api_bp)
app.register_blueprint(misc_bp)


@app.route("/api/v1/settings", methods=["PUT"])
def api_update_settings():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"result": "KO", "error": "Missing data"}), 400
        update_settings(data, app)
        return "", 204
    except Exception as e:
        app.logger.error(e)
        return jsonify({"result": "KO", "error": "Internal error"}), 500
