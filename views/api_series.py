from flask import Blueprint, jsonify, request, current_app as app
from utils.common_db import download_thumbnail, update_thumbnail, add_genres, get_author_id, get_series_info
from utils.common_code import valid_ids
import sqlite3
import time
from typing import List, Tuple

api_series_bp = Blueprint("api_series", __name__, url_prefix="/series")

allowed_statuses = ["plan-to", "reading", "completed", "one-shot", "dropped", "on-hold", "ongoing"]
allowed_types = ["all", "Manga", "Manhwa", "Manhua", "OEL", "Vietnamese", "Malaysian", "Indonesian",
                 "Novel", "Artbook", "Other", "minor"]


def _valid_status(status: str) -> bool:
    return True if status in allowed_statuses else False


def _valid_type(type_: str) -> bool:
    return True if type_ in allowed_types else False


def _valid_genres(genres: List[str]) -> List[str]:
    allowed_genres = ["nsfw", "Josei", "Seinen", "Shoujo", "Shounen", "GL", "BL", "Lolicon", "Shotacon", "Hentai",
                      "Smut", "Adult", "Mature", "Ecchi", "Doujinshi", "4-Koma", "Anthology", "Harlequin", "Webtoon",
                      "Old-Style", "Award", "Cancel", "Rushed", "European", "Asian", "isekai", "Reverse isekai",
                      "Time Rewind", "Villainess", "Revenge", "Modern", "Childhood F.", "Con. Marr.", "Arranged Marr.",
                      "Sensei", "Age Gap", "Office", "Boss-Sub", "Showbiz", "Action", "Adventure", "Comedy", "Drama",
                      "Fantasy", "Gender Bender", "Harem", "Reverse Harem", "Historical", "Horror", "Martial Arts",
                      "Mecha", "Mystery", "Psychological", "Romance", "School Life", "Sci-fi", "Slice of Life",
                      "Sports", "Supernatural", "Tragedy", "Incest", "Yandere", "Toxic Rel.", "Borderline H"]
    return [genre for genre in genres if genre in allowed_genres]


@api_series_bp.route("", methods=["GET"])
def get_series_list() -> Tuple[jsonify, int]:
    try:
        sr = app.config["MAIN_RATING"]
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
        if "nsfw" in genres_included:
            genres_included.remove("nsfw")
            genres_included.extend(nsfw)
        if "nsfw" in genres_excluded:
            genres_excluded.remove("nsfw")
            genres_excluded.extend(nsfw + ["Ecchi"])
        # Validate parameters
        if status and not _valid_status(status):
            return jsonify({"result": "KO", "error": "Invalid status", "valid": allowed_statuses}), 400
        if not (type_ == "all" or _valid_type(type_)):
            return jsonify({"result": "KO", "error": "Invalid type", "valid": ["all"] + allowed_types}), 400
        valid_sorts = ["rating-mu", "rating-dex", "rating-mal", "name", "time"]
        if sort_by not in valid_sorts:
            return jsonify({"result": "KO", "error": "Invalid sort_by parameter", "valid": valid_sorts}), 400
        genres_included = _valid_genres(genres_included)
        genres_excluded = _valid_genres(genres_excluded)
        if any(genre in genres_included for genre in genres_excluded):
            return jsonify({"result": "KO", "error": "Genres cannot be both included and excluded"}), 400

        conn = sqlite3.connect("data/mml.sqlite3")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        select_clause = "SELECT DISTINCT s.*, si.extension"
        from_clause = " FROM series s LEFT JOIN series_thumbnails si ON s.id = si.series_id "

        if sort_by.startswith("rating-") and (by := sort_by.split('-')[1]) in ("mu", "dex", "mal"):
            from_clause += f"LEFT JOIN series_ratings_{by} sr ON sr.id_{by} = s.id_{by} "
            select_clause += ", COALESCE(sr.rating, 0) AS rating"
            order_clause = "ORDER BY sr.rating DESC, s.title ASC "
        else:
            from_clause += f"LEFT JOIN series_ratings_{sr} sr ON sr.id_{sr} = s.id_{sr} "
            select_clause += ", COALESCE(sr.rating, 0) AS rating"
            if sort_by == "title":
                order_clause = "ORDER BY s.title ASC "
            elif sort_by == "time":
                order_clause = "ORDER BY s.timestamp_status ASC "
            else:
                order_clause = "ORDER BY s.title ASC "

        params = []
        where_conditions = []

        if status:
            where_conditions.append("s.status = ?")
            params.append(status)

        if type_ != "all":
            if type_ == "minor":
                where_conditions.append(
                    "s.type = ? OR s.type = ? OR s.type = ? OR s.type = ? OR s.type = ? OR s.type = ? OR s.type = ?")
                params.extend(["OEL", "Vietnamese", "Malaysian", "Indonesian", "Novel", "Artbook", "Other"])
            else:
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

        query = select_clause + from_clause
        if where_conditions:
            query += "WHERE " + " AND ".join(where_conditions) + " "

        offset = (page - 1) * per_page
        query += order_clause
        query += "LIMIT ? OFFSET ?"
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
                "id": row["id"],
                "thumbnail_ext": row["extension"],
                "ids": {
                    "mu": row["id_mu"],
                    "dex": row["id_dex"],
                    "mal": row["id_mal"],
                    "bato": row["id_bato"],
                    "line": row["id_line"],
                },
                "title": row["title"],
                "alt_titles": alt_titles,
                "type": row["type"],
                "description": row["description"],
                "vol_ch": row["vol_ch"],
                "is_md": bool(row["is_md"]),
                "genres": genres,
                "status": row["status"],
                "year": row["year"],
                "authors": authors,
                "rating": row["rating"],
                "user_rating": row["user_rating"],
            }
            series.append(series_data)

        conn.close()
        return jsonify({"result": "OK", "data": series, "page": page}), 200

    except Exception as e:
        app.logger.error(e)
        return jsonify({"result": "KO", "error": "Internal error"}), 500


