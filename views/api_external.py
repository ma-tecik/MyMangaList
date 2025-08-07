from flask import Blueprint, jsonify, request, current_app as app
import sqlite3
import re
from utils.external import series_data_external
from typing import Dict, Any, Tuple

external_bp = Blueprint("external_api", __name__)

def _is_keys_valid(ids: Dict[str, Any]) -> bool:
    if not ids:
        return False
    if any(not value.isdigit() for value in [ids[k] for k in ["mal", "bato", "line"] if k in ids]):
        return False
    if "mu" in ids and not re.fullmatch(r"[0-9a-z]+", ids["mu"]):
        return False
    if "dex" in ids and not re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", ids["dex"]):
        return False
    return True

@external_bp.route("/external/series/id", methods=["GET"])
def get_series_id() -> Tuple[jsonify, int]:
    try:
        ids = request.args.to_dict()
        if not _is_keys_valid(ids) or any(key not in ["mu", "dex", "mal", "bato", "line"] for key in ids):
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
        ids = request.args.to_dict()
        if not _is_keys_valid(ids) or any(key not in ["mu", "dex", "mal", "bato", "line"] for key in ids):
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
