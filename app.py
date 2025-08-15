from flask import Flask, render_template, jsonify
from views.api import api_bp
from views.misc import misc_bp
import logging
import os
import json

app = Flask(__name__, instance_relative_config=True)
app.config.from_file("config.json", load=json.load)

# Normalize config
if not app.config.get("MAIN_SERIES_RATING") or app.config["MAIN_SERIES_RATING"] not in ["mu", "dex", "mal"]:
    app.config["MAIN_SERIES_RATING"] = "mu"
if not app.config.get("TITLE_LANGUAGES"):
    app.config["TITLE_LANGUAGES"] = []
if not app.config.get("SECRET_KEY"):
    raise ValueError("SECRET_KEY must be set in config.json")

# Configure logging
logging.getLogger().handlers.clear()
log_dir = os.path.join(app.instance_path, "logs")
os.makedirs(log_dir, exist_ok=True)
file_handler = logging.FileHandler(os.path.join(log_dir, "app.log"))
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s in %(module)s.%(funcName)s: %(message)s", datefmt = "%Y-%m-%d %H:%M:%S"))
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s in %(module)s.%(funcName)s: %(message)s", datefmt = "%Y-%m-%d %H:%M:%S"))
app.logger.setLevel(logging.INFO)
app.logger.addHandler(console_handler)
app.logger.addHandler(file_handler)

# Blueprints
app.register_blueprint(api_bp)
app.register_blueprint(misc_bp)


# @app.route("/", methods=["GET"])
# def index():
#     return "", 301, {"Location": "/series/list/plan-to"}
# @app.route("/series/list/<path>", methods=["GET"])
# def series(path):
#     try:
#         if path not in {"plan-to", "reading", "completed", "one-shots", "dropped", "ongoing"}:
#             return {"result": "KO", "error": "Invalid path"}, 404
#         titles = {
#             "plan-to": "Plan to Read",
#             "reading": "Reading",
#             "completed": "Completed",
#             "one-shots": "One-shots",
#             "dropped": "Dropped",
#             "ongoing": "Ongoing",
#         }
#         page_title = titles.get(path)
#         return render_template(
#             "list.html",
#             page_title=page_title,
#             page=path,
#         ), 200
#     except Exception as e:
#         app.logger.error(e)
#         return jsonify({"result": "KO", "error": "Internal server error"}), 500