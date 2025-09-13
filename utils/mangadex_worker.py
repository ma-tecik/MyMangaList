from typing import List, Tuple


def worker(genres_: List[dict], demographic: str, content_rating: str, original_language: str) -> Tuple[List[str], str, bool, List[str]]:
    language_map_0 = {"ja": "Manga", "ko": "Manhwa", "zh": "Manhua", "zh-hk": "Manhua"}
    accepted_languages_map = {"Manga": ["ja-ro", "ja"], "Manhwa": ["ko"], "Manhua": ["zh", "zh-hk"]}
    language_map_1 = {"en": "OEL", "vi": "Vietnamese", "ms": "Malaysian", "id": "Indonesian"}
    genre_map = {
        "0a39b5a1-b235-4886-a747-1d05d216532d": "Award",
        "256c8bd9-4904-4360-bf4f-508a76d67183": "Sci-fi",
        "292e862b-2d17-4062-90a2-0356caa4ae27": "Time Rewind",
        "2bd2e8d0-f146-434a-9b51-fc9ff2c5fe6a": "Gender Bender",
        "2d1f5d56-a1e5-4d0d-a961-2193588b08ec": "Lolicon",
        "33771934-028e-4cb3-8744-691e866a923e": "Historical",
        "391b0423-d847-456f-aff0-8b0cfc03066b": "Action",
        "3b60b75c-a2d7-4860-ab56-05f391bb889c": "Psychological",
        "3e2b8dae-350e-4ab8-a8ce-016e844b9f0d": "Webtoon",
        "423e2eae-a7a2-4a8b-ac03-a8351462d71d": "Romance",
        "4d32cc48-9f00-4cca-9b5a-a839f0764984": "Comedy",
        "50880a9d-5440-4732-9afb-8f457127e836": "Mecha",
        "51d83883-4103-437c-b4b1-731cb73d786c": "Anthology",
        "5920b825-4181-4a17-beeb-9918b0ff7a30": "BL",
        "5bd0e105-4481-44ca-b6e7-7544da56b1a3": "Incest",
        "65761a2a-415e-47f3-bef2-a9dababba7a6": "Reverse Harem",
        "799c202e-7daa-44eb-9cf7-8a3c0441531e": "Martial Arts",
        "87cc87cd-a395-47af-b27a-93258283bbc6": "Adventure",
        "92d6d951-ca5e-429c-ac78-451071cbf064": "Office",
        "a3c67850-4684-404e-9b7f-c69850ee5da6": "GL",
        "aafb99c1-7f60-43fa-b75f-fc9502ce29c7": "Harem",
        "b11fda93-8f1d-4bef-b2ed-8803d3733170": "4-Koma",
        "b13b2a48-c720-44a9-9c77-39c9979373fb": "Doujinshi",
        "b9af3a63-f058-46de-a9a0-e0c13906197a": "Drama",
        "caaa44eb-cd40-4177-b930-79d3ef2afe87": "School Life",
        "cdad7e68-1419-41dd-bdce-27753074a640": "Horror",
        "cdc58593-87dd-415e-bbc0-2ec27bf404cc": "Fantasy",
        "d14322ac-4d6f-4e9b-afd9-629d5f4d8a41": "Villainess",
        "ddefd648-5140-4e5f-ba18-4eca4071d19b": "Shotacon",
        "e5301a23-ebd9-49dd-a0cb-2add944c7fe9": "Slice of Life",
        "eabc5b4c-6aff-42f3-b657-3e90cbd00b75": "Supernatural",
        "ee968100-4191-4968-93d3-f82d72be7e46": "Mystery",
        "f8f62932-27da-4fe4-8ee1-6779a8c5edba": "Tragedy",
    }
    genre_map_1 = {
        "ace04997-f6bd-436e-b261-779182193d3d": "isekai",
        "0bc90acb-ccc1-44ca-a34a-b9f3a73259d0": "isekai"
    }

    accepted_languages = []
    genres = []
    type_ = "Other"
    os_a = False

    if demographic:
        genres.append(demographic.capitalize())

    if content_rating == "pornographic":
        genres.append("Hentai")

    for i in genres_:
        if (genre_id := i["id"]) == "0234a31e-a729-4e28-9d6a-3f87c4966b9e": # Oneshot
            os_a = True
        elif genre_id in genre_map_1:
            if genre_map_1[genre_id] in genres:
                continue
            genres.append(genre_map_1[genre_id])
        elif genre_id in genre_map:
            genres.append(genre_map[genre_id])

    if original_language in language_map_0:
        type_ = language_map_0[original_language]
        accepted_languages.extend(accepted_languages_map[type_])
    elif original_language in language_map_1:
        type_ = language_map_1[original_language]
        accepted_languages.extend(original_language)
    else:
        accepted_languages.extend(original_language)

    return genres, type_, os_a, accepted_languages
