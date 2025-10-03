from flask import current_app as app
from utils.common_db import update_ratings, update_user_ratings, add_series_data
from utils.external import series_data_external
from utils.mangadex import search
from utils.mangaupdates import get_id_old as get_id_mu
from time import sleep, time
import requests
import sqlite3
from typing import List, Dict, Tuple, Union

base_url = "https://api.mangadex.org/"
auth_url = "https://auth.mangadex.org/realms/mangadex/protocol/openid-connect/token"


def dex_authenticate() -> Dict[str, Union[str, int]]:
    try:
        s = ("USERNAME", "PASSWORD", "CLIENT_ID", "SECRET")
        u = [app.config.get(f"DEX_{i}") for i in s]
        if not all(i for i in u):
            app.logger.warning("Mangadex integration is enabled but some credentials are missing.")
            return {}
        payload = {
            "grant_type": "password",
            "username": u[0],
            "password": u[1],
            "client_id": u[2],
            "client_secret": u[3]
        }
        response = requests.post(auth_url, data=payload)
        timestamp = time()
        if response.status_code != 200:
            app.logger.error(f"Failed to authenticate with Mangadex: {response.status_code}")
            return {}
        data = response.json()
        tokens = {"access_token": data["access_token"],
                  "refresh_token": data["refresh_token"],
                  "expiration": int(timestamp) + 880}
        return tokens
    except Exception as e:
        app.logger.error(e)
        return {}


def dex_refresh_token(tokens: Dict[str, Union[str, int]]) -> Tuple[Dict[str, Union[str, int]], Dict[str, str]]:
    try:
        s = ("CLIENT_ID", "CLIENT_SECRET")
        u = [app.config[f"DEX_{i}"] for i in s]
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": tokens["refresh_token"],
            "client_id": u[0],
            "client_secret": u[1]
        }
        timestamp = time()
        response = requests.post(auth_url, data=payload)
        if response.status_code != 200:
            app.logger.error(f"Failed to refresh Mangadex token: {response.status_code}")
            return {}, {}
        access_token = response.json()["access_token"]
        tokens["access_token"] = access_token
        tokens["expiration"] = int(timestamp) + 880
        headers, _ = dex_get_headers(tokens)
        if not headers:
            return {}, {}
        return tokens, headers
    except Exception as e:
        app.logger.error(e)
        return {}, {}


def dex_get_headers(tokens: Dict[str, Union[str, int]]) -> Tuple[Dict[str, str], int]:
    try:
        url = base_url + "user/me"
        token = tokens.get("access_token")
        if not token:
            return {}, 500
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        response = requests.get(url, headers=headers)
        if response.status_code == 401:
            app.logger.warning("Mangadex token is invalid or expired.")
            return {}, 401
        return headers, 200
    except Exception as e:
        app.logger.error(e)
        return {}, 500


def dex_get_lists(headers) -> Tuple[Dict[str, List[str]], int]:
    try:
        url = base_url + "manga/status"
        for attempt in range(3):
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()["statuses"]
                break
            if response.status_code == 401:
                return {}, 401
            if attempt == 2:
                return {}, 502
            sleep(2)
        status_map = {"on_hold": "on-hold", "plan_to_read": "plan-to", "re_reading": "reading"}
        lists = {"plan-to": [], "reading": [], "completed": [], "dropped": [], "on-hold": []}
        for k, v in data.items():
            if v in status_map:
                v = status_map[v]
            lists[v].append(k)
        return lists, 200
    except Exception as e:
        app.logger.error(e)
        return {}, 500


def dex_start() -> Tuple[Dict[str, str], Dict[str, str], Dict[str, List[str]]]:
    try:
        tokens = dex_authenticate()
        if not tokens:
            return {}, {}, {}
        headers, s = dex_get_headers(tokens)
        if s == 200:
            lists, s = dex_get_lists(headers)
            if s == 200:
                return tokens, headers, lists
    except Exception as e:
        app.logger.error(e)
    return {}, {}, {}


def dex_update_ratings(lists, headers) -> bool:
    try:
        url = base_url + "manga/ratings"
        url_user = base_url + "rating"

        ratings = []
        ids = [i for sublist in lists.values() for i in sublist]
        for attempt in range(3):
            r = requests.get(url, headers=headers, json=ids)
            if r.status_code == 200:
                r = r.json()["statistics"]
                ratings.extend([{"id": k, "rating": v["rating"]["bayesian"]} for k, v in r.items()])
                break
            if r.status_code == 401 or attempt == 2:
                return False
        if not ratings:
            return False

        user_ratings = []
        for attempt in range(3):
            r = requests.get(url_user, headers=headers)
            if r.status_code == 200:
                r = r.json()["ratings"]
                user_ratings.extend([{"id": i, "rating": i["rating"]} for i in r])
                break
            elif r.status_code == 401 or attempt == 2:
                return False

        errors = 0
        _, s = update_ratings("dex", ratings)
        if s != 200:
            errors += 1
        if user_ratings:
            _, s = update_user_ratings("dex", user_ratings)
            if s != 200:
                errors += 1

        if errors == 0:
            return True
        else:
            return False
    except Exception as e:
        app.logger.error(e)
        return False


