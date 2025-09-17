from flask import current_app as app
import sqlite3
from typing import Tuple, Dict, Any, List


def get_author(id_: int, cursor: sqlite3.Cursor) -> Tuple[Dict[str, Any], int]:
    try:
        cursor.execute(f"SELECT * FROM authors WHERE id = ?", (id_,))
        a = cursor.fetchone()
        if not a:
            return {"result": "KO", "error": "No author found"}, 404
        author = {
            "id": a[0],
            "ids": {
                "mu": a[1],
                "dex": a[2],
                "mal": a[3],
            },
            "name": a[4],
            "series": {}
        }
        cursor.executemany("SELECT COUNT(*) FROM series_authors WHERE author_id = ? and author_type = ?",
                           [(id_, i) for i in ["Author", "Artist", "Both"]])
        series = cursor.fetchall()
        for i in ["Author", "Artist", "Both"]:
            author["series"]["as_" + i.lower()] = series[["Author", "Artist", "Both"].index(i)][0]
        return author, 200
    except Exception as e:
        app.logger.error(e)
        return {"result": "KO", "error": "Internal error"}, 500


def get_authors(page: int, cursor: sqlite3.Cursor) -> List[Dict[str, Any]]:
    try:
        per_page = 100
        offset = (page - 1) * per_page
        cursor.execute("SELECT id, name FROM authors LIMIT ? OFFSET ?", (per_page, offset))
        _authors = cursor.fetchall()

        authors = []
        for a in _authors:
            cursor.execute("SELECT COUNT(*) FROM series_authors WHERE author_id = ?", (a[0],))
            authors.append({"id": a[0],
                            "name": a[1],
                            "series": cursor.fetchone()[0]})
        return authors
    except Exception as e:
        app.logger.error(e)
        return []
