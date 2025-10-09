from flask import blueprints, redirect, current_app as app
import sqlite3

redirect_bp = blueprints.Blueprint("redirects", __name__)


# MangaUpdates

@redirect_bp.route("/series/<mu_id>/<mu_title>")
def redirect_mu(mu_id, mu_title):
    try:
        conn = sqlite3.connect("data/mml.sqlite3")
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM series WHERE id_mu = ?", (mu_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return redirect(f"https://www.mangaupdates.com/series/{mu_id}/{mu_title}", 302)
        return redirect(f"/series/{row[0]}", 301)
    except Exception as e:
        app.logger.error(f"Failed to redirect series with id_mu {mu_id} page: {e}")
        return "Internal Server Error", 500


@redirect_bp.route("/group/<mu_id>/<mu_group>")
def redirect_group(mu_id, mu_group):
    return redirect(f"https://www.mangaupdates.com/group/1{mu_id}/{mu_group}", 301)


@redirect_bp.route("/author/<mu_id>/<mu_name>")
def redirect_author(mu_id, mu_name):
    try:
        conn = sqlite3.connect("data/mml.sqlite3")
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM authors WHERE id_mu = ?", (mu_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return redirect(f"https://www.mangaupdates.com/author/{mu_id}/{mu_name}", 302)
        return redirect(f"/authors/{row[0]}", 301)
    except Exception as e:
        app.logger.error(f"Failed to redirect author with id_mu {mu_id} page: {e}")
        return "Internal Server Error", 500


# MangaDex

@redirect_bp.route("/title/<dex_id>")
def redirect_dex(dex_id):
    try:
        conn = sqlite3.connect("data/mml.sqlite3")
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM series WHERE id_dex = ?", (dex_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return redirect(f"https://mangadex.org/title/{dex_id}", 302)
        return redirect(f"/series/{row[0]}", 301)
    except Exception as e:
        app.logger.error(f"Failed to redirect series with id_dex {dex_id} page: {e}")
        return "Internal Server Error", 500
