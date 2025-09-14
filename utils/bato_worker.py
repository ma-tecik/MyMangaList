from typing import List, Tuple


def worker(genres_: List[str], original_language: str) -> Tuple[List[str], str, List[str]]:
    valid_types = {"Manga": "ja", "Manhwa": "ko", "Manhua": "zh-CN", "Artbook": ""}
    language_map = {"Japanese": ("Manga", "ja"), "Korean": ("Manhwa", "ko"), "Chinese": ("Manhua", "zh-CN"),
                    "English": ("OEL", "")}
    valid_genres = [
        "Hentai", "Smut", "Adult", "Mature", "Ecchi", "Doujinshi", "Action", "Adventure", "Comedy", "Drama",
        "Fantasy", "Harem", "Reverse Harem", "Historical", "Horror", "Martial Arts", "Mecha", "Mystery",
        "Psychological", "Romance", "Sci-fi", "Slice of Life", "Sports", "Supernatural", "Tragedy", "Anthology",
        "Villainess", "Revenge", "Age Gap", "Showbiz", "Incest", "Harlequin", "4-Koma"
    ]
    genre_map = {
        "Oneshot": "One-shot", "Josei(W)": "Josei", "Seinen(M)": "Seinen", "Shoujo(G)": "Shoujo",
        "Shounen(B)": "Shounen", "Contest winning": "Award", "Childhood Friends": "Childhood F.",
        "Office Workers": "Office", "Regression": "Time Rewind", "Reverse Isekai": "Reverse isekai",
    }
    genre_map1 = {
        "Yuri(GL)": "GL", "Shoujo ai": "GL",
        "Yaoi(BL)": "BL", "Shounen ai": "BL", "Bara(ML)": "BL",
        "Webtoon": "Webtoon", "Full Color": "Webtoon",
        "Genderswap": "Gender Bender", "Gender Bender": "Gender Bender",
        "School Life": "School Life", "College life": "School Life",
        "Isekai": "isekai", "Reincarnation": "isekai", "Transmigration": "isekai",
        "Emperor's daughte": "European", "Royal Family": "European", "Royalty": "European"
    }
    accepted_languages = []
    genres = []
    types_ = []
    type_ = "Other"

    for i in genres_[0:4]:
        if i in valid_types:
            types_.append(i)
            genres_.remove(i)
        elif i == "Imageset":
            types_.append("Artbook")
            genres_.remove(i)

    for i in genres_:
        if i in valid_genres:
            genres.append(i)
        elif i in genre_map:
            genres.append(genre_map[i])
        elif i in genre_map1:
            if (j := genre_map1[i]) not in genres:
                genres.append(j)

    if len(types_) == 1:
        type_ = types_[0]
        accepted_languages.append(valid_types.get(types_[0]))
    elif original_language in language_map:
        type_ = language_map.get(original_language)[0]
        accepted_languages.append(language_map.get(original_language)[1])
    elif "Doujinshi" in genres:
        type_ = "Manga"
        accepted_languages.append("ja")

    if "" in accepted_languages:
        accepted_languages.remove("")
    return genres, type_, accepted_languages