@api_series_bp.route("", methods=["POST"])
def create_series() -> Tuple[jsonify, int]:
    try:
        data = request.get_json()
        # Validate parameters
        if not data:
            return jsonify({"result": "KO", "error": "No data provided"}), 400
        if not all(field in data and data.get(field) for field in
                   ["ids", "title", "type", "status", "authors", "thumbnail"]):
            return jsonify({"result": "KO", "error": "Missing required fields"}), 400
        if not _valid_status(data["status"]):
            return jsonify({"result": "KO", "error": "Invalid status", "valid": allowed_statuses}), 400
        if not _valid_type(data["type"]):
            return jsonify({"result": "KO", "error": "Invalid type", "valid": allowed_types}), 400
        if not (ids := valid_ids(data.get("ids"))):
            return {"result": "KO", "error": "At least one valid ID is required"}, 400

        conn = sqlite3.connect("data/mml.sqlite3")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM series WHERE id_mu = ? OR id_dex = ? OR id_bato = ? OR id_line = ? OR id_mal = ?",
            (ids.get("mu"), ids.get("dex"), ids.get("bato"), ids.get("line"), ids.get("mal")))
        row = cursor.fetchall()
        if len(row) > 1:
            return {"result": "MERGE_REQUIRED",
                    "error": "Manual merge required for series with multiple IDs: " + ", ".join(str(i[0]) for i in row),
                    "url": f"/series/merge?ids={','.join(str(r[0]) for r in row)}"}, 409
        elif len(row) == 1:
            sid = row[0][0]
            return {"result": "MERGE_REQUIRED", "error": "Series with these IDs already exists, please use update.",
                    "url": f"/series/{sid}"}, 409

        authors = []
        for author in data["authors"]:
            if author.get("type") in ["Author", "Artist", "Both"]:
                a_t = author["type"]
            else:
                return jsonify({"result": "KO", "error": "Missing or invalid author info"}), 400

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
                         "merge_url": f"/author/merge?ids={','.join(str(i) for i in r)}"}), 409
                else:
                    app.logger.info(f"Error getting author ID for {author}")
                    return jsonify({"result": "KO", "error": "Internal error"}), 500
            else:
                return jsonify(
                    {"result": "KO", "error": "Author must have at least one ID (external or internal)."}), 400
            authors.append({"id": a_id, "type": a_t})

        cursor.execute(f"""INSERT INTO series
        (id_mu, id_dex, id_bato, id_mal, id_line, title, type, description, vol_ch, is_md, status, year, timestamp_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) RETURNING id""",
                       (ids.get("mu"), ids.get("dex"), ids.get("bato"), ids.get("mal"), ids.get("line"),
                        data.get("title"), data.get("type"), data.get("description"), data.get("vol_ch"),
                        data.get("is_md", False), data.get("status"), data.get("year"), int(time.time())))
        id_ = cursor.fetchone()[0]

        if data.get("timestamp"):
            if len(data.get("timestamp")) == 1:
                t = data["timestamp"]
                if (k := next(iter(t.keys()))) in ["mu", "dex", "mal"]:
                    cursor.execute(f"UPDATE series SET timestamp_{k} = ? WHERE id = ?", (t[k], id_))
            elif len(data.get("timestamp")) > 1:
                return jsonify({"result": "KO", "error": "Multiple timestamps provided, only one is allowed"}), 400

        r, s = download_thumbnail(id_, data["thumbnail"], cursor)
        if s != 201:
            return jsonify(r), s

        if authors:
            cursor.executemany("INSERT INTO series_authors (series_id, author_id, author_type) VALUES (?, ?, ?)",
                               [(id_, a["id"], a["type"]) for a in authors])

        if genres := _valid_genres(data.get("genres", [])):
            add_genres(id_, genres, cursor)

        if alt_titles := data.get("alt_titles"):
            cursor.executemany("INSERT INTO series_titles (series_id, alt_title) VALUES (?, ?)",
                               [(id_, title) for title in alt_titles])

        r, s = get_series_info(id_, cursor)
        if s == 200:
            conn.commit()
            conn.close()
            return jsonify({"result": "OK", "data": r}), 201
        else:
            conn.close()
            return jsonify({"result": "KO", "error": "Error retrieving created series"}), 500
    except Exception as e:
        app.logger.error(e)
        return jsonify({"result": "KO", "error": "Internal error"}), 500


