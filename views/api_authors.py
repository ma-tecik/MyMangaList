from flask import Blueprint, jsonify, request, current_app as app
from utils.common_code import valid_ids
from utils.db_authors import get_author, get_authors
import sqlite3

api_authors_bp = Blueprint("api_authors", __name__, url_prefix="/authors")


@api_authors_bp.route("", methods=["GET"])
def get_authors():
    try:
        page = request.args.get("page", 1, type=int)
        conn = sqlite3.connect("data/mml.sqlite3")
        cursor = conn.cursor()
        authors = get_authors(page, cursor)
        conn.close()
        if authors:
            return jsonify({"result": "OK", "page": page, "data": authors}), 200
    except Exception as e:
        app.logger.error(e)
    return jsonify({"result": "KO", "error": "Internal error"}), 500


@api_authors_bp.route("", methods=["POST"])
def create_author():
    try:
        name = request.get_json().get("name")
        if not name:
            return jsonify({"result": "KO", "error": "No name provided"}), 400
        conn = sqlite3.connect("data/mml.sqlite3")
        cursor = conn.cursor()
        cursor.execute(f"INSERT INTO authors (name) VALUES (?) RETURNING id", (name,))
        id_ = cursor.fetchone()[0]
        conn.commit()
        conn.close()
        r, s = get_author(id_, cursor)
        if s == 200:
            return jsonify({"result": "OK", "data": r}), 201
    except Exception as e:
        app.logger.error(e)
    return jsonify({"result": "KO", "error": "Internal error"}), 500


@api_authors_bp.route("/search", methods=["GET"])
def search_authors():
    try:
        name = request.args.get("name")
        conn = sqlite3.connect("data/mml.sqlite3")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM authors WHERE name = ?", (name,))
        rows = cursor.fetchall()
        conn.close()
        authors = []
        for a in rows:
            author_data = {
                "id": a["id"],
                "ids": {
                    "mu": a["id_mu"],
                    "dex": a["id_dex"],
                    "mal": a["id_mal"],
                },
                "name": a["name"],
            }
            authors.append(author_data)
        if not authors:
            return jsonify({"result": "KO", "error": "No author found"}), 404
        return jsonify({"result": "OK", "data": authors}), 200
    except Exception as e:
        app.logger.error(e)
        return jsonify({"result": "KO", "error": "Internal error"}), 500


@api_authors_bp.route("/<int:id_>", methods=["GET"])
def get_authors_by_id(id_):
    try:
        conn = sqlite3.connect("data/mml.sqlite3")
        cursor = conn.cursor()

        r, s = get_author(id_, cursor)
        conn.close()
        if s != 200:
            return jsonify(r), s
        author = r
        return jsonify({"result": "OK", "data": author}), 200
    except Exception as e:
        app.logger.error(e)
        return jsonify({"result": "KO", "error": "Internal error"}), 500


@api_authors_bp.route("/<int:id_>", methods=["PATCH"])
def update_author(id_):
    try:
        data = request.get_json()
        if not data:
            return jsonify({"result": "KO", "error": "No data provided"}), 400

        conn = sqlite3.connect("data/mml.sqlite3")
        cursor = conn.cursor()
        r, s = get_author(id_, cursor)
        if s != 200:
            return jsonify(r), s

        ids = None
        if "ids" in data:
            if not (ids := valid_ids(data.get("ids"), reduced=True)):
                conn.close()
                return jsonify({"result": "KO", "error": "IDs not valid"}), 400
            for key, value in ids.items():
                cursor.execute(f"SELECT id FROM authors WHERE id_{key} = ? AND id != ?", (value, id_))
                if cursor.fetchone():
                    conn.close()
                    return jsonify({"result": "KO", "error": f"Author with {key} ID {value} already exists"}), 409

        update_fields = []
        update_params = []

        if ids:
            id_fields = ["mu", "dex", "mal"]
            for field in id_fields:
                if field in ids:
                    update_fields.append(f"id_{field} = ?")
                    update_params.append(ids[field])

        if name := data.get("name"):
            update_fields.append("name = ?")
            update_params.append(name)

        if update_fields:
            query = f"UPDATE authors SET {', '.join(update_fields)} WHERE id = ?"
            update_params.append(id_)
            cursor.execute(query, update_params)

        r, s = get_author(id_, cursor)
        if s != 200:
            conn.close()
            return jsonify({"result": "KO", "error": "Internal error"}), 500

        conn.commit()
        conn.close()

        return jsonify({"result": "OK", "data": r}), 200

    except Exception as e:
        app.logger.error(e)
        return jsonify({"result": "KO", "error": "Internal error"}), 500


@api_authors_bp.route("/merge", methods=["POST"])
def merge_authors():
    try:
        ids = request.args.get("ids", "").split(",") if request.args.get("ids") else []
        if len(ids) < 2:
            return jsonify({"result": "KO", "error": "You must provide at least 2 internal IDs"}), 400
        ids = [int(i) for i in ids]
        ids.sort()
        id_ = ids[0]
        conn = sqlite3.connect("data/mml.sqlite3")
        cursor = conn.cursor()

        external_ids = {}
        for i in ids:
            r, s = get_author(i, cursor)
            if s == 404:
                conn.close()
                return jsonify({"result": "KO", "error": f"No author found for id {i}"}), 404
            for k, v in r["ids"].items():
                if v is None:
                    continue
                if k in external_ids and external_ids[k] != v:
                    conn.close()
                    return jsonify({"result": "KO", "error": "Conflict in external IDs"}), 409
                external_ids[k] = v

        series_to_merge = []
        for i in ids[1:]:
            cursor.execute("SELECT series_id, author_type FROM series_authors WHERE author_id = ?", (i,))
            for r in cursor.fetchall():
                series_to_merge.append((r[0], id_, r[1]))
            cursor.execute("DELETE FROM authors WHERE id = ?", (i,))

        for k, v in external_ids.items():
            cursor.execute(f"UPDATE authors SET id_{k} = ? WHERE id = ?", (v, id_))
        cursor.executemany("INSERT INTO series_authors VALUES (?, ?, ?)", series_to_merge)

        r, s = get_author(id_, cursor)
        if s != 200:
            conn.close()
            return jsonify({"result": "KO", "error": "Internal error"}), 500

        conn.commit()
        conn.close()
        return jsonify({"result": "OK", "data": r}), 200

    except Exception as e:
        app.logger.error(e)
        return jsonify({"result": "KO", "error": "Internal error"}), 500
