from flask import Blueprint, jsonify, request, current_app as app
import sqlite3
from utils.external import series_data_external, update_ratings
from utils.common_code import valid_ids
from typing import Tuple

api_external_bp = Blueprint("api_external", __name__, url_prefix="/external")


@api_external_bp.route("/series/id", methods=["GET"])
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


@api_external_bp.route('/series/data', methods=['GET'])
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


@api_external_bp.route("/series/ratings", methods=["PUT"])
def update_series_ratings() -> Tuple[jsonify, int]:
    try:
        body = request.get_json() or {}
        type_ = body.get("id_type")
        if type_ not in ("mu", "dex", "mal"):
            return jsonify({"result": "KO", "error": "Invalid or missing id_type"}), 400
        data = body.get("data")
        if not isinstance(data, list):
            return jsonify({"result": "KO", "error": "Invalid or missing data"}), 400

        not_exist, s = update_ratings(type_, data)
        if s == 200:
            return jsonify({"result": "OK", "not_exist": not_exist}), 200
        else:
            return jsonify({"result": "KO", "error": "Internal error"}), 500
    except Exception as e:
        app.logger.error(e)
        return jsonify({"result": "KO", "error": "Internal error"}), 500
