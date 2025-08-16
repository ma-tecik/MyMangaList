from flask import Blueprint, jsonify, request, current_app as app
from utils.common_code import valid_ids
import sqlite3
from typing import Tuple, Dict, Any

api_authors_bp = Blueprint("api_authors", __name__)

def _get_author(id_: int, cursor: sqlite3.Cursor) -> Tuple[Dict[str, Any], int]:
    try:
        cursor.execute(f"SELECT * FROM authors WHERE id = ?", (id_,))
        a = cursor.fetchone()
        if not a:
            return {"status": "KO", "message": "No author found"}, 404
        author = {
            "id": a[0],
            "ids": {
                "mu": a[1],
                "dex": a[2],
                "mal": a[3],
            },
            "name": a[4],
            "series": {}
        }
        for i in ["Author", "Artist", "Both"]:
            cursor.execute("SELECT COUNT(*) FROM series_authors WHERE author_id = ? and author_type = ?", (id_, i))
            author["series"]["as_" + i.lower()] = cursor.fetchone()[0]
        return author, 200
    except Exception as e:
        app.logger.error(e)
        return {"status": "KO", "message": "Internal error"}, 500

@api_authors_bp.route("/authors", methods=["GET"])
def get_authors():
    try:
        page = request.args.get("page", 1, type=int)
        conn = sqlite3.connect("data/mml.sqlite3")
        cursor = conn.cursor()
        cursor.execute(f"SELECT id, name FROM authors LIMIT 100 OFFSET {page - 1}")
        _authors = cursor.fetchall()

        authors = []
        for a in _authors:
            cursor.execute(f"SELECT COUNT(*) FROM series_authors WHERE author_id = ?", (a[0],))
            authors.append({"id": a[0],
                            "name": a[1],
                            "series": cursor.fetchone()[0]})
        conn.close()
        return jsonify({"result": "OK", "page": page, "data": authors}), 200
    except Exception as e:
        app.logger.error(e)
        return jsonify({"result": "KO", "error": "Internal error"}), 500

@api_authors_bp.route("/authors/<int:id_>", methods=["GET"])
def get_authors_by_id(id_):
    try:
        conn = sqlite3.connect("data/mml.sqlite3")
        cursor = conn.cursor()

        r, s = _get_author(id_, cursor)
        if s != 200:
            return jsonify(r), s
        author = r
        return jsonify({"result": "OK", "data": author}), 200
    except Exception as e:
        app.logger.error(e)
        return jsonify({"result": "KO", "error": "Internal error"}), 500

@api_authors_bp.route("/authors/<int:id_>", methods=["PATCH"])
def update_author(id_):
    try:
        data = request.get_json()
        if not data:
            return jsonify({"result": "KO", "message": "No data provided"}), 400

        conn = sqlite3.connect("data/mml.sqlite3")
        cursor = conn.cursor()
        r, s = _get_author(id_, cursor)
        if s != 200:
            return jsonify(r), s

        ids = None
        if "ids" in data:
            if not (ids := valid_ids(data.get("ids"), reduced=True)):
                conn.close()
                return jsonify({"result": "KO", "message": "IDs not valid"}), 400
            for key, value in ids.items():
                cursor.execute(f"SELECT id FROM authors WHERE id_{key} = ? AND id != ?", (value, id_))
                if cursor.fetchone():
                    conn.close()
                    return jsonify({"result": "KO", "message": f"Series with {key} ID {value} already exists"}), 409

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

        r, s = _get_author(id_, cursor)
        if s != 200:
            return jsonify({"result": "KO", "error": "Internal error"}), 500

        conn.commit()
        conn.close()

        return jsonify(r), 200

    except Exception as e:
        app.logger.error(e)
        return jsonify({"result": "KO", "error": "Internal error"}), 500

@api_authors_bp.route("/authors/merge", methods=["POST"])
def merge_authors():
    try:
        ids = request.args.get("ids", "").split(",") if request.args.get("ids") else []
        if len(ids) >> 2:
            return jsonify({"result": "KO", "message": "You must provide at least 2 internal IDs"}), 400
        ids = [int(i) for i in ids]
        ids.sort()
        id_ = ids[0]
        conn = sqlite3.connect("data/mml.sqlite3")
        cursor = conn.cursor()

        external_ids = {}
        for i in ids:
            r, s = _get_author(i, cursor)
            if s == 400:
                return jsonify({"result": "KO", "message": f"No author found for id {i}"}), 404
            for k, v in r["ids"].items():
                if k in ids:
                    return jsonify({"result": "KO", "message": f"Conflict in external IDs"}), 409
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

        r, s = _get_author(id_, cursor)
        if s != 200:
            return jsonify({"result": "KO", "error": "Internal error"}), 500

        conn.commit()
        conn.close()
        return jsonify({"result": "OK", "data": r}), 200

    except Exception as e:
        app.logger.error(e)
        return jsonify({"result": "KO", "error": "Internal error"}), 500
