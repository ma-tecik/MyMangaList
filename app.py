from flask import Flask, request, session, jsonify, redirect, render_template
from views.api import api_bp
from views.site import site_bp
from views.misc import misc_bp
from utils.settings import first_run, first_run_detect_language, get_settings
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
    os.makedirs("data/backups", exist_ok=True)
    first_run()

if not os.path.isfile("data/detect_language.sqlite3"):
    first_run_detect_language()


get_settings(app)

if os.environ.get("MML_REDIS_DISABLED") == "true":
    app.config["REDIS_DISABLED"] = True
    from utils.scheduler import init_scheduler
    init_scheduler(app)


@app.before_request
def require_login():
    public = ["api.ping", "api.login", "site.login", "site.redoc", "site.openapi_spec"]
    public_files = ["/static/style.css", "/static/login.js"]

    if request.endpoint in public or request.path in public_files:
        return None
    if not session.get("logged_in"):
        if request.path.startswith("/api/"):
            if request.method == "HEAD":
                return "", 401
            return jsonify({"status": "KO", "error": "Authentication required"}), 401
        return redirect("/login")
    return None


# Blueprints
app.register_blueprint(api_bp)
app.register_blueprint(site_bp)
app.register_blueprint(misc_bp)

# Error Handlers
@app.errorhandler(404)
def not_found(error):
    if request.path.startswith("/api/"):
        if request.method == "HEAD":
            return "", 404
        return jsonify({"status": "KO", "error": "404 Not Found"}), 404
    return render_template("404.html"), 404

