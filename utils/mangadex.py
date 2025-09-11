from flask import current_app as app
from utils.common_code import author_type_merger
from utils.mangadex_worker import worker
from typing import Dict, Any, Tuple
import requests
from utils.line import get_id as get_id_line
from utils.mangaupdates import get_id_old as get_id_mu


def get_id(url: str) -> str:
    parts = url.split("/title/")[1].split("/")
    id_ = parts[0]
    return id_


def series(id_dex: str) -> Tuple[Dict[str, Any], int]:
    try:
        response = requests.get(
            f"https://api.mangadex.org/manga/{id_dex}?includes[]=author&includes[]=artist&includes[]=cover_art")
    except Exception as e:
        app.logger.error(f"Fetching data for ID {id_dex}: {e}")
        return {"status": "KO", "error": "Failed to  fetch details from Mangadex"}, 502
    if response.status_code == 404:
        app.logger.info(f"Series not found for ID {id_dex}")
        return {"status": "KO", "error": "Series not found"}, 404
    if response.status_code != 200:
        app.logger.error(f"Error fetching data for ID {id_dex}, status code: {response.status_code}")
        return {"status": "KO", "error": "Unexpected error"}, response.status_code

    data = response.json()
    data = data["data"]

    authors = []
    cover_filename = None
    for i in data["relationships"]:
        if i["type"] in ["author", "artist"]:
            author_info = {
                "ids": {"dex": i.get("id")},
                "name": i.get("attributes", {}).get("name"),
                "type": i["type"].capitalize()
            }
            authors.append(author_info)
        elif i["type"] == "cover_art":
            cover_filename = i["attributes"]["fileName"]
    authors = author_type_merger(authors)

    genres, type_, os_a, accepted_languages = worker(data["attributes"].get("tags", []),
                                                     data["attributes"]["publicationDemographic"],
                                                     data["attributes"]["contentRating"],
                                                     data["attributes"]["originalLanguage"])
    accepted_languages.extend(app.config["TITLE_LANGUAGES"])

    alt_titles = []
    if "altTitles" in data["attributes"]:
        for alt_title in data["attributes"]["altTitles"]:
            for lang, title in alt_title.items():
                if lang in accepted_languages:
                    alt_titles.append(title)

    thumbnail = f"https://uploads.mangadex.org/covers/{id_dex}/{cover_filename}.256.jpg"

    import datetime
    updated_at_str = data["attributes"]["updatedAt"]
    dt = datetime.datetime.fromisoformat(updated_at_str.replace("Z", "+00:00"))
    timestamp = int(dt.timestamp())

    data_final = {
        "ids": {"dex": id_dex},
        "title": data["attributes"]["title"].get("en"),
        "alt_titles": alt_titles,
        "type": type_,
        "description": data["attributes"]["description"].get("en", ""),
        "is_md": True,
        "genres": genres,
        "year": data["attributes"].get("year"),
        "authors": authors,
        "os_a": os_a,
        "thumbnail": thumbnail,
        "timestamp": {"dex": timestamp},
        "dex_status": data["attributes"].get("status"),
    }
    if id_mu := data["attributes"]["links"].get("mu"):
        data_final["ids"]["mu"] = get_id_mu(id_mu)
    if data["attributes"]["links"].get("mal"):
        data_final["ids"]["mal"] = data["attributes"]["links"]["mal"]
    if engtl := data["attributes"]["links"].get("engtl"):
        if "webtoons.com" in engtl:
            data_final["ids"]["line"] = get_id_line(engtl)
    return data_final, 200