def dex_sync_lists(lists) -> Dict[str, str]:
    try:
        conn = sqlite3.connect("data/mml.sqlite3")
        cursor = conn.cursor()
        ids = [i for sublist in lists.values() for i in sublist]
        query = f"SELECT id_dex, status FROM series WHERE id_dex IS NOT NULL and integration = 1 AND id_dex IN ({','.join(['?'] * len(ids))})"
        cursor.execute(query, ids)
        db = {m[0]: m[1] for m in cursor.fetchall()}

        add_to_db = {}
        to_update = {}
        status_map = {"on_hold": "on-hold", "plan_to_read": "plan-to", "re_reading": "reading"}
        status_map_reverse = {"plan-to": "plan_to_read", "one-shots": "completed", "on-hold": "on_hold",
                              "ongoing": "plan_to_read"}
        for k, v in db.items():
            if v in status_map_reverse:
                v = status_map_reverse[v]
            if k in lists and lists[v] == k:
                continue
            to_update[k] = v
        for k, v in lists.items():
            if k not in db:
                v = status_map[v] if v in status_map else v
                add_to_db[k] = v

        for k, v in add_to_db.items():
            r, s = series_data_external({"dex": k})
            if s != 200:
                app.logger.info(f"Skipping {k}, ↑")
                continue

            query = "SELECT id FROM series WHERE id_dex = ?"
            params = [k]
            for m, n in r["ids"].items():
                if m == "dex":
                    continue
                query += f" OR id_{m} = ?"
                params.append(n)

            cursor.execute(query, params)
            if len(cursor.fetchall()) >= 2:
                app.logger.warning(f"Multiple entries found for Title:{r['title']}, IDs: ({r['ids']}). Skipping.")
                continue
            if cursor.fetchone():
                id_ = cursor.fetchone()[0]
                query = "UPDATE series SET "
                params = []
                for m, n in r["ids"].items():
                    query += f"id_{m} = ?, "
                    params.append(n)
                if r["timestamp"].get("mu"):
                    query += "timestamp_mu = ?, "
                    params.append(1)
                else:
                    query += "timestamp_dex = ?, "
                    params.append(1)
                query = query.rstrip(", ") + " WHERE id = ?"
                cursor.execute(query, params + [id_])
            else:
                cursor.execute(f"""INSERT INTO series
                (id_mu, id_dex, id_mal, id_line, title, type, description, vol_ch, is_md, status, year, timestamp_status)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?) returning id""",
                               (r["ids"].get("mu"), k, r["ids"].get("mal"), r["ids"].get("line"), r["title"],
                                r["type"], r["description"], r["vol_ch"], 1, add_to_db[k], r["year"], 1))
                id_ = cursor.fetchone()[0]
                add_series_data(id_, r, cursor)
            conn.commit()
        conn.close()
        return to_update
    except Exception as e:
        app.logger.error(e)
        return {}


def dex_sync_lists_forced(tokens: Dict[str, Union[str, int]], headers: Dict[str, str], to_update: Dict[str, str], ) -> Tuple[Dict[str, str], Dict[str, str]]:
    try:
        url = base_url + "manga/"
        w = 1
        for k, v in to_update.items():
            if int(time()) >= tokens["expiration"]:
                tokens, headers = dex_refresh_token(tokens)
                if not headers:
                    return {}, {}
                w = 1
            if w >= 3:
                sleep(1)
                w = 0
            response = requests.get(url + k + "status", headers=headers, json={"status": v})
            if response.status_code != 200:
                app.logger.error(f"Failed to update status for {k}: {response.status_code}")
            w += 1
    except Exception as e:
        app.logger.error(e)
    return tokens, headers


def dex_fetch_ids() -> bool:
    try:
        conn = sqlite3.connect("data/mml.sqlite3")
        cursor = conn.cursor()
        cursor.execute("SELECT title, id_mu, id, id_mal FROM series WHERE id_mu IS NOT NULL AND id_dex is NULL")
        series = cursor.fetchall()
        to_update = []
        to_update_mal = []
        w = 0
        for title, id_mu, id_, id_mal in series:
            if w >= 3:
                sleep(1)
                w = 0
            results = search(title)
            w += 1
            if not results:
                continue
            for i in results:
                result_id_mu = get_id_mu(i["attributes"].get("links", {}).get("mu"))
                if result_id_mu == id_mu:
                    app.logger.info(f"For {title} (MU_ID:{id_mu}): Found DEX_ID {i["id"]}")
                    to_update.append((i["id"], id_))
                    if not id_mal and (id_mal := i["attributes"].get("links", {}).get("mal")):
                        app.logger.info(f"For {title} (MU_ID:{id_mu}): Found MAL_ID {id_mal}")
                        to_update_mal.append((id_mal, id_))
                    break
        if to_update:
            cursor.executemany("UPDATE series SET id_dex = ? WHERE id = ?", to_update)
            conn.commit()
        if to_update_mal:
            for i in to_update_mal[:]:
                cursor.execute("SELECT 1 FROM series WHERE id_mal = ? LIMIT 1", (i[0],))
                if cursor.fetchone():
                    app.logger.info(f"Skipping existing entry with MAL ID (merge could be required): {i[0]}")
                    to_update_mal.remove(i)
                    continue
            if to_update_mal:
                cursor.executemany("UPDATE series SET id_mal = ? WHERE id = ?", to_update_mal)
                conn.commit()
        conn.close()
        return True
    except Exception as e:
        app.logger.error(e)
    return False
