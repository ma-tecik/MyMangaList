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


def series(id_line: str) -> Tuple[Dict[str, Any], int]:
    try:
        if id_line.startswith("o:"):
            try:
                data = api.titleHomeMainV2(titleNo=id_line[2:], serviceZone="GLOBAL", language="en",
                                           platform="APP_ANDROID")
            except Exception as e:
                app.logger.error(f"Fetching data for ID {id_line}: {e}")
                data = None
            if not data or not isinstance(data, dict):
                return {}, 502
            data = data.get("title")
            authors = [{"name": a.get("authorName", ""), "type": "Both"} for a in data.get("authorList", [])]
            thumbnail = "line://" + data.get("posterThumbnailUrl") if data.get("posterThumbnailUrl") else ""
        elif id_line.startswith("c:"):
            try:
                data = api.challengeTitleHomeMainV1(titleNo=id_line[2:], serviceZone="GLOBAL", language="en",
                                                    platform="APP_ANDROID")
            except Exception as e:
                app.logger.error(f"Fetching data for ID {id_line}: {e}")
                data = None
            if not data or not isinstance(data, dict):
                return {}, 502
            data = data.get("challengeTitle")
            authors = [{"name": data.get("author", {}).get("authorName"), "type": "Both"}] if data.get("author") else []
            thumbnail = "line://" + data.get("thumbnailUrl") if data.get("thumbnailUrl") else ""
        else:
            return {}, 400

        genres = [data.get("representGenre", {}).get("displayName", ""), "Webtoon"]
        if data.get("mature"):
            genres.append("Mature")

        return {
            "ids": {"line": id_line},
            "title": data.get("title", ""),
            "description": data.get("synopsis", ""),
            "is_md": False,
            "genres": genres,
            "authors": authors,
            "thumbnail": thumbnail,
        }, 200
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
