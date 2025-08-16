from flask import Blueprint, request, current_app as app
import sqlite3
from typing import Tuple, Any

api_h_bp = Blueprint('api_h', __name__)


@api_h_bp.route("/h", methods=["POST"])
def add_h() -> Tuple[str, int]:
    try:
        id_ = request.args.get("id")
        if not id_:
            return "", 400

        conn = sqlite3.connect("data/mml.sqlite3")
        cursor = conn.cursor()

        if "/" in id_:
            i = id_.split("/")[0]
            k = id_.split("/")[1]
            if not i.isdigit():
                conn.close()
                return "", 400
            cursor.execute("INSERT OR IGNORE INTO schale_ids VALUES(?, ?)", (int(i), k))
        else:
            if not id_.isdigit():
                conn.close()
                return "", 400
            cursor.execute("INSERT OR IGNORE INTO nhentai_ids VALUES(?)", (int(id_),))
        conn.commit()
        conn.close()
        return "", 204
    except Exception as e:
        app.logger.error(e)
        return "", 500

@api_h_bp.route("/h", methods=["DELETE"])
def delete_h() -> Tuple[str, int]:
    try:
        id_ = request.args.get("id")
        if not id_:
            return "", 400

        conn = sqlite3.connect("data/mml.sqlite3")
        cursor = conn.cursor()

        if "/" in id_:
            id_ = id_.split("/")[0]
            if not id_.isdigit():
                conn.close()
                return "", 400
            cursor.execute("DELETE FROM schale_ids WHERE schale_id=?", (int(id_),))
        else:
            if not id_.isdigit():
                conn.close()
                return "", 400
            cursor.execute("DELETE FROM nhentai_ids WHERE nhentai_id = ?", (int(id_),))
        conn.commit()
        cursor.close()
        return "", 204
    except Exception as e:
        app.logger.error(e)
        return "", 500


@api_h_bp.route("/h/<int:id_>", methods=["GET"])
def get_nhentai(id_: int) -> Tuple[str, int]:
    try:
        conn = sqlite3.connect("data/mml.sqlite3")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(1) FROM nhentai_ids WHERE nhentai_id = ?", (id_,))
        r = cursor.fetchone()[0]
        conn.close()
        if r == 0:
            return "", 404
        return "", 204
    except Exception as e:
        app.logger.error(e)
        return "", 500

@api_h_bp.route("/h/<int:id_>/<path:subpath>", methods=["GET"])
def get_h(id_: int, subpath: Any) -> Tuple[str, int]:
    try:
        conn = sqlite3.connect("data/mml.sqlite3")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(1) FROM schale_ids WHERE schale_id = ?", (id_,))
        r = cursor.fetchone()[0]
        conn.close()
        if r == 0:
            return "", 404
        return "", 204
    except Exception as e:
        app.logger.error(e)
        return "", 500