@api_series_bp.route("/<int:id_>", methods=["GET"])
def get_series_by_id(id_) -> Tuple[jsonify, int]:
    try:
        conn = sqlite3.connect("data/mml.sqlite3")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        r, s = get_series_info(id_, cursor)
        conn.close()
        if s == 200:
            return jsonify({"result": "OK", "data": r}), 200
        else:
            return jsonify(r), s
    except Exception as e:
        app.logger.error(e)
        return jsonify({"result": "KO", "error": "Internal error"}), 500


@api_series_bp.route("/<int:id_>", methods=["DELETE"])
def delete_series(id_) -> Tuple[jsonify, int]:
    try:
        conn = sqlite3.connect("data/mml.sqlite3")
        conn.row_factory = sqlite3.Row
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
        return jsonify({"result": "KO", "error": "Internal error"}), 500


@api_series_bp.route("/<int:id_>", methods=["PATCH"])
def update_series(id_) -> Tuple[jsonify, int]:
    try:
        data = request.get_json()
        if not data:
            return jsonify({"result": "KO", "error": "No data provided"}), 400

        conn = sqlite3.connect("data/mml.sqlite3")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        r, s = get_series_info(id_, cursor)
        if s == 404:
            conn.close()
            return jsonify({"result": "KO", "error": "Series not found"}), 404
        elif s != 200:
            conn.close()
            return jsonify(r), s

        ids = None
        if "ids" in data:
            if not (ids := valid_ids(data.get("ids"))):
                conn.close()
                return jsonify({"result": "KO", "error": "IDs not valid"}), 400
            for key, value in ids.items():
                cursor.execute(f"SELECT id FROM series WHERE id_{key} = ? AND id != ?", (value, id_))
                if cursor.fetchone():
                    conn.close()
                    return jsonify({"result": "KO", "error": f"Series with {key} ID {value} already exists"}), 409

        if "status" in data and not _valid_status(data["status"]):
            conn.close()
            return jsonify({"result": "KO", "error": "Invalid status", "valid": allowed_statuses}), 400

        if "type" in data and not _valid_type(data["type"]):
            conn.close()
            return jsonify({"result": "KO", "error": "Invalid type", "valid": allowed_types}), 400

        if "timestamp" in data and len(data["timestamp"]) != 1:
            conn.close()
            return jsonify({"result": "KO", "error": "Multiple timestamps provided, only one is allowed"}), 400

        if "integration" in data and not isinstance(data["integration"], bool):
            conn.close()
            return jsonify({"result": "KO", "error": "Invalid integration value, must be boolean"}), 400

        update_fields = []
        update_params = []

        series_fields = ["title", "type", "description", "vol_ch", "is_md", "status", "year"]
        for field in series_fields:
            if field in data:
                update_fields.append(f"{field} = ?")
                update_params.append(data[field])

        if "status" in data:
            update_fields.append("timestamp_status = ?")
            update_params.append(int(time.time()))

        if ids:
            id_fields = ["mu", "dex", "mal", "bato", "line"]
            for field in id_fields:
                if field in ids:
                    update_fields.append(f"id_{field} = ?")
                    update_params.append(ids[field])

        if "timestamp" in data:
            t = data["timestamp"]
            for i in ["mu", "dex", "mal"]:
                if i in t:
                    update_fields.append(f"timestamp_{i} = ?")
                    update_params.append(t[i])
                else:
                    update_fields.append(f"timestamp_{i} = NULL")

        if "integration" in data:
            if isinstance(data["integration"], bool):
                update_fields.append("integration = ?")
                update_params.append(1 if data["integration"] else 0)

        if update_fields:
            query = f"UPDATE series SET {', '.join(update_fields)} WHERE id = ?"
            update_params.append(id_)
            cursor.execute(query, update_params)

        if "genres" in data:
            cursor.execute("DELETE FROM series_genres WHERE series_id = ?", (id_,))
            if genres := _valid_genres(data["genres"]):
                add_genres(id_, genres, cursor)
            cursor.execute("UPDATE series SET integration_genres = 0 WHERE id = ?", (id_,))

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
            cursor.execute("UPDATE series_thumbnails SET integration = 0 WHERE series_id = ?", (id_,))

        r, s = get_series_info(id_, cursor)
        if s == 200:
            conn.commit()
            conn.close()
            return jsonify({"result": "OK", "data": r}), 200
        else:
            conn.close()
            return jsonify({"result": "KO", "error": "Error retrieving updated series"}), 500

    except Exception as e:
        app.logger.error(e)
        return jsonify({"result": "KO", "error": "Internal error"}), 500


