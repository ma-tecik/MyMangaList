import requests
from flask import current_app as app
import sqlite3
from typing import Tuple, Union, Dict, List, Any


def download_thumbnail(series_id: int, thumbnail: str, cursor: sqlite3.Cursor) -> Tuple[dict, int]:
    import requests
    try:
        response = requests.get(thumbnail)
        if response.status_code != 200:
            app.logger.error(f"Failed to download image from {thumbnail}, status code: {response.status_code}")
            return {"result": "KO", "error": "Failed to download thumbnail"}, 502
        ext = response.headers.get("Content-Type").split("/")[-1]
        with open(f"data/thumbnails/{series_id}.{ext}", "wb") as f:
            f.write(response.content)
        cursor.execute("INSERT INTO series_thumbnails (series_id, extension) VALUES (?, ?)", (series_id, ext))
        return {"result": "OK"}, 201
    except Exception as e:
        app.logger.error(f"Failed to download the image from {thumbnail}: {e}")
        return {"result": "KO", "error": "Failed to download thumbnail"}, 500

# def delete_thumbnail(series_id: int, cursor: sqlite3.Cursor) -> Tuple[Dict[str, str], int]:
#     try:
#         cursor.execute("DELETE FROM series_thumbnails WHERE series_id = ? RETURNING extension", (series_id,))
#         ext = cursor.fetchone()[0]
#         with open(f'data/thumbnails/{series_id}.{ext}', 'wb') as image_file:
#             image_file.write(b'')
#         return {"result": "OK"}, 204
#     except Exception as e:
#         app.logger.error(f"Failed to delete the image for series {series_id}: {e}")
#         return {"result": "KO", "error": "Failed to delete image"}, 500
#
def update_thumbnail(series_id: int, thumbnail: str, cursor: sqlite3.Cursor) -> Tuple[Dict[str, str], int]:
    try:
        response = requests.get(thumbnail)
        if response.status_code != 200:
            app.logger.error(f"Failed to download image from {thumbnail}, status code: {response.status_code}")
            return {"result": "KO", "error": "Failed to download thumbnail"}, 502
        ext = response.headers.get("Content-Type").split("/")[-1]
        cursor.execute("SELECT extension FROM series_thumbnails WHERE series_id = ?", (series_id,))
        old_ext = cursor.fetchone()[0]
        if old_ext != ext:
            cursor.execute(f"UPDATE series_thumbnails SET extension = ? WHERE series_id = ?", (ext, series_id))
        with open(f"data/thumbnails/{series_id}.{old_ext}", "wb") as f:
            f.write(b"")
        with open(f"data/thumbnails/{series_id}.{ext}", "wb") as f:
            f.write(response.content)
        return {"result": "OK"}, 201
    except Exception as e:
        app.logger.error(f"Failed to update the image for series {series_id}: {e}")
        return {"result": "KO", "error": "Failed to update thumbnail"}, 500


def get_author_id(author: Dict[str, Union[str, int]], cursor: sqlite3.Cursor) -> Tuple[List[int], int]:
    try:
        ids = author.get("ids", {})
        id_mu = ids.get("mu")
        id_dex = ids.get("dex")
        id_mal = ids.get("mal")
        if not (id_mu or id_dex or id_mal):
            return [], 400

        cursor.execute("SELECT id FROM authors WHERE id_mu = ? OR id_dex = ? OR id_mal = ?", (id_mu, id_dex, id_mal))
        rows = cursor.fetchall()
        if not rows:
            cursor.execute("INSERT INTO authors (id_mu, id_dex, id_mal, name) VALUES (?, ?, ?, ?) RETURNING id",
                           (id_mu, id_dex, id_mal, author.get("name")))
            author_id = cursor.fetchone()[0]
        elif len(rows) == 1:
            author_id = rows[0][0]
            has_multiple_ids = sum(bool(x) for x in [id_mu, id_dex, id_mal]) > 1
            if has_multiple_ids:
                cursor.execute("SELECT id_mu, id_dex, id_mal FROM authors WHERE id = ?", (author_id,))
                existing = cursor.fetchone()
                if id_mu and not existing[0]:
                    cursor.execute("UPDATE authors SET id_mu = ? WHERE id = ?", (id_mu, author_id))
                if id_dex and not existing[1]:
                    cursor.execute("UPDATE authors SET id_dex = ? WHERE id = ?", (id_dex, author_id))
                if id_mal and not existing[2]:
                    cursor.execute("UPDATE authors SET id_mal = ? WHERE id = ?", (id_mal, author_id))
        else:
            return [i for i in rows[0]], 409
        return [author_id], 200
    except Exception as e:
        app.logger.error(e)
        return [], 500


def get_series_info(id_: int, cursor: sqlite3.Cursor) -> Tuple[Dict[str, Any], int]:
    try:
        cursor.execute("""
                       SELECT DISTINCT s.*, si.extension
                       FROM series s
                                LEFT JOIN series_thumbnails si ON s.id = si.series_id
                       WHERE s.id = ?
                       """, (id_,))
        row = cursor.fetchone()
        if not row:
            return {"status": "KO", "error": "Series not found"}, 404
        cursor.execute("SELECT alt_title FROM series_titles WHERE series_id = ?", (id_,))
        alt_titles = [t[0] for t in cursor.fetchall()]
        cursor.execute(
            "SELECT g.genre FROM genres g LEFT JOIN series_genres sg ON g.id = sg.genre_id WHERE sg.series_id = ?",
            (id_,))
        genres = [g[0] for g in cursor.fetchall()]
        cursor.execute(
            "SELECT DISTINCT a.id, a.name, sa.author_type FROM authors a LEFT JOIN series_authors sa ON a.id = sa.author_id WHERE sa.series_id = ?",
            (id_,))
        authors = [{"id": a[0], "name": a[1], "type": a[2]} for a in cursor.fetchall()]
        ratings = {}
        for i in ["mu", "dex", "mal"]:
            cursor.execute(f"SELECT rating FROM series_ratings_{i} WHERE id_{i} = ?", (id_,))
            r = cursor.fetchone()
            if r:
                ratings[i] = r[0]

        series_data = {
            "id": id_,
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
            "ratings": ratings,
            "user_rating": row["user_rating"],
        }
        return series_data, 200

    except Exception as e:
        app.logger.error(e)
        return {"status": "KO", "error": "Internal error"}, 500