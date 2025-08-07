from flask import current_app as app
from typing import Dict, Any, Tuple
import utils.mangaupdates as mangaupdates
import utils.mangadex as mangadex
import utils.myanimelist as myanimelist
import utils.bato as bato
import utils.line as line
from utils.common_code import author_id_merger

def _merge_ids(base_ids: Dict[str, Any], new_ids: Dict[str, Any]) -> Dict[str, Any]:
    for key, value in new_ids.items():
        if key in base_ids and base_ids[key] != value:
            app.logger.info(f"Conflict in IDs for {key}. Existing: {base_ids}, New: {new_ids}")
        else:
            base_ids[key] = value
    return base_ids

def series_data_external(ids: dict) -> Tuple[Dict[str, Any], int]:
    sources = (
        ("dex", mangadex),
        ("bato", bato),
        ("mu", mangaupdates),
        ("mal", myanimelist),
        ("line", line),
    )
    http_codes = []
    data_results = {}
    for source_id, module in sources:
        if source_id in ids:
            r, s = module.series(ids[source_id])
            if s == 200:
                data_results[source_id] = r
                if source_id in ["dex", "bato", "mu"]:
                    ids = _merge_ids(ids, r["ids"])
            else:
                http_codes.append(s)

    # Priority order: mu > dex > mal > bato > line
    priority_sources = ("mu", "dex", "mal", "bato", "line",)

    for primary_source in priority_sources:
        if primary_source in data_results:
            data_final = data_results[primary_source].copy()

            # Merge data from other sources
            for other_source in data_results: # TODO: implement timestamps
                if other_source != primary_source:
                    if other_source in ["dex", "mal"]:
                        data_final["authors"].extend(data_results[other_source].get("authors", []))
                    data_final["genres"] = data_final["genres"] + [genre for genre in data_results[other_source].get("genres", []) if genre not in data_final.get("genres")]
                    data_final["alt_titles"] = data_final["alt_titles"] + [at for at in data_results[other_source].get("alt_titles", []) if at not in data_final.get("alt_titles") and at != data_final["title"]]

            data_final["authors"] = author_id_merger(data_final.get("authors", []), ids)
            data_final["id"] = ids
            return data_final, 200

    return {}, 502 if 502 in http_codes else 404 if 404 in http_codes else 500


if __name__ == "__main__":
    example_ids = {
        "dex": "8573d280-7f60-411d-b146-c97dca3c62f2",
    }
    data, status = series_data_external(example_ids)
    print(data, status)