@api_series_bp.route("/<int:id_>/ratings", methods=["PATCH"])
def update_series_ratings(id_):
    try:
        data = request.get_json()
        if not data:
            return jsonify({"result": "KO", "error": "No data provided"}), 400

        conn = sqlite3.connect("data/mml.sqlite3")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        r, s = get_series_info(id_, cursor)
        if s == 404:
            conn.close()
            return jsonify({"result": "KO", "error": "Series not found"}), 404
        elif s != 200:
            conn.close()
            return jsonify(r), s

        if (user_rating := data.get("user_rating")) is not None:
            if not isinstance(user_rating, (int, float)) or not (1 <= float(user_rating) <= 10):
                conn.close()
                return jsonify(
                    {"result": "KO", "error": "Invalid user rating, must be a number between 1 and 10"}), 400
            cursor.execute("SELECT user_rating FROM series WHERE id = ?", (id_,))
            old_rating = cursor.fetchone()[0]
            if old_rating != user_rating:
                cursor.execute("UPDATE series SET user_rating = ? WHERE id = ?", (user_rating, id_))

        ids_map = r.get("ids", {})
        for i in ["mu", "dex", "mal"]:
            rating_key = f"{i}_rating"
            votes_key = f"{i}_votes"
            if votes_key in data and data[votes_key] is not None:
                try:
                    if int(data[votes_key]) < 1:
                        conn.close()
                        return jsonify({"result": "KO", "error": f"Invalid {votes_key}, must be >= 1"}), 400
                except ValueError:
                    conn.close()
                    return jsonify({"result": "KO", "error": f"Invalid {votes_key}, must be an integer"}), 400
            if rating_key in data:
                rating = data[rating_key]
                votes = data.get(votes_key)
                if rating is None or not (1 <= float(rating) <= 10):
                    conn.close()
                    return jsonify({"result": "KO", "error": f"Invalid {rating_key}, must be between 1 and 10"}), 400
                ext_id = ids_map.get(i)
                if not ext_id:
                    # cannot update without external id for that source
                    continue
                # check existing
                cursor.execute(f"SELECT rating, votes FROM series_ratings_{i} WHERE id_{i} = ?", (ext_id,))
                row = cursor.fetchone()
                if row is None:
                    # insert
                    cursor.execute(
                        f"INSERT INTO series_ratings_{i} (id_{i}, rating, votes) VALUES (?, ?, ?)",
                        (ext_id, float(rating), int(votes) if votes is not None else 0),
                    )
                else:
                    old_rating, old_votes = row[0], row[1]
                    if old_rating != float(rating):
                        cursor.execute(f"UPDATE series_ratings_{i} SET rating = ? WHERE id_{i} = ?",
                                       (float(rating), ext_id))
                    if votes is not None and old_votes != int(votes):
                        cursor.execute(f"UPDATE series_ratings_{i} SET votes = ? WHERE id_{i} = ?",
                                       (int(votes), ext_id))
        conn.commit()
        conn.close()
        return "", 204
    except Exception as e:
        app.logger.error(e)
        return jsonify({"result": "KO", "error": "Internal error"}), 500
