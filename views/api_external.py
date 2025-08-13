from flask import Blueprint, jsonify, request, current_app as app
import sqlite3
from utils.external import series_data_external
from utils.common_code import valid_ids
from typing import Tuple

external_bp = Blueprint("external_api", __name__)


@external_bp.route("/external/series/id", methods=["GET"])
def get_series_id() -> Tuple[jsonify, int]:
    try:
        if not (ids := valid_ids(request.args.to_dict())):
            return jsonify({"result": "KO", "error": "Invalid or missing IDs"}), 400
        conn = sqlite3.connect("instance/mml.sqlite3")
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
        return jsonify({"result": "KO", "error": "Internal server error"}), 500

@external_bp.route('/external/series/data', methods=['GET'])
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
    return jsonify({"result": "KO", "error": "Internal server error"}), 500
