from flask import Blueprint, jsonify, request, current_app as app
from utils.common_db import download_thumbnail, get_author_id
import sqlite3
from typing import List, Tuple

series_bp = Blueprint("series_api", __name__)

allowed_statuses = ["Plan to Read", "Reading", "Completed", "One-shot", "Dropped", "Ongoing"]
allowed_types = ["Manga", "Manhwa", "Manhua", "OEL", "Vietnamese", "Malaysian", "Indonesian",
                 "Novel", "Artbook", "Other"]


def _valid_status(status: str) -> bool:
    return True if status in allowed_statuses else False


def _valid_type(type_: str) -> bool:
    return True if type_ in allowed_types else False


def _valid_genres(genres: List[str]) -> List[str]:  # TODO: Will be updated
    allowed_genres = ["Josei", "Seinen", "Shoujo", "Shounen", "GL", "BL", "Lolicon", "Shotacon",
                      "Hentai", "Smut", "Adult", "Mature", "Ecchi", "Doujinshi",
                      ]
    return [genre for genre in genres if genre in allowed_genres]


@series_bp.route("/series", methods=["GET"])
def get_series_list() -> Tuple[jsonify, int]:
    return jsonify({"result": "KO", "error": "Not implemented yet"}), 501


@series_bp.route("/series/", methods=["POST"])
def create_series() -> Tuple[jsonify, int]:
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "KO", "message": "No data provided"}), 400
        if not all(field in data for field in ["ids", "title", "type", "status", "authors", "thumbnail"]):
            return jsonify({"status": "KO", "message": "Missing required fields"}), 400
        if not data["Authors"].get[0]:
            return jsonify({"status": "KO", "message": "Missing Authors"}), 400
        if not _valid_status(data["status"]):
            return jsonify({"status": "KO", "message": "Invalid status", "valid": allowed_statuses}), 400
        if not _valid_type(data["type"]):
            return jsonify({"status": "KO", "message": "Invalid type", "valid": allowed_types}), 400

        ids = {k: v for k, v in data.get('ids', {}).items() if
               k in {'mu', 'dex', 'bato', 'mal', 'line'} and v is not None}
        if len(ids) == 0:
            return {"result": "KO", "error": "At least one valid ID is required"}, 400

        conn = sqlite3.connect("instance/mml.sqlite3")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM series WHERE id_mu = ? OR id_dex = ? OR id_bato = ? OR id_line = ? OR id_mal = ?",
            (ids.get('mu'), ids.get('dex'), ids.get('bato'), ids.get('line'), ids.get('mal')))
        row = cursor.fetchall()
        if len(row) > 1:
            return {"result": "MERGE_REQUIRED",
                    "error": "Manual merge required for series with multiple IDs: " + ", ".join(str(i[0]) for i in row),
                    "url": f"/series/merge?ids={','.join(str(r[0]) for r in row)}"}, 409
        elif len(row) == 1:
            data["id"] = row[0][0]
            return {"result": "USE_UPDATE", "error": "Series with these IDs already exists, please use update.",
                    "url": f"/series/update?data={data}"}, 409

        authors = []
        for author in data["authors"]:
            if author.get("type") in ["Author", "Artist", "Both"]:
                a_t = author["type"]
            else:
                return jsonify({"status": "KO", "message": "Missing or invalid author info"}), 400

            if author.get("id"):
                a_id = author["id"]
            elif author.get("ids"):
                r, s = get_author_id(author, cursor)
                if s == 200:
                    a_id = r[0]
                elif s == 409:
                    return jsonify(
                        {"result": "MERGE_REQUIRED", "error": "Manual merge required for authors with multiple IDs: " + ", ".join(str(i) for i in r),
                         "merge_url": f"/author/merge?ids={','.join(str(i) for i in r)}"}), 409
                else:
                    return jsonify({"status": "KO", "message": "Internal server error"}), 500
            else:
                return jsonify(
                    {"status": "KO", "message": "Author must have at least one ID (external or internal)."}), 400
            authors.append({"id": a_id, "type": a_t})

        cursor.execute(f"""INSERT INTO series (id_mu, id_dex, id_bato, id_mal, id_line, title, type, description, vol_ch, is_md, year, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) RETURNING id""",
                       (data.get('id_mu'), data.get('id_dex'), data.get('id_bato'), data.get('id_mal'),
                        data.get('id_line'), data.get('title'), data.get('type'), data.get('description'),
                        data.get('vol_ch'), data.get('is_md', False), data.get('year'), data.get("status")))
        id_ = cursor.fetchone()[0]

        r, s = download_thumbnail(id_, data["thumbnail"], cursor)
        if s != 201:
            return jsonify(r), s

        for a in authors:
            cursor.execute("INSERT INTO series_authors (series_id, author_id, author_type) VALUES (?, ?, ?)",
                           (id_, a["id"], a["type"]))

        genres = _valid_genres(data.get("Genres", []))
        if genres:
            cursor.execute("SELECT id FROM genres WHERE genre IN ({})".format(', '.join('?' for _ in genres)), genres)
            genre_ids = [row[0] for row in cursor.fetchall()]
            cursor.executemany("INSERT INTO series_genres (series_id, genre_id) VALUES (?, ?)",[(id_, genre_id) for genre_id in genre_ids])

        conn.commit()
        conn.close()
        return jsonify({"status": "OK"}), 201

    except Exception as e:
        app.logger.error(e)
        return jsonify({"status": "KO", "message": "Internal server error"}), 500


@series_bp.route("/series/<int:series_id>", methods=["GET"])
def get_series_by_id(series_id) -> Tuple[jsonify, int]:
    return jsonify({"result": "KO", "error": "Not implemented yet"}), 501


@series_bp.route("/series/<int:series_id>", methods=["DELETE"])
def delete_series(series_id) -> Tuple[jsonify, int]:
    return jsonify({"result": "KO", "error": "Not implemented yet"}), 501


@series_bp.route("/series/<int:series_id>", methods=["PATCH"])
def update_series(series_id) -> Tuple[jsonify, int]:
    return jsonify({"result": "KO", "error": "Not implemented yet"}), 501
