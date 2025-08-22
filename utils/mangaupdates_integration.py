from flask import current_app as app
from utils.external import update_ratings, update_user_ratings
from utils.common_code import base36
from utils.common_db import series_move_batch, download_thumbnail, get_author_id, add_genres, update_thumbnail
from utils.mangaupdates import series
from time import sleep
import requests
import sqlite3
from typing import List, Tuple, Dict

base_url = "https://api.mangaupdates.com/v1/"


def get_headers() -> dict:
    try:
        url = base_url
        w = True
        headers = {}
        token = app.config.get("MU_TOKEN", "")
        while w:
            if not token:
                username = app.config["MU_USERNAME"]
                password = app.config["MU_PASSWORD"]
                for attempt in range(3):
                    response = requests.put(url + "account/login",
                                            json={"username": username, "password": password})
                    if response.status_code == 200:
                        break
                    if attempt == 2:
                        raise Exception("Failed to login to MangaUpdates")
                    sleep(2)
                token = response.json()['context']['session_token']
                app.config["MU_TOKEN"] = token
                w = False
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            response = requests.get(url + "lists", headers=headers)
            if response.status_code == 200:
                lists = [i["list_id"] for i in response.json()]
                for i in ("PLAN_TO_READ", "READING", "COMPLETED", "ONE-SHOTS", "DROPPED", "ON_HOLD", "ONGOING"):
                    if not app.config[f"MU_LIST_{i}"] in lists:
                        app.logger.error(
                            f"mu lists in settings is not right, MU_LIST_{i} is not in the mangaupdates lists")
                        return {}
            else:
                token = ""
                headers = {}
        return headers
    except Exception as e:
        app.logger.error(e)
        return {}


# !!! /lists/{list_id}/search and /series/search return different responses !!!
def get_list(list_id: str, headers) -> List[dict]:
    try:
        url = base_url + f"lists/{list_id}/search"
        data = []
        for attempt in range(3):
            response = requests.get(url, headers=headers, json={"page": 1, "perpage": -1})
            if response.status_code == 200:
                data = response.json()["results"]
                break
            if attempt == 2:
                return []
            sleep(2)
        return data
    except Exception as e:
        app.logger.error(e)
        return []


def _get_ids_scanlated(list_id: str, headers) -> List[int]:
    try:
        url = base_url + f"series/search"
        ids = []
        total_hits = 0
        page = 1
        while True:
            payload = {"filter": "scanlated", "list": list_id, "page": page}
            for attempt in range(3):
                response = requests.post(url, headers=headers, json=payload)
                if response.status_code == 200:
                    break
                if attempt == 2:
                    return []
                sleep(2)
            if page == 1:
                total_hits = response.json()["total_hits"]
                if total_hits in (0, 10000):
                    return []
            ids.extend([i["record"]["series"]["id"] for i in response.json()["results"]])
            if len(ids) == total_hits:
                break
            page += 1
            sleep(1)
        return ids
    except Exception as e:
        app.logger.error(e)
        return []


def _get_ids_not_scanlated(list_id: str, headers) -> List[int]:
    series_all = get_list(list_id, headers)
    series_scanlated = _get_ids_scanlated(list_id, headers)
    if not series_all or not series_scanlated:
        return []
    elif len(series_all) == len(series_scanlated):
        return []
    else:
        return [i["record"]["series_id"] for i in series_all if i["record"]["series_id"] not in series_scanlated]


# payload =  [{"series": {"id": i}, "list_id": list_id} for i in series_ids]
def _move_series_batch(payload, headers) -> bool:
    try:
        url = base_url + "lists/series/update"
        for attempt in range(3):
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                break
            if attempt == 2:
                return False
            sleep(2)
        return True
    except Exception as e:
        app.logger.error(e)
        return False


# payload =  [{"series": {"id": i}, "list_id": list_id} for i in series_ids]
def _add_series_batch(payload, headers) -> bool:
    try:
        url = base_url + "lists/series"
        for attempt in range(3):
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                break
            if attempt == 2:
                return False
            sleep(2)
        return True
    except Exception as e:
        app.logger.error(e)
        return False


def mu_update_ratings(data: Dict[str, List[dict]]) -> bool:
    try:
        ratings = []
        user_ratings = []
        for i in data.values():
            for m in i:
                id_ = base36(m["record"]["id"])
                rating = m["metadata"]["series"].get("bayesian_rating", None)
                user_rating = m["metadata"].get("user_rating", None)
                if rating:
                    ratings.append({"id": id_, "rating": rating})
                if user_rating:
                    user_ratings.append({"id": id_, "rating": user_rating})

        errors = 0
        if ratings:
            _, s = update_ratings("mu", ratings)
            if s != 200:
                errors += 1
        if user_ratings:
            s = update_user_ratings("mu", user_ratings)
            if s != 200:
                errors += 1

        if errors == 0:
            return True
        else:
            return False
    except Exception as e:
        app.logger.error(e)
        return False


