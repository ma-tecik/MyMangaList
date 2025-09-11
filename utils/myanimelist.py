from flask import current_app as app
import requests
from typing import Dict, Any, Tuple


def get_id(url: str) -> int:
    parts = url.split("/manga/")[1].split("/")
    id_ = parts[0]
    return int(id_)


def series(id_mal: int) -> Tuple[Dict[str, Any], int]:
    if not app.config.get('MAL_CLIENT_ID'):
        return {}, 403
    try:
        response = requests.get(f"https://api.myanimelist.net/v2/manga/{id_mal}", params={
            "fields": "alternative_titles,start_date,synopsis,updated_at,media_type,genres,num_volumes,num_chapters,authors{first_name,last_name}"},
                                headers={"X-MAL-CLIENT-ID": app.config['MAL_CLIENT_ID']})
    except Exception as e:
        app.logger.error(e)
        return {}, 500

    data = response.json()
    os_a = False

    alt_titles = data.get("alternative_titles", {}).get("synonyms", [])
    for lang in ["en", "ja"]:
        t = data.get("alternative_titles", {}).get(lang)
        if t:
            alt_titles.append(t)

    genres = []

    type_ = data.get("media_type", "")
    if type_ in ["manga", "manhwa", "manhua", "novel"]:
        type_ = type_.capitalize()
    elif type_ == "light_novel":
        type_ = "Novel"
    elif type_ == "oel":
        type_ = "OEL"
    elif type_ == "doujinshi":
        type_ = "Manga"
        genres.append("Doujinshi")
    elif type_ == "one_shot":
        type_ = "Manga"
        os_a = True
    else:
        type_ = "Other"

    vol_ch = []
    if data.get("num_volumes"):
        vol_ch.append(f"{data['num_volumes']} Volumes")
    if data.get("num_chapters"):
        vol_ch.append(f"{data['num_chapters']} Chapters")
    vol_ch = ", ".join(vol_ch)
    if vol_ch:
        vol_ch += " (Complete)"

    genre_erotica = False
    valid_genres = ["Josei", "Seinen", "Shoujo", "Shounen", "Hentai", "Ecci", "Villainess", "Action", "Adventure",
                    "Comedy", "Drama", "Fantasy", "Harem", "Reverse Harem", "Historical", "Horror", "Martial Arts",
                    "Mecha", "Mystery", "Psychological", "Romance", "Sci-fi", "Slice of Life", "Sports", "Supernatural"]
    genre_map = {"Award Winning": "Award", "Boys Love": "BL", "Girls Love": "GL", "School": "School Life",
                 "Workplace": "Office"}
    genre_map_1 = {"Isekai": "isekai", "Reincarnation": "isekai", "Showbiz": "Showbiz", "Idols (Female)": "Showbiz",
                   "Idols (Male)": "Showbiz"}
    for i in data.get("genres"):
        j = i.get("name")
        if j in valid_genres:
            genres.append(j)
        elif j in genre_map:
            genres.append(genre_map[j])
        elif j in genre_map_1:
            if genre_map_1[j] not in genres:
                genres.append(genre_map_1[j])
        elif j == "Erotica":
            genre_erotica = True

    if genre_erotica and not any(g in genres for g in ["BL", "GL"]):
        if "Josei" in genres or "Shoujo" in genres:
            genres.append("Smut")
        elif "Seinen" in genres or "Shounen" in genres:
            genres.append("Borderline H")

    authors = []
    for a in data.get("authors", []):
        a_map = {"Story & Art": "Both", "Art": "Artist", "Story": "Author"}
        author_info = {
            "ids": {"mal": a.get("node", {}).get("id")},
            "name": f"{a.get('node', {}).get('first_name', '')} {a.get('node', {}).get('last_name', '')}".strip(),
            "type": a_map.get(a.get("role", ""))
        }
        authors.append(author_info)

    import datetime
    updated_at_str = data["updated_at"]
    dt = datetime.datetime.fromisoformat(updated_at_str.replace("Z", "+00:00"))
    timestamp = int(dt.timestamp())

    data_final = {
        "ids": {"mal": id_mal},
        "title": data.get("title", ""),
        "alt_titles": alt_titles,
        "type": type_,
        "description": data.get("synopsis", ""),
        "vol_ch": vol_ch,
        "is_md": False,
        "genres": genres,
        "year": data.get("start_date", "")[:4],
        "authors": authors,
        "os_a": os_a,
        "thumbnail": data.get("main_picture", {}).get("medium"),
        "timestamp": {"mal": timestamp},
    }
    return data_final, 200
