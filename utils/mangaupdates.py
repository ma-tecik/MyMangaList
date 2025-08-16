from flask import current_app as app
from utils.detect_language import detect_language
from utils.common_code import author_type_merger, base36
from utils.mangaupdates_worker import worker
from utils.line import get_id as get_id_line
from typing import Dict, Any, Tuple, Union
import requests
import re


def _extract_line_id(t: str) -> int:
    match = re.search(r"(https?://)?www\.webtoons\.com\S*", t)
    if match:
        l = match.group(0)
        id_ = get_id_line(l)
        if id_:
            return id_
    return 0


def _id_from_old_url(old_url: str) -> str:
    try:
        response = requests.get(old_url, allow_redirects=True)
        new_url = response.url
        return new_url.split("/series/")[1].split("/")[0]
    except Exception as e:
        app.logger.error(f"for {old_url}: {e}")
        return ""


def get_id_url(url: str) -> str:
    if "/series/" in url:
        id_ = url.split("/series/")[1].split("/")[0]
    elif "/series.html" in url or type(url) == int:
        id_ = _id_from_old_url(url) if url else ""
    else:
        app.logger.warning(f"Invalid URL format: {url}")
        return ""
    return id_

def get_id_old(id_: Union[str, int]) -> str:
    if id_.isdigit():
        return _id_from_old_url("https://www.mangaupdates.com/series.html?id=" + str(id_))
    elif isinstance(id_, str):
        return id_
    return ""

def series(id_mu36: str) -> Tuple[Dict[str, Any], int]:
    id_mu = int(id_mu36, 36)

    try:
        response = requests.get(f"https://api.mangaupdates.com/v1/series/{id_mu}")
    except Exception as e:
        app.logger.error(f"Fetching data for ID{id_mu36}: {e}")
        return {"status": "KO", "error": "Failed to fetch details from MangaUpdates"}, 502

    if response.status_code == 404:
        app.logger.info(f"Series not found for ID:{id_mu36}")
        return {"status": "KO", "error": "Series not found"}, 404
    if response.status_code != 200:
        app.logger.error(f"Error fetching data for ID:{id_mu36}, status code: {response.status_code}")
        return {"status": "KO", "error": "Series not found"}, response.status_code

    data = response.json()

    accepted_languages = app.config["TITLE_LANGUAGES"]

    type_map = {"Manga": ["ja"], "Manhwa": ["ko"], "Manhua": ["zh-CN"], "OEL": [],
                "Vietnamese": ["vi"], "Malaysian": ["ms"], "Indonesian": ["id"],
                "Novel": ["ja", "ko", "zh-CN"], "Artbook": ["ja", "ko", "zh-CN"]}
    _type = data["type"]
    if _type in type_map:
        accepted_languages.extend(type_map[_type])
        type_ = _type
    elif _type == "Doujinshi":
        type_ = "Manga"
        accepted_languages.extend(type_map[type_])
    else:
        type_ = "Other"

    alt_titles_all = []
    alt_titles = []
    if "associated" in data:
        alt_titles_all = [item["title"] for item in data["associated"]]
    for name in alt_titles_all:
        lang, confidence = detect_language(name)
        if confidence and lang in accepted_languages:
            alt_titles.append(name)

    authors = []
    for author in data["authors"]:
        author_info = {
            "ids": {"mu": base36(author.get("author_id"))},
            "name": author.get('name'),
            "type": author.get('type')
        }
        authors.append(author_info)
    authors = author_type_merger(authors)

    genres = worker([i['genre'] for i in data['genres']], data["categories"])

    os_a = False
    # Author ID of Anthology = 6713743855 (3316twv)
    if ("Os Coll." in genres or data.get("type") == "Doujinshi" or
            any(author_.get("author_id") == "3316twv" for author_ in authors)):
        os_a = True

    ids: Dict[str, Any] = {'mu': id_mu36}
    if id_line := _extract_line_id(data["title"]):
        ids['line'] = id_line

    data_final = {
        "ids": ids,
        "title": data["title"],
        "alt_titles": alt_titles,
        "type": type_,
        "description": data["description"],
        "vol_ch": data["status"],
        "is_md": True,
        "genres": genres,
        "year": data["year"],
        "authors": authors,
        "os_a": os_a,
        "thumbnail": data["image"]["url"]["original"],
        "timestamp": {"mu": data["last_updated"]["timestamp"], }
    }
    return data_final, 200


# def search(text_: str) -> list:
#     response = requests.post("https://api.mangaupdates.com/v1/series/search", json={"search": text_, "perpage": 5})
#     response = response.json()
#
#     results = []
#     for item in response['results']:
#         data = item['record']
#
#         url = data['url']
#         id_mu36 = url.split("/series/")[1].split("/")[0]
#
#         alt_names = []
#         if item['hit_title'] != data['title']:
#             alt_names.append(data['hit_title'])
#
#         data_final = {
#             'ids': {'mu': id_mu36},
#             'title': data['title'],
#             'alt_names': alt_names,
#             'type': data['type'],
#             'description': data['description'],
#             'md': True,
#             'year': data['year'],
#             'rating': data['bayesian_rating'],
#             'timestamp_mu': data['last_updated']['timestamp'],
#             'os_a': False,
#             'image_url': data['image']['url']['original'],
#         }
#
#         results.append(data_final)
#
#     return results
#
#
#
# def author(author_id: str) -> Dict[str, Any]:
#     response = requests.get(f"https://api.mangaupdates.com/v1/author/{author_id}")
#     data = response.json()
#
#     if 'error' in data:
#         raise ValueError(f"Author not found: {author_id}")
#
#     author_data = {
#         'ids': {'mu': author_id},
#         'name': data['name'],
#         'type': data['type'],
#         'image_url': data['image']['url']['original'],
#         'description': data['description'],
#         'timestamp': data['last_updated']['timestamp'],
#         'md': True,
#     }
#     return author_data


if __name__ == "__main__":
    # Test the series function
    text = "One Piece"
    # results = search(text)
    # id_mu_ = results[0]['id']['mu']
    id_mu_ = "vy4abhh"
    manga_data = series(id_mu_)
    print(manga_data)
