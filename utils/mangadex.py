from flask import current_app as app
from utils.common_code import author_type_merger
from typing import Dict, Any, Tuple
import requests


def get_id(url: str) -> str:
    parts = url.split("/title/")[1].split("/")
    id_ = parts[0]
    return id_

def series(id_dex: str) -> Tuple[Dict[str, Any], int]:
    try:
        response = requests.get(f"https://api.mangadex.org/manga/{id_dex}?includes[]=author&includes[]=artist&includes[]=cover_art")
    except Exception as e:
        app.logger.error(f"Fetching data for ID {id_dex}: {e}")
        return {"status": "KO", "error": "Failed to  fetch details from Mangadex"}, 502
    if response.status_code == 404:
        app.logger.info(f"Series not found for ID {id_dex}")
        return {"status": "KO", "error": "Series not found"}, 404
    if response.status_code != 200:
        app.logger.error(f"Error fetching data for ID {id_dex}, status code: {response.status_code}")
        return {"status": "KO", "error": "Series not found"}, response.status_code

    data = response.json()
    data = data["data"]

    authors = []
    cover_filename = None
    for i in data["relationships"]:
        if i["type"] in ["author", "artist"]:
            author_info = {
                "id_dex": i.get("id"),
                "name": i.get("attributes", {}).get("name"),
                "type": i["type"].capitalize()
            }
            authors.append(author_info)
        elif i["type"] == "cover_art":
            cover_filename = i["attributes"]["fileName"]
    authors = author_type_merger(authors)


    type_ = None
    lang_map = {"ja": "Manga", "ko": "Manhwa", "zh": "Manhua", "zh-hk": "Manhua", "en": "OEL",
                     "vi": "Vietnamese", "ms": "Malaysian", "id": "Indonesian", "tl": "Filipino", "th": "Thai",
                     "fr": "French", "es": "Spanish", "de": "German"}
    original_lang = data["attributes"]["originalLanguage"]
    for lang, t in lang_map.items():
        if original_lang == lang:
            type_ = t
            break
    if not type_:
        app.logger.info(f"Original language {original_lang} not recognized for ID {id_dex}. Defaulting to 'Other'.")
        type_ = "Other"

    accepted_languages = ["en"]
    accepted_languages.extend(app.config.get("TITLE_LANGUAGES", [])) # TODO: check if this works.
    if original_lang == "ja":
        accepted_languages.extend(["ja-ro", "ja"])
    elif original_lang == "ko":
        accepted_languages.append("ko")
    elif original_lang in ["zh", "zh-hk"]:
        accepted_languages.extend(["zh", "zh-hk"])

    alt_titles = []
    if "altTitles" in data["attributes"]:
        for alt_title in data["attributes"]["altTitles"]:
            for lang, title in alt_title.items():
                if lang in accepted_languages:
                    alt_titles.append(title)

    image_url = f"https://uploads.mangadex.org/covers/{id_dex}/{cover_filename}.256.jpg"

    import datetime
    updated_at_str = data["attributes"]["updatedAt"]
    dt = datetime.datetime.fromisoformat(updated_at_str.replace("Z", "+00:00"))
    timestamp = int(dt.timestamp())

    os_a = False
    os_a_tag_ids = {
        "b13b2a48-c720-44a9-9c77-39c9979373fb",  # Doujinshi
        "51d83883-4103-437c-b4b1-731cb73d786c",  # Anthology
        "0234a31e-a729-4e28-9d6a-3f87c4966b9e"  # Oneshot
    }
    if any(tag["id"] in os_a_tag_ids for tag in data["attributes"].get("tags", [])):
        os_a = True

    data_final = {
        "ids": {"dex": id_dex},
        "title": data["attributes"]["title"].get("en"),
        "alt_titles": alt_titles,
        "type": type_,
        "description": data["attributes"]["description"].get("en", ""),
        "is_md": True,
        "genres": [], # TODO: implement genres
        "year": data["attributes"].get("year"),
        "authors": authors,
        "os_a": os_a,
        "image_url": image_url,
        'timestamps': {"dex": timestamp},
    }

    if data["attributes"]["links"].get("mu"):
        data_final["id"]["mu"] = data["attributes"]["links"]["mu"]
    if data["attributes"]["links"].get("mal"):
         data_final["id"]["mal"] = data["attributes"]["links"]["mal"]
    if not data_final.get("line") and data["attributes"]["links"].get("engtl"):
        engtl = data["attributes"]["links"]["engtl"]
        if "webtoons.com" in engtl:
            data_final["id"]["line"] = engtl.split("title_no=")[1] if "title_no=" in engtl else engtl.split("titleNo=")[1]

    return data_final, 200


if __name__ == "__main__":
    #manga_id = "c408ec80-586a-4d87-8bbc-e5e8d17a3898"
    #manga_id = "984df7d5-ae4c-43c6-aa65-737b9f37e5ef"
    manga_id = "c1c408f6-3dec-4d62-b6b3-b57e615d933c"
    manga_data = series(manga_id)
    print(manga_data)