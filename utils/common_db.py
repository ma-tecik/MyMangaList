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
        cursor.execute("INSERT INTO series_thumbnails (series_id, extension, url) VALUES (?, ?, ?)",
                       (series_id, ext, thumbnail))
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
            cursor.execute(f"UPDATE series_thumbnails SET extension = ?, url = ? WHERE series_id = ?",
                           (ext, thumbnail, series_id))
        with open(f"data/thumbnails/{series_id}.{old_ext}", "wb") as f:
            f.write(b"")
        with open(f"data/thumbnails/{series_id}.{ext}", "wb") as f:
            f.write(response.content)
        return {"result": "OK"}, 201
    except Exception as e:
        app.logger.error(f"Failed to update the image for series {series_id}: {e}")
        return {"result": "KO", "error": "Failed to update thumbnail"}, 500


def add_genres(id_: int, genres: List[str], cursor: sqlite3.Cursor) -> None:
    cursor.execute("SELECT id FROM genres WHERE genre IN ({})".format(", ".join("?" for _ in genres)), genres)
    genre_ids = [row[0] for row in cursor.fetchall()]
    genre_ids.sort()
    cursor.executemany("INSERT INTO series_genres (series_id, genre_id) VALUES (?, ?)",
                       [(id_, genre_id) for genre_id in genre_ids])


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
            return {"result": "KO", "error": "Series not found"}, 404
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

        ext_ids = {"mu": row["id_mu"], "dex": row["id_dex"], "mal": row["id_mal"]}
        for i, ext_id in ext_ids.items():
            if ext_id:
                cursor.execute(f"SELECT rating FROM series_ratings_{i} WHERE id_{i} = ?", (ext_id,))
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
        return {"result": "KO", "error": "Internal error"}, 500


def update_ratings(type_: str, data: List[Dict[str, Union[int, str, float]]]) -> Tuple[list, int]:
    try:
        not_exist = []
        to_create = []
        to_update = []

        conn = sqlite3.connect("data/mml.sqlite3")
        cursor = conn.cursor()

        for item in data:
            if not isinstance(item, dict):
                continue
            id_: Union[int, str] = item.get("id")
            rating = item.get("rating")
            if id_ is None or rating is None:
                continue

            try:
                rating = float(rating)
            except Exception:
                continue
            if not (1 <= rating <= 10):
                continue
            cursor.execute(f"SELECT 1 FROM series WHERE id_{type_} = ?", (id_,))
            if cursor.fetchone() is None:
                not_exist.append(str(id_))
                continue

            cursor.execute(f"SELECT rating FROM series_ratings_{type_} WHERE id_{type_} = ?", (id_,))
            row = cursor.fetchone()
            if row is None:
                to_create.append((id_, rating))
            else:
                if rating != row[0]:
                    to_update.append((rating, id_))

        if to_create:
            cursor.executemany(f"INSERT INTO series_ratings_{type_} (id_{type_}, rating) VALUES (?, ?)", to_create)
            conn.commit()
        if to_update:
            cursor.executemany(f"UPDATE series_ratings_{type_} SET rating = ? WHERE id_{type_} = ?", to_update)
            conn.commit()

        cursor.close()
        app.logger.info(f"{type_} ratings updated")
        return not_exist, 200
    except Exception as e:
        app.logger.error(e)
        return [], 500


def update_user_ratings(type_: str, data: List[Dict[str, Union[int, str, float]]]) -> bool:
    try:
        to_update = []

        conn = sqlite3.connect("data/mml.sqlite3")
        cursor = conn.cursor()

        for item in data:
            if not isinstance(item, dict):
                continue
            id_: Union[int, str] = item.get("id")
            rating = item.get("rating")
            if id_ is None or rating is None:
                continue

            try:
                rating = float(rating)
            except Exception:
                continue
            if not (1 <= rating <= 10):
                continue
            cursor.execute(f"SELECT user_rating FROM series WHERE id_{type_} = ?", (id_,))
            row = cursor.fetchone()
            if row is None:
                continue
            if row[0] != rating:
                to_update.append((id_, rating))

        if to_update:
            cursor.executemany(f"UPDATE series SET user_rating = ? WHERE id_{type_} = ?", to_update)
            conn.commit()

        cursor.close()
        app.logger.info("User ratings updated")
        return True
    except Exception as e:
        app.logger.error(e)
        return False


def add_series_data(id_: int, data: Dict[str, Any], cursor: sqlite3.Cursor) -> bool:
    try:
        download_thumbnail(id_, data["thumbnail"], cursor)
        authors_ = []
        for author in data["authors"]:
            p, s = get_author_id(author, cursor)
            if s != 200:
                return False
            authors_.append({"id": p[0], "type": author["type"]})

        authors = {}
        for author in authors_:
            a_id = author["id"]
            a_type = author["type"]
            if a_id not in authors:
                authors[a_id] = a_type
            else:
                if a_type == "Both":
                    authors[a_id] = "Both"
                elif {authors[a_id], a_type} == {"Author", "Artist"}:
                    authors[a_id] = "Both"
        cursor.executemany("INSERT INTO series_authors (series_id, author_id, author_type) VALUES (?, ?, ?)",
                           [(id_, a, t) for a, t in authors.items()])
        add_genres(id_, data.get("genres"), cursor)
        cursor.executemany("INSERT INTO series_titles (series_id, alt_title) VALUES (?, ?)",
                           [(id_, title) for title in data["alt_titles"]])

        for i in ("mu", "dex", "mal"):
            if data.get("timestamp", {}).get(i):
                cursor.execute(f"UPDATE series SET timestamp_{i} = ? WHERE id = ?", (data["timestamp"][i], id_))
                break
        else:
            for i in ("mu", "dex", "mal"):
                if i in data["ids"]:
                    cursor.execute(f"UPDATE series SET timestamp_{i} = 1 WHERE id = ?", (id_,))
                    break

        return True
    except Exception as e:
        app.logger.error(e)
        return False
