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
        cursor.execute("SELECT * FROM series WHERE " + " OR ".join([f"{key} = ?" for key in ids.keys()]), tuple(ids.values()))
        rows = cursor.fetchall()
        conn.close()
        if not rows:
            return jsonify({"result": "KO", "error": "No series found"}), 404
        if len(rows) > 1:
            return jsonify({"result": "MERGE_REQUIRED", "error": "Merge required for series with multiple IDs", "merge_url": "/series/merge?" + "&".join(str(i[0]) for i in rows)}), 409
        return jsonify({"result": "OK", "series": rows[0]}), 200
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
            return jsonify({"result": "KO", "error": "No data found for the provided IDs"}), 404
        elif s == 502:
            return jsonify({"result": "KO", "error": "Failed to fetch data from external sources"}), 502
    except Exception as e:
        app.logger.error(e)
    return jsonify({"result": "KO", "error": "Internal error"}), 500

@api_external_bp.route("/external/series/ratings", methods=["PUT"])
def update_series_ratings() -> Tuple[jsonify, int]:
    try:
        data = request.get_json()
        if type_ := data.get("id_type") not in ("mu", "dex", "mal"):
            return jsonify({"result": "KO", "error": "Invalid or missing id_type"}), 400
        if not data or not isinstance(data, dict):
            return jsonify({"result": "KO", "error": "Invalid or missing data"}), 400

        conn = sqlite3.connect("data/mml.sqlite3")
        cursor = conn.cursor()
        not_exist = []
        to_create = {}
        to_update = {}
        for i in data:
            if not (id_ := data[i].get("id")) or not isinstance(r := data[i].get("rating"), (int, float)) or not isinstance(v := data[i].get("votes"), int):
                continue
            cursor.execute(f"SELECT * FROM series WHERE id_{type_} = ?", (id_,))
            if not cursor.fetchone():
                not_exist.append(id_)
                continue
            cursor.execute(f"SELECT rating, votes FROM series_ratings_{type_} WHERE id_{type_} = ?", (id_,))
            if not (row := cursor.fetchone()):
                to_create[id_] = {"rating": r, "votes": v}
            elif row[0] != r or row[1] != v:
                to_update[id_] = {"rating": r, "votes": v}

        if to_create:
            cursor.executemany(f"INSERT INTO series_ratings_{type_} (id_{type_}, rating, votes) VALUES (?, ?, ?)", [(i, j["rating"], j["votes"]) for i, j in to_create.items()])
        if to_update:
            cursor.executemany(f"UPDATE series_ratings_{type_} SET rating = ?, votes = ? WHERE id_{type_} = ?", [(j["rating"], j["votes"], i) for i, j in to_update.items()])
        conn.commit()
        conn.close()
        return  jsonify({"result": "OK", "message": "Ratings updated successfully", "not_exist": not_exist}), 200
    except Exception as e:
        app.logger.error(e)
        return jsonify({"result": "KO", "error": "Internal error"}), 500