def mu_get_data_for_all() -> Tuple[Dict[str, List[dict]], dict]:
    try:
        headers = get_headers()
        if not headers:
            return {}, {}

        data = {}
        for i in ("Plan_to_read", "Reading", "Completed", "One-shot", "Dropped", "On_hold", "Ongoing"):
            list_id = app.config[f"MU_LIST_{i.upper()}"]
            data_ = get_list(list_id, headers)
            if data_:
                data[i] = data_

        if not data:
            return {}, headers  # or {} TODO: is headers necessary?
        return data, headers
    except Exception as e:
        app.logger.error(e)
        return {}, {}


def mu_update_ongoing() -> bool:
    try:
        headers = get_headers()
        if not headers:
            return False
        ongoing = app.config.get(f"MU_LIST_ONGOING")
        plan_to_read = app.config.get(f"MU_LIST_PLAN_TO_READ")
        to_move = _get_ids_scanlated(ongoing, headers)
        payload = []
        if to_move:
            payload.extend([{"series": {"id": i}, "list_id": plan_to_read} for i in to_move])
            to_move = [base36(i) for i in to_move]
            series_move_batch(to_move, "mu", "Ongoing", "Plan_to_read")
            sleep(10)
        to_move = _get_ids_not_scanlated(ongoing, headers)
        if to_move:
            payload.extend([{"series": {"id": i}, "list_id": ongoing} for i in to_move])
            to_move = [base36(i) for i in to_move]
            series_move_batch(to_move, "mu", "Plan_to_read", "Ongoing")
        if payload:
            _move_series_batch(payload, headers)
        return True
    except Exception as e:
        app.logger.error(e)
        return False


def mu_sync_lists(data: Dict[str, List[dict]], headers) -> bool:
    try:
        ids = {}
        for i in data:
            for m in data[i]:
                id_ = base36(m["record"]["id"])
                timestamp = m["record"]["time_added"]["timestamp"]
                ids[id_] = (i, timestamp)

        if not ids:
            return False

        conn = sqlite3.connect("data/mml.sqlite3")
        cursor = conn.cursor()
        cursor.executemany("SELECT id_mu, status, timestamp_status FROM series WHERE id_mu IS NOT NULL", ids.keys())
        db = {r[0]: (r[1], r[2]) for r in cursor.fetchall()}

        add_to_db = {}
        add_to_mu = {k: db[k][0] for k in db.keys() if k not in ids.keys()}
        to_update_db = {}
        to_update_mu = {}
        for k, v in ids.items():
            if k not in db:
                add_to_db[k] = v
            elif db[k][0] == v[0]:
                continue
            elif db[k][1] >> v[1]:
                to_update_mu[k] = v
            elif db[k][1] << v[1]:
                to_update_db[k] = v
            else:
                app.logger.warning(f"Skipping {k}, because status different but timestamps same")

        if to_update_db:
            query = "UPDATE series SET status = ?, timestamp_status = ? WHERE id_mu = ?"
            cursor.executemany(query, [(to_update_db[k][0], to_update_mu[1], k) for k in to_update_mu.keys()])
            conn.commit()
        if add_to_mu:
            for i in ("Plan_to_read", "Reading", "Completed", "One-shot", "Dropped", "On_hold", "Ongoing"):
                list_id = app.config[f"MU_LIST_{i.upper()}"]
                payload = [{"series": {"id": j}, "list_id": list_id} for j in add_to_mu if add_to_mu[j] == i]
                _add_series_batch(payload, headers)
                sleep(1)
        if to_update_mu:
            for i in ("Plan_to_read", "Reading", "Completed", "One-shot", "Dropped", "On_hold", "Ongoing"):
                list_id = app.config[f"MU_LIST_{i.upper()}"]
                payload = [{"series": {"id": j}, "list_id": list_id} for j in add_to_mu if add_to_mu[j] == i]
                _move_series_batch(payload, headers)
                sleep(1)
        for i in add_to_db.keys():
            try:
                r, s = series(base36(i))
                if s != 200:
                    app.logger.info(f"Skipping {i}, ↑")
                    continue
                cursor.execute(f"""INSERT INTO series
                (id_mu, id_line, title, type, description, vol_ch, id_mu, status, year, timestamp_status, timestamp_mu)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) RETURNING id""",
                               (i, r["ids"].get("line"), r.get("title"), r.get("type"),
                                r.get("description"), r.get("vol_ch"), True, add_to_db[i][0], r.get("year"),
                                add_to_db[i][1], r["timestamp"]["mu"]))
                id_ = cursor.fetchone()[0]
                _, s = download_thumbnail(id_, r["thumbnail"], cursor)
                if s != 201:
                    continue
                authors = []
                for author in r["authors"]:
                    p, s = get_author_id(author, cursor)
                    if s != 200:
                        continue
                    authors.append({"id": p[0], "type": author["type"]})
                    cursor.executemany(
                        "INSERT INTO series_authors (series_id, author_id, author_type) VALUES (?, ?, ?)",
                        [(id_, a["id"], a["type"]) for a in authors])
                add_genres(id_, r.get("genres"), cursor)
                cursor.executemany("INSERT INTO series_titles (series_id, alt_title) VALUES (?, ?)",
                                   [(id_, title) for title in r["alt_titles"]])
                conn.commit()
            except Exception as e:
                app.logger.error(e)
                continue
        conn.close()
        return True
    except Exception as e:
        app.logger.error(e)
        return False


