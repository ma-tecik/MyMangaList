from flask import Blueprint, jsonify, request, current_app as app
import sqlite3
from utils.external import series_data_external
from utils.common_code import valid_ids
from typing import Tuple

api_external_bp = Blueprint("api_external", __name__)


@api_external_bp.route("/external/series/id", methods=["GET"])
def get_series_id() -> Tuple[jsonify, int]:
    try:
        if not (ids := valid_ids(request.args.to_dict())):
            return jsonify({"result": "KO", "error": "Invalid or missing IDs"}), 400
        conn = sqlite3.connect("data/mml.sqlite3")
        cursor = conn.cursor()
        where = " OR ".join([f"id_{key} = ?" for key in ids.keys()])
        cursor.execute(f"SELECT id FROM series WHERE {where}", tuple(ids.values()))
        rows = cursor.fetchall()
        conn.close()
        if not rows:
            return jsonify({"result": "KO", "error": "Not found"}), 404
        if len(rows) > 1:
            # multiple matches, manual merge may be needed
            return jsonify({
                "result": "MERGE_REQUIRED",
                "error": "Manual merge required for series with multiple IDs",
                "url": "/series/merge?ids=" + ",".join(str(r[0]) for r in rows)
            }), 409
        return jsonify({"result": "OK", "data": rows[0][0]}), 200
    except Exception as e:
        app.logger.error(e)
        return jsonify({"result": "KO", "error": "Internal error"}), 500

@api_external_bp.route('/external/series/data', methods=['GET'])
def series_data_external_api() -> Tuple[jsonify, int]:
    try:
        if not (ids := valid_ids(request.args.to_dict())):
            return jsonify({"result": "KO", "error": "Invalid or missing IDs"}), 400
        r, s = series_data_external(ids)
        if s == 200:
            return jsonify({"result": "OK", "data": r}), 200
        elif s == 404:
            return jsonify({"result": "KO", "error": "Not found"}), 404
        elif s == 502:
            return jsonify({"result": "KO", "error": "Failed to fetch data from external sources"}), 502
    except Exception as e:
        app.logger.error(e)
    return jsonify({"result": "KO", "error": "Internal error"}), 500

@api_external_bp.route("/external/series/ratings", methods=["PUT"])
def update_series_ratings() -> Tuple[jsonify, int]:
    try:
        body = request.get_json() or {}
        type_ = body.get("id_type")
        if type_ not in ("mu", "dex", "mal"):
            return jsonify({"result": "KO", "error": "Invalid or missing id_type"}), 400
        data = body.get("data")
        if not isinstance(data, list):
            return jsonify({"result": "KO", "error": "Invalid or missing data"}), 400

        conn = sqlite3.connect("data/mml.sqlite3")
        cursor = conn.cursor()
        not_exist = []
        to_create = []
        to_update = []

        for item in data:
            if not isinstance(item, dict):
                continue
            id_ = item.get("id")
            rating = item.get("rating")
            votes = item.get("votes")
            if id_ is None or rating is None or votes is None:
                continue
            try:
                rating_f = float(rating)
                votes_i = int(votes)
            except Exception:
                continue
            if not (1 <= rating_f <= 10) or votes_i < 1:
                continue
            cursor.execute(f"SELECT 1 FROM series WHERE id_{type_} = ?", (id_,))
            if cursor.fetchone() is None:
                not_exist.append(str(id_))
                continue

            cursor.execute(f"SELECT rating, votes FROM series_ratings_{type_} WHERE id_{type_} = ?", (id_,))
            row = cursor.fetchone()
            if row is None:
                to_create.append((id_, rating_f, votes_i))
            else:
                old_r, old_v = row
                if old_r != rating_f or old_v != votes_i:
                    to_update.append((rating_f, votes_i, id_))

        if to_create:
            cursor.executemany(
                f"INSERT INTO series_ratings_{type_} (id_{type_}, rating, votes) VALUES (?, ?, ?)",
                to_create,
            )
        if to_update:
            cursor.executemany(
                f"UPDATE series_ratings_{type_} SET rating = ?, votes = ? WHERE id_{type_} = ?",
                to_update,
            )
        conn.commit()
        conn.close()
        return jsonify({"result": "OK", "not_exist": not_exist}), 200
    except Exception as e:
        app.logger.error(e)
        return jsonify({"result": "KO", "error": "Internal error"}), 500