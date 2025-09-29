from flask import Blueprint, render_template, send_from_directory, request, redirect, session, current_app as app
from utils.db_authors import get_author, get_authors
import sqlite3

site_bp = Blueprint("site", __name__)


@site_bp.route("/login")
def login():
    return render_template("login.html")


@site_bp.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@site_bp.route("/")
def index():
    try:
        return render_template("index.html")  # TODO: May be change
    except Exception as e:
        app.logger.error(f"Failed to return index: {e}")
        return "Internal Server Error", 500


@site_bp.route("/series/<status>")
def series_list(status):
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
            return render_template("404.html"), 404
        return render_template("list.html", page_title=status)
    except Exception as e:
        app.logger.error(f"Failed to return series list page: {e}")
        return "Internal Server Error", 500


@site_bp.route("/series/<int:id_>")
def series_redirect(id_):
    try:
        conn = sqlite3.connect("data/mml.sqlite3")
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM series WHERE id = ?", (id_,))
        status = cursor.fetchone()
        if status:
            return redirect("/series/status/id_", 302)
        return render_template("404-series.html"), 404
    except Exception as e:
        app.logger.error(f"Error in series_redirect: {e}")
        return "Internal Server Error", 500


@site_bp.route("/series/<status>/<int:series_id>")
def series(status, series_id):
    try:
        allowed_status = ("plan-to", "reading", "completed", "one-shots", "on-hold", "dropped", "ongoing")
        if status not in allowed_status:
            return render_template("404.html"), 404

        conn = sqlite3.connect("data/mml.sqlite3")
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM series WHERE id = ?", (series_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return render_template("404-series.html"), 404
        elif row != status:
            return redirect(f"/series/{row}/{series_id}", 302)
        return render_template("series.html")
    except Exception as e:
        app.logger.error(f"Failed to return series with id {series_id} page: {e}")
        return "Internal Server Error", 500


@site_bp.route("/series/add")
def series_add():
    try:
        return render_template("series-add.html")
    except Exception as e:
        app.logger.error(f"Failed to return series add page: {e}")
        return "Internal Server Error", 500


@site_bp.route("/series/merge")
def series_merge():
    try:
        return render_template("series-merge.html")
    except Exception as e:
        app.logger.error(f"Failed to return merge authors page: {e}")
        return "Internal Server Error", 500


@site_bp.route("/authors")
def authors():
    try:
        page = int(request.args.get("page", 1))
        conn = sqlite3.connect("data/mml.sqlite3")
        cursor = conn.cursor()
        data = get_authors(page, cursor)
        conn.close()
        if data:
            return render_template("authors.html", data=data)
    except Exception as e:
        app.logger.error(f"Failed to return authors page: {e}")
    return "Internal Server Error", 500


@site_bp.route("/authors/<int:author_id>")
def author(author_id):
    try:
        conn = sqlite3.connect("data/mml.sqlite3")
        cursor = conn.cursor()
        data, s = get_author(author_id, cursor)
        conn.close()
        if s == 404:
            return render_template("404.html"), 404
        if s == 200:
            return render_template("author.html", data=data)
    except Exception as e:
        app.logger.error(f"Failed to return author page: {e}")
    return "Internal Server Error", 500


@site_bp.route("/authors/add")
def add_author():
    try:
        return render_template("authors-add.html")
    except Exception as e:
        app.logger.error(f"Failed to return add author page: {e}")
        return "Internal Server Error", 500


@site_bp.route("/authors/merge")
def merge_authors():
    try:
        return render_template("authors-merge.html")
    except Exception as e:
        app.logger.error(f"Failed to return merge authors page: {e}")
        return "Internal Server Error", 500


@site_bp.route("/h")
def h():
    try:
        return render_template("h.html")
    except Exception as e:
        return "Internal Server Error", 500


@site_bp.route("/settings")
def settings():
    try:
        return render_template("settings.html")
    except Exception as e:
        app.logger.error(f"Failed to return settings page: {e}")
        return "Internal Server Error", 500


@site_bp.route("/integration")
def integration():
    try:
        return render_template("integration.html")
    except Exception as e:
        app.logger.error(f"Failed to return integration page: {e}")
        return "Internal Server Error", 500


@site_bp.route("/api", methods=["GET"])
def redoc():
    try:
        return send_from_directory("static", "redoc.html")
    except Exception as e:
        app.logger.error(f"Failed to return redoc.html, {e}")
        return "Internal Server Error", 500


@site_bp.route("/api/openapi.yaml", methods=["GET"])
def openapi_spec():
    try:
        return send_from_directory("static", "openapi.yaml")
    except Exception as e:
        app.logger.error(f"Failed to return openapi.yaml, {e}")
        return "Internal Server Error", 500