def mu_update_series(to_update: List[str], cursor) -> bool:
    try:
        authors_to_add = []
        authors_to_update = []

        titles_to_add = []
        titles_to_delete = []

        genres_to_add = []
        genres_to_delete = []

        for m in to_update:
            r, s = series(m)
            if s != 200:
                continue
            cursor.execute(
                "SELECT title, type, description, vol_ch, year, id, id_line, automation_genres from series WHERE id_mu = ?",
                (m,))
            row = cursor.fetchone()
            id_ = row[5]

            x = 0
            to_update = {"timestamp": r["timestamp"]["mu"], }
            for i in ["title", "type", "description", "vol_ch", "year"]:
                if r[i] != row[x]:
                    to_update[i] = r[i]
                x += 1

            if len(r["ids"]) == 2 and r["ids"].get("line") != row[6]:
                to_update["id_line"] = r["ids"].get("line")

            if to_update:
                cols = ", ".join(f"{k} = ?" for k in to_update.keys())
                vals = list(to_update.values()) + [id_]
                cursor.execute(f"UPDATE series SET {cols} WHERE id = ?", vals)

            cursor.execute("SELECT url FROM series_thumbnails WHERE series_id = ?", (id_,))
            if r["thumbnail"] != cursor.fetchone()[0]:
                update_thumbnail(id_, r["thumbnail"], cursor)

            cursor.execute("""SELECT a.id_mu, sa.author_type
                              FROM series_authors sa
                                       JOIN authors a ON a.id = sa.author_id
                              WHERE sa.series_id = ?""", (id_,))
            authors = {i[0]: i[1] for i in cursor.fetchall()}
            for a in r["authors"]:
                a_id = a.get("ids", {}).get("mu")
                if not a_id:
                    app.logger.warning(f"""For series: {id_} skipping author: {a}.
                    ID_MU not found, please add the author to the MangaUpdates database.""")
                    continue
                if a_id not in authors or a["type"] != authors[a_id]:
                    r, s = get_author_id(a, cursor)
                    if s != 200:
                        app.logger.warning(f"For series: {id_} skipping author: {a}.")
                        continue
                if a_id not in authors:
                    authors_to_add.append((a["type"], id_, r[0]))
                elif a["type"] != authors[a_id]:
                    authors_to_update.append((a["type"], id_, r[0]))

            cursor.execute("SELECT alt_title FROM series_titles WHERE series_id = ?", (id_,))
            titles_db = {i[0] for i in cursor.fetchall()}
            titles_mu = set(r["alt_titles"])
            titles_to_add.extend([id_, t] for t in titles_mu - titles_db)
            titles_to_delete.extend([id_, t] for t in titles_db - titles_mu)

            if row[7]:
                cursor.execute("SELECT genre_id FROM series_genres WHERE series_id = ?", (id_,))
                genres_db = {g[0] for g in cursor.fetchall()}
                cursor.executemany("SELECT id FROM genres WHERE genre = ?", r["genres"])
                genres_mu = {g[0] for g in cursor.fetchall()}
                genres_to_add.extend([id_, g] for g in genres_mu - genres_db)
                genres_to_delete.extend([id_, g] for g in genres_db - genres_mu)

        if authors_to_add:
            cursor.executemany("INSERT INTO series_authors (author_type, series_id, author_id) VALUES (?, ?, ?)",
                               authors_to_add)
        if authors_to_update:
            cursor.executemany("UPDATE series_authors SET author_type = (?) WHERE series_id = ? AND author_id  = ?",
                               authors_to_update)
        if titles_to_add:
            cursor.executemany("INSERT INTO series_titles (series_id, alt_title) VALUES (?, ?)", titles_to_add)
        if titles_to_delete:
            cursor.execute("DELETE FROM series_titles WHERE series_id = ? AND alt_title = ?", titles_to_delete)
        if genres_to_add:
            cursor.executemany("INSERT INTO series_genres (series_id, genre_id) VALUES (?, ?)", genres_to_add)
        if genres_to_delete:
            cursor.executemany("DELETE FROM series_genres WHERE series_id = ? AND genre_id = ?", genres_to_delete)
        return True
    except Exception as e:
        app.logger.error(e)
        return False
