from flask import Blueprint, render_template, send_from_directory, current_app as app

site_bp = Blueprint("site", __name__)


@site_bp.route("/")
def index():
    try:
        return render_template("index.html") # TODO: May be change
    except Exception as e:
        app.logger.error(f"Error in list_plan_to: {e}")
        return "Internal Server Error", 500

@site_bp.route("/list/<status>")
def list_plan_to(status):
    try:
        status_map = {"plan-to": "Plan to Read",
                      "reading": "Reading",
                      "completed": "Completed",
                      "one-shots": "One-shots",
                      "on-hold": "On Hold",
                      "dropped": "Dropped",
                      "ongoing": "Ongoing"}

        status = status_map.get(status, None)
        if not status:
            return render_template("list-404.html"), 404  # TODO: May be change
        return render_template("list.html", page_title=status)
    except Exception as e:
        app.logger.error(f"Error in list_plan_to: {e}")
        return "Internal Server Error", 500


@site_bp.route("/list/reading")
def list_reading():
    return render_template("list.html", page_title="Reading")


@site_bp.route("/api", methods=["GET"])
def redoc():
    try:
        return send_from_directory("static", "redoc-static.html")
    except Exception as e:
        app.logger.error(f"Failed to return redoc-static.html, {e}")
        return "Internal Server Error", 500


@site_bp.route("/api/openapi.yaml", methods=["GET"])
def openapi_spec():
    try:
        return send_from_directory("static", "redoc-static.html")
    except Exception as e:
        app.logger.error(f"Failed to return openapi.yaml, {e}")
        return "Internal Server Error", 500
