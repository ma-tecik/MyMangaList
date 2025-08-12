from flask import current_app as app
from webtoon_api import WebtoonApi
from typing import Dict, Any, Tuple, Optional

api = WebtoonApi()


def get_id(url: str) -> int:
    part = url.split("title_no=")[1] if "title_no=" in url else url.split("titleNo=")[1]
    id_ = part.split("&")[0] if "&" in part else part.split("?")[0] if "?" in part else part
    return int(id_)


def series(id_line: int) -> Tuple[Dict[str, Any], int]:
    try:
        data = api.titleInfo(titleNo=id_line, serviceZone="GLOBAL", language="en", platform="APP_ANDROID").get(
            "titleInfo")
    except Exception as e:
        app.logger.error(f"Fetching data for ID {id_line}: {e}")
        return {"status": "KO", "error": "Failed to  fetch details from Line Webtoon"}, 502

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


def get_thumbnail(thumbnail: str) -> Optional[bytes]:
    try:
        image = api.get_static_content(thumbnail)
        return image
    except Exception as e:
        app.logger.error(f"For {thumbnail}: {e}")
        return None
