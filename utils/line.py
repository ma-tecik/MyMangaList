from flask import current_app as app
from webtoon_api import WebtoonApi
from typing import Dict, Any, Tuple, Optional

api = WebtoonApi()


def get_id(url: str) -> str:
    part = url.split("title_no=")[1] if "title_no=" in url else url.split("titleNo=")[1]
    id_ = part.split("&")[0] if "&" in part else part.split("?")[0] if "?" in part else part
    if "challenge" in url or "canvas" in url:
        id_ = "c:" + id_
    else:
        id_ = "o:" + id_
    return id_


def series(id_line: str) -> Tuple[Dict[str, Any], int]: # TODO: Add support for canvas
    try:
        if id_line.startswith("O:"):
            data = api.titleInfo(titleNo=id_line[2:], serviceZone="GLOBAL", language="en", platform="APP_ANDROID").get(
                "titleInfo")
            if data["writingAuthorName"] == data["pictureAuthorName"]:
                authors = [{"name": data["writingAuthorName"], "type": "Both"}]
            else:
                authors = [{"name": data["writingAuthorName"], "type": "Author"},
                           {"name": data["pictureAuthorName"], "type": "Artist"}]
            return {
                "ids": {"line": id_line},
                "title": data["title"],
                "description": data["synopsis"],
                "is_md": False,
                "genres": ["Webtoon", data["representGenre"].capitalize()],
                "authors": authors,
                "thumbnail": "line://" + data["thumbnail"]
            }, 200
        elif id_line.startswith("c:"):
            return {}, 501
        else:
            return {}, 400
    except Exception as e:
        app.logger.error(f"Fetching data for ID {id_line}: {e}")
        return {"status": "KO", "error": "Failed to  fetch details from Line Webtoon"}, 502


def get_thumbnail(thumbnail: str) -> Optional[bytes]:
    try:
        image = api.get_static_content(thumbnail)
        return image
    except Exception as e:
        app.logger.error(f"For {thumbnail}: {e}")
        return None
