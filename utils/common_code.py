from flask import current_app as app
from typing import List, Dict, Any
import re


def base36(num: int) -> str:
    alphabet = "0123456789abcdefghijklmnopqrstuvwxyz"
    result = ""
    if 0 <= num < 36:
        return alphabet[num]
    while num > 0:
        num, i = divmod(num, 36)
        result = alphabet[i] + result
    return result


def author_type_merger(authors: List[dict]) -> List[dict]:
    merged_authors = {}
    if any(a.get("ids", {}).get(k) for a in authors for k in ("mu", "dex", "mal")):
        for author in authors:
            author_id = next((author.get("ids").get(k) for k in ("mu", "dex", "mal") if author.get("ids").get(k)), None)
            if author_id and author_id in merged_authors:
                merged_authors[author_id]["type"] = "Both"
            else:
                merged_authors[author_id] = author
    else:
        for author in authors:
            name = author["name"]
            type_ = author["type"].capitalize()
            if name not in merged_authors:
                merged_authors[name] = {"name": name, "type": type_}
            else:
                merged_authors[name]["type"] = "Both"
    return list(merged_authors.values())


def author_id_merger(authors: List[dict], count, series_ids) -> List[dict]:
    merged_authors = []
    type_groups = {
        "Both": [a for a in authors if a.get("type") == "Both"],
        "Author": [a for a in authors if a.get("type") == "Author"],
        "Artist": [a for a in authors if a.get("type") == "Artist"]
    }
    for author_type, author_list in type_groups.items():
        if len(author_list) == count:
            ids = {}
            for a in author_list:
                for k, v in a.get("ids").items():
                    if k in ids and ids[k] != v:
                        app.logger.warning(f"Conflict. Series:{series_ids} Authors:{authors}")
                        return authors
                    ids[k] = v
            merged_author = {"type": author_type, "name": author_list[0]["name"], "ids": ids}
            merged_authors.append(merged_author)
        else:
            merged_authors.extend(author_list)
    return merged_authors


def valid_ids(ids: Dict[str, Any], reduced: bool = False) -> Dict[str, Any]:
    valid_keys = ("mu", "dex", "mal")
    if not reduced:
        valid_keys += ("bato", "line")
    ids = {k: v for k, v in ids.items() if k in valid_keys and v is not None}
    if not ids:
        return {}
    if any(not value.isdigit() for value in [ids[k] for k in ["mal", "bato"] if k in ids]):
        return {}
    if "line" in ids and not (re.fullmatch(r"[o]{1}:[0-9]{4}", ids["line"]) or re.fullmatch(r"[c]{1}:[0-9]{6}", ids["line"])):
        return {}
    if "mu" in ids and not re.fullmatch(r"[0-9a-z]+", ids["mu"]):
        return {}
    if "dex" in ids and not re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", ids["dex"]):
        return {}
    return ids
