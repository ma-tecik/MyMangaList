from flask import Flask, render_template, jsonify, request
from views.api import api_bp
from views.misc import misc_bp
from utils.settings import get_settings
import logging
import sqlite3
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

get_settings(app)

# Blueprints
app.register_blueprint(api_bp)
app.register_blueprint(misc_bp)


@app.route("/api/v1/settings", methods=["PUT"])
def set_settings():
    try:
        data = request.get_json()
        conn = sqlite3.connect("data/mml.sqlite3")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM settings")
        db = {i[0]: i[1] for i in cursor.fetchall()}

        params_to_add = []
        params_to_update = []
        for k, v in data.items():
            if k in db:
                if v == db[k]:
                    continue
                params_to_update.append((k, v))
            else:
                params_to_add.append((k, v))
            app.config[k] = v

        if params_to_add:
            cursor.executemany("INSERT INTO settings VALUES (?, ?)", params_to_add)
            conn.commit()
        if params_to_update:
            cursor.executemany("UPDATE settings SET value = ? WHERE key = ? ", params_to_update)
            conn.commit()
        conn.close()
        return "", 204
    except Exception as e:
        app.logger.error(e)
        return jsonify({"result": "ko", "message": "Internal error"}), 500

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
#         return jsonify({"result": "KO", "error": "Internal error"}), 500
