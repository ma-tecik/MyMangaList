from flask import Blueprint, jsonify, request, current_app as app
from utils.common_db import download_thumbnail, update_thumbnail, get_author_id, get_series_info
from utils.common_code import valid_ids
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

def _valid_genres(genres: List[str]) -> List[str]:  # TODO: Will be implemented
    allowed_genres = ["nsfw", "sfw", "Josei", "Seinen", "Shoujo", "Shounen", "GL", "BL", "Lolicon", "Shotacon",
                      "Hentai", "Smut", "Adult", "Mature", "Ecchi", "Doujinshi",
                      ]
    # return [genre for genre in genres if genre in allowed_genres]
    return genres

@series_bp.route("/series", methods=["GET"])
def get_series_list() -> Tuple[jsonify, int]:
    try:
        sr = app.config["MAIN_SERIES_RATING"]
        # Query parameters
        args = request.args.to_dict()
        page = int(args.get("page", 1))
        per_page = max(min(int(args.get("perpage", 30)), 100), 30)
        status = args.get("status")
        type_ = args.get("type", "all")
        genres_included = args.get("included", "").split(",") if args.get("included") else []
        genres_excluded = args.get("excluded", "").split(",") if args.get("excluded") else []
        sort_by = args.get("sort_by", f"rating-{sr}")

        nsfw = ["Hentai", "Smut", "Adult", "Borderline H"]
        if "sfw" in genres_included:
            genres_included.remove("sfw")
        if "nsfw" in genres_included:
            genres_included.remove("nsfw")
            genres_included.extend(nsfw)
        if "nsfw" in genres_excluded:
            genres_excluded.remove("nsfw")
            genres_excluded.extend(nsfw + ["Ecchi"])
        if "sfw" in genres_excluded:
            genres_excluded.remove("sfw")
            genres_included.extend(nsfw)
        # Validate parameters
        if status and not _valid_status(status):
            return jsonify({"result": "KO", "error": "Invalid status", "valid": allowed_statuses}), 400
        if not (type_ == "all" or _valid_type(type_)):
            return jsonify({"result": "KO", "error": "Invalid type", "valid": ["all"]+allowed_types}), 400
        valid_sorts = ["rating-mu", "rating-dex", "rating-mal", "name", "id"]
        if sort_by not in valid_sorts:
            return jsonify({"result": "KO", "error": "Invalid sort_by parameter", "valid": valid_sorts}), 400
        genres_included = _valid_genres(genres_included)
        genres_excluded = _valid_genres(genres_excluded)
        if any(genre in genres_included for genre in genres_excluded):
            return jsonify({"result": "KO", "error": "Genres cannot be both included and excluded"}), 400

        conn = sqlite3.connect("instance/mml.sqlite3")
        cursor = conn.cursor()
        query = """
        SELECT DISTINCT s.*,
                        si.extension
        FROM series s
        LEFT JOIN series_images si ON s.id = si.series_id
        """
        if sort_by.startswith("rating-"):
            by = sort_by.split('-')[1]
            query += f"""
            LEFT JOIN series_ratings_{by} sr ON sr.id_{by} = s.id_{by}
            ORDER BY sr.rating_{by} DESC, s.title ASC
            """
        else:
            query += f"LEFT JOIN series_ratings_{sr} sr ON sr.id_{sr} = s.id_{sr}"
            if sort_by == "id":
                query += "ORDER BY s.id ASC"
            else:
                query += "ORDER BY s.title ASC"

        params = []
        where_conditions = []

        if status:
            where_conditions.append("s.status = ?")
            params.append(status)

        if type_ != "all":
            where_conditions.append("s.type = ?")
            params.append(type_)

        if genres_included:
            subquery = """
            s.id IN (
                SELECT sg.series_id FROM series_genres sg 
                JOIN genres g ON sg.genre_id = g.id 
                WHERE g.genre IN ({})
                GROUP BY sg.series_id
                HAVING COUNT(DISTINCT g.genre) = ?
            )
            """.format(','.join('?' * len(genres_included)))
            where_conditions.append(subquery)
            params.extend(genres_included)
            params.append(len(genres_included))

        if genres_excluded:
            subquery = """
            s.id NOT IN (
                SELECT sg.series_id FROM series_genres sg 
                JOIN genres g ON sg.genre_id = g.id 
                WHERE g.genre IN ({})
            )
            """.format(','.join('?' * len(genres_excluded)))
            where_conditions.append(subquery)
            params.extend(genres_excluded)

        if where_conditions:
            query += " WHERE " + " AND ".join(where_conditions)

        offset = (page - 1) * per_page
        query += f" LIMIT ? OFFSET ?"
        params.extend([per_page, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()

        series = []
        for row in rows:
            cursor.execute("""
                           SELECT a.id, a.name, sa.author_type
                           FROM series_authors sa
                                    JOIN authors a ON sa.author_id = a.id
                           WHERE sa.series_id = ?
                           """, (row[0],))
            authors = [{"id": a[0], "name": a[1], "type": a[2]} for a in cursor.fetchall()]
            cursor.execute("""
                           SELECT g.genre
                           FROM series_genres sg
                                    JOIN genres g ON sg.genre_id = g.id
                           WHERE sg.series_id = ?
                           """, (row[0],))
            genres = [g[0] for g in cursor.fetchall()]
            cursor.execute("SELECT alt_title FROM series_titles WHERE series_id = ?", (row[0],))
            alt_titles = [t[0] for t in cursor.fetchall()]

            series_data = {
                "id": row[0],
                "ids": {
                    "mu": row[1],
                    "dex": row[2],
                    "bato": row[3],
                    "mal": row[4],
                    "line": row[5]
                },
                "title": row[6],
                "alt_titles": alt_titles,
                "type": row[7],
                "description": row[8],
                "vol_ch": row[9],
                "is_md": bool(row[10]),
                "status": row[11],
                "year": row[12],
                "user_rating": row[14],
                "image_ext": row[15],
                "rating": row[16],
                "authors": authors,
                "genres": genres
            }
            series.append(series_data)

        conn.close()
        return jsonify({"status": "OK", "series": series, "page": page}), 200

    except Exception as e:
        app.logger.error(e)
        return jsonify({"status": "KO", "message": "Internal server error"}), 500

@series_bp.route("/series", methods=["POST"])
def create_series() -> Tuple[jsonify, int]:
    try:
        data = request.get_json()
        # Validate parameters
        if not data:
            return jsonify({"status": "KO", "message": "No data provided"}), 400
        if not all(field in data and data.get(field) for field in
                   ["ids", "title", "type", "status", "authors", "thumbnail"]):
            return jsonify({"status": "KO", "message": "Missing required fields"}), 400
        if not _valid_status(data["status"]):
            return jsonify({"status": "KO", "message": "Invalid status", "valid": allowed_statuses}), 400
        if not _valid_type(data["type"]):
            return jsonify({"status": "KO", "message": "Invalid type", "valid": allowed_types}), 400
        if not (ids := valid_ids(data.get("ids"))):
            return {"result": "KO", "error": "At least one valid ID is required"}, 400

        conn = sqlite3.connect("instance/mml.sqlite3")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM series WHERE id_mu = ? OR id_dex = ? OR id_bato = ? OR id_line = ? OR id_mal = ?",
            (ids.get("mu"), ids.get("dex"), ids.get("bato"), ids.get("line"), ids.get("mal")))
        row = cursor.fetchall()
        if len(row) > 1:
            return {"result": "MERGE_REQUIRED",
                    "error": "Manual merge required for series with multiple IDs: " + ", ".join(str(i[0]) for i in row),
                    "url": f"/series/merge?ids={",".join(str(r[0]) for r in row)}"}, 409
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
                        {"result": "MERGE_REQUIRED",
                         "error": "Manual merge required for authors with multiple IDs: " + ", ".join(
                             str(i) for i in r),
                         "merge_url": f"/author/merge?ids={",".join(str(i) for i in r)}"}), 409
                else:
                    app.logger.info(f"Error getting author ID for {author}")
                    return jsonify({"status": "KO", "message": "Internal server error"}), 500
            else:
                return jsonify(
                    {"status": "KO", "message": "Author must have at least one ID (external or internal)."}), 400
            authors.append({"id": a_id, "type": a_t})

        cursor.execute(f"""INSERT INTO series (id_mu, id_dex, id_bato, id_mal, id_line, title, type, description, vol_ch, is_md, status, year)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) RETURNING id""",
                       (ids.get("mu"), ids.get("dex"), ids.get("bato"), ids.get("mal"), ids.get("line"),
                        data.get("title"), data.get("type"), data.get("description"), data.get("vol_ch"),
                        data.get("is_md", False), data.get("status"), data.get("year")))
        id_ = cursor.fetchone()[0]

        if len(data.get("timestamp")) == 1:
            t = data["timestamp"]
            if (k := next(iter(t.keys()))) in ["mu", "dex", "mal"]:
                cursor.execute(f"UPDATE series SET timestamp_{k} = ? WHERE id = ?", (t[k], id_))
        elif len(data.get("timestamp")) > 1:
            return jsonify({"status": "KO", "message": "Multiple timestamps provided, only one is allowed"}), 400

        r, s = download_thumbnail(id_, data["thumbnail"], cursor)
        if s != 201:
            return jsonify(r), s

        if authors:
            cursor.executemany("INSERT INTO series_authors (series_id, author_id, author_type) VALUES (?, ?, ?)",
                               [(id_, a["id"], a["type"]) for a in authors])

        if genres := _valid_genres(data.get("Genres", [])):
            cursor.execute("SELECT id FROM genres WHERE genre IN ({})".format(", ".join("?" for _ in genres)), genres)
            genre_ids = [row[0] for row in cursor.fetchall()]
            cursor.executemany("INSERT INTO series_genres (series_id, genre_id) VALUES (?, ?)",
                               [(id_, genre_id) for genre_id in genre_ids])

        if alt_titles := data.get("alt_titles"):
            cursor.executemany("INSERT INTO series_titles (series_id, alt_title) VALUES (?, ?)",
                               [(id_, title) for title in alt_titles])

        r, s = get_series_info(id_, cursor)
        if s == 200:
            conn.commit()
            conn.close()
            return jsonify({"status": "OK", "data": r}), 200
        else:
            conn.close()
            return jsonify({"status": "KO", "message": "Error retrieving created series"}), 500
    except Exception as e:
        app.logger.error(e)
        return jsonify({"status": "KO", "message": "Internal server error"}), 500

