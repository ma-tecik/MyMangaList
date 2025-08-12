from flask import current_app as app
import sqlite3
from typing import Tuple, Union, Dict, List


def download_thumbnail(series_id: int, thumbnail: str, cursor: sqlite3.Cursor) -> Tuple[dict, int]:
    import requests
    try:
        response = requests.get(thumbnail)
        if response.status_code != 200:
            app.logger.error(f"Failed to download image from {thumbnail}, status code: {response.status_code}")
            return {"result": "KO", "error": "Failed to download thumbnail"}, 502
        ext = response.headers.get('Content-Type').split('/')[-1]
        with open(f"static/images/{series_id}.{ext}", 'wb') as f:
            f.write(response.content)
        cursor.execute("INSERT INTO series_images (series_id, extension) VALUES (?, ?)", (series_id, ext))
    except Exception as e:
        app.logger.error(f"Failed to download the image from {thumbnail}: {e}")
        return {"result": "KO", "error": "Failed to download thumbnail"}, 500
    return {"result": "OK"}, 201

# def delete_thumbnail(series_id: int, cursor: sqlite3.Cursor) -> Tuple[Dict[str, str], int]:
#     try:
#         cursor.execute("DELETE FROM series_images WHERE series_id = ? RETURNING extension", (series_id,))
#         ext = cursor.fetchone()[0]
#         with open(f'static/images/{series_id}.{ext}', 'wb') as image_file:
#             image_file.write(b'')
#         return {"result": "OK"}, 204
#     except Exception as e:
#         app.logger.error(f"Failed to delete the image for series {series_id}: {e}")
#         return {"result": "KO", "error": "Failed to delete image"}, 500
#
# def update_thumbnail(series_id: int, thumbnail: str, cursor: sqlite3.Cursor) -> Tuple[Dict[str, str], int]:
#     return {"status": "KO", "error": "Not implemented yet"}, 501


def get_author_id(author: Dict[str, Union[str, int]], cursor: sqlite3.Cursor) -> Tuple[List[int], int]:
    try:
        id_mu = author.get("id_mu")
        id_dex = author.get("id_dex")
        id_mal = author.get("id_mal")
        if not (id_mu or id_dex or id_mal):
            return [], 400

        cursor.execute("SELECT id FROM authors WHERE id_mu = ? OR id_dex = ? OR id_mal = ?", (id_mu, id_dex, id_mal))
        rows = cursor.fetchall()
        if not rows:
            cursor.execute("INSERT INTO authors (id_mu, id_dex, id_mal) VALUES (?, ?, ?) RETURNING id", (id_mu, id_dex, id_mal))
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