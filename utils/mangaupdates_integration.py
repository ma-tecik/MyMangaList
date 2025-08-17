from flask import current_app as app
from utils.external import update_ratings, update_user_ratings
from utils.common_code import base36
from utils.common_db import series_move_batch
from time import sleep
import requests
from typing import List

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


def get_ids_scanlated(list_id: str, headers) -> List[int]:
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


def get_ids_not_scanlated(list_id: str, headers) -> List[int]:
    series_all = get_list(list_id, headers)
    series_scanlated = get_ids_scanlated(list_id, headers)
    if not series_all or not series_scanlated:
        return []
    elif len(series_all) == len(series_scanlated):
        return []
    else:
        return [i["record"]["series_id"] for i in series_all if i["record"]["series_id"] not in series_scanlated]


# payload =  [{"series": {"id": i}, "list_id": list_id} for i in series_ids]
def move_series_batch(payload, headers) -> bool:
    try:
        url = base_url + "lists/series/update"
        requests.post(url, headers=headers, json=payload)
        return True
    except Exception as e:
        app.logger.error(e)
        return False


def mu_update_ratings() -> bool:
    try:
        headers = get_headers()
        if not headers:
            return False
        ratings = []
        user_ratings = []
        for i in ("PLAN_TO_READ", "READING", "COMPLETED", "ONE-SHOTS", "DROPPED", "ON_HOLD", "ONGOING"):
            j = app.config.get(f"MU_LIST_{i}")
            if not j:
                return False
            data = get_list(j, headers)
            if not data:
                return False
            for m in data:
                id_ = base36(m["record"]["id"])
                rating = m["metadata"]["series"].get("bayesian_rating", None)
                user_rating = m["metadata"].get("user_rating", None)
                if not rating is None:
                    ratings.append({"id": id_, "rating": rating})
                if not user_rating is None:
                    user_ratings.append({"id": id_, "rating": user_rating})
            if i != "ONGOING":
                sleep(1)
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


def mu_updates_ongoing() -> bool:
    try:
        headers = get_headers()
        if not headers:
            return False
        ongoing = app.config.get(f"MU_LIST_ONGOING")
        plan_to_read = app.config.get(f"MU_LIST_PLAN_TO_READ")
        to_move = get_ids_scanlated(ongoing, headers)
        payload = []
        if to_move:
            payload.extend([{"series": {"id": i}, "list_id": plan_to_read} for i in to_move])
            to_move = [base36(i) for i in to_move]
            series_move_batch(to_move, "mu", "Ongoing", "Plan_to_read")
            sleep(10)
        to_move = get_ids_not_scanlated(ongoing, headers)
        if to_move:
            payload.extend([{"series": {"id": i}, "list_id": ongoing} for i in to_move])
            to_move = [base36(i) for i in to_move]
            series_move_batch(to_move, "mu", "Plan_to_read", "Ongoing")
        if payload:
            move_series_batch(payload, headers)
        return True
    except Exception as e:
        app.logger.error(e)
        return False