@series_bp.route("/series/<int:id_>", methods=["GET"])
def get_series_by_id(id_) -> Tuple[jsonify, int]:
    try:
        conn = sqlite3.connect("instance/mml.sqlite3")
        cursor = conn.cursor()
        r, s = get_series_info(id_, cursor)
        conn.close()
        if s == 200:
            return jsonify({"status": "OK", "data": r}), 200
        else:
            return jsonify(r), s
    except Exception as e:
        app.logger.error(e)
        return jsonify({"status": "KO", "message": "Internal server error"}), 500

@series_bp.route("/series/<int:id_>", methods=["DELETE"])
def delete_series(id_) -> Tuple[jsonify, int]:
    try:
        conn = sqlite3.connect("instance/mml.sqlite3")
        cursor = conn.cursor()
        r, s = get_series_info(id_, cursor)
        if s == 404:
            conn.close()
            return jsonify({"result": "KO", "error": "Series not found"}), 404
        elif s != 200:
            conn.close()
            return jsonify(r), s

        authors_to_delete = []
        for author in r.get("authors"):
            cursor.execute("SELECT COUNT(*) FROM series_authors WHERE author_id = ?", (author["id"],))
            if cursor.fetchone()[0] == 1:
                authors_to_delete.append(author["id"])

        cursor.execute("DELETE FROM series WHERE id = ?", (id_,))

        if authors_to_delete:
            cursor.executemany("DELETE FROM authors WHERE id = ?", [(a_id,) for a_id in authors_to_delete])

        conn.commit()
        conn.close()
        return jsonify({"result": "OK", "data": r}), 200

    except Exception as e:
        app.logger.error(e)
        return jsonify({"result": "KO", "error": "Internal server error"}), 500

@series_bp.route("/series/<int:id_>", methods=["PATCH"])
def update_series(id_) -> Tuple[jsonify, int]:
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "KO", "message": "No data provided"}), 400

        conn = sqlite3.connect("instance/mml.sqlite3")
        cursor = conn.cursor()

        r, s = get_series_info(id_, cursor)
        if s == 404:
            conn.close()
            return jsonify({"status": "KO", "message": "Series not found"}), 404
        elif s != 200:
            conn.close()
            return jsonify(r), s

        if "ids" in data:
            if not (ids := valid_ids(data.get("ids"))):
                conn.close()
                return jsonify({"status": "KO", "message": "IDs not valid"}), 400
            for key, value in ids.items():
                cursor.execute(f"SELECT id FROM series WHERE id_{key} = ? AND id != ?", (value, id_))
                if cursor.fetchone():
                    conn.close()
                    return jsonify({"status": "KO", "message": f"Series with {key} ID {value} already exists"}), 409

        if "status" in data and not _valid_status(data["status"]):
            conn.close()
            return jsonify({"status": "KO", "message": "Invalid status", "valid": allowed_statuses}), 400

        if "type" in data and not _valid_type(data["type"]):
            conn.close()
            return jsonify({"status": "KO", "message": "Invalid type", "valid": allowed_types}), 400

        if "timestamp" in data and len(data["timestamp"]) != 1:
            conn.close()
            return jsonify({"status": "KO", "message": "Multiple timestamps provided, only one is allowed"}), 400


        update_fields = []
        update_params = []

        series_fields = ["title", "type", "description", "vol_ch", "is_md", "status", "year"]
        for field in series_fields:
            if field in data:
                update_fields.append(f"{field} = ?")
                update_params.append(data[field])

        if "ids" in data:
            id_fields = ["mu", "dex", "mal", "bato", "line"]
            for field in id_fields:
                if field in ids:
                    update_fields.append(f"id_{field} = ?")
                    update_params.append(ids[field])

        if "timestamp" in data: # TODO: PRIORITY: HIGH! Test this!
            t = data["timestamp"]
            for i in ["mu", "dex", "mal"]:
                if i in t:
                    update_fields.append(f"timestamp_{i} = ?")
                    update_params.append(t[i])
                else:
                    update_fields.append(f"timestamp_{i} = NULL")

        if update_fields:
            query = f"UPDATE series SET {', '.join(update_fields)} WHERE id = ?"
            update_params.append(id_)
            cursor.execute(query, update_params)

        if "genres" in data:
            cursor.execute("DELETE FROM series_genres WHERE series_id = ?", (id_,))
            if genres := _valid_genres(data["genres"]):
                cursor.execute("SELECT id FROM genres WHERE genre IN ({})".format(", ".join("?" for _ in genres)), genres)
                genre_ids = [row[0] for row in cursor.fetchall()]
                cursor.executemany("INSERT INTO series_genres (series_id, genre_id) VALUES (?, ?)",
                                   [(id_, genre_id) for genre_id in genre_ids])

        if "alt_titles" in data:
            cursor.execute("DELETE FROM series_titles WHERE series_id = ?", (id_,))
            if alt_titles := data["alt_titles"]:
                cursor.executemany("INSERT INTO series_titles (series_id, alt_title) VALUES (?, ?)",
                                   [(id_, title) for title in alt_titles])

        if "thumbnail" in data:
            r, s = update_thumbnail(id_, data["thumbnail"], cursor)
            if s != 201:
                conn.close()
                return jsonify(r), s

        r, s = get_series_info(id_, cursor)
        if s == 200:
            conn.commit()
            conn.close()
            return jsonify({"status": "OK", "data": r}), 200
        else:
            conn.close()
            return jsonify({"status": "KO", "message": "Error retrieving updated series"}), 500

    except Exception as e:
        app.logger.error(e)
        return jsonify({"status": "KO", "message": "Internal server error"}), 500

@series_bp.route("/series/<int:id_>/ratings", methods=["POST"])
def update_series_ratings(id_):
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "KO", "message": "No data provided"}), 400

        conn = sqlite3.connect("instance/mml.sqlite3")
        cursor = conn.cursor()

        r, s = get_series_info(id_, cursor)
        if s == 404:
            conn.close()
            return jsonify({"status": "KO", "message": "Series not found"}), 404
        elif s != 200:
            conn.close()
            return jsonify(r), s

        if user_rating := data.get("user_rating"):
            if not isinstance(user_rating, (int, float)) or not (0 <= user_rating <= 10):
                conn.close()
                return jsonify({"status": "KO", "message": "Invalid user rating, must be a number between 0 and 10"}), 400
            cursor.execute("SELECT user_rating FROM series WHERE id = ?", (id_,))
            old_rating = cursor.fetchone()[0]
            if old_rating != user_rating:
                cursor.execute("UPDATE series SET user_rating = ? WHERE id = ?", (user_rating, id_))

        for i in ["mu", "dex", "mal"]:
            j = f"{i}_rating"
            if j in data:
                rating = data[j]
                votes = data.get(f"{i}_votes", 0)
                if not (0 <= rating <= 10):
                    conn.close()
                    return jsonify({"status": "KO", "message": f"Invalid {j}, must be a number between 0 and 10"}), 400
                cursor.execute(f"SELECT rating, votes FROM series_ratings_{i} WHERE id = ?", (id_,))
                old_rating, old_votes = cursor.fetchone()
                if old_rating != rating:
                    cursor.execute(f"UPDATE series_ratings_{i} SET rating = ? WHERE id = ?", (rating, id_))
                if votes and old_votes != votes:
                    cursor.execute(f"UPDATE series_ratings_{i} SET votes = ? WHERE id = ?", (votes, id_))
        conn.commit()
        conn.close()
        return "", 204
    except Exception as e:
        app.logger.error(e)
        return jsonify({"status": "KO", "message": "Internal server error"}), 500