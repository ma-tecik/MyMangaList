import sqlite3
from idlelib.configdialog import is_int


def first_run():
    with open("schema.sql") as f:
        schema = f.read()
    with open("first_run.sql") as f:
        set_up = f.read()

    conn = sqlite3.connect("data/mml.sqlite3")
    cursor = conn.cursor()
    cursor.executescript(schema)
    cursor.executescript(set_up)
    conn.commit()
    conn.close()

    conn = sqlite3.connect("data/detect_language.sqlite3")
    cursor = conn.cursor()
    cursor.execute("""
                   CREATE TABLE titles
                   (
                       title      TEXT
                           primary key,
                       lang       TEXT,
                       confidence REAL,
                       timestamp  INTEGER
                   )
                   """)
    conn.commit()
    conn.close()


def iso_langs() -> list:
    iso639_1 = [
        "aa", "ab", "ae", "af", "ak", "am", "an", "ar", "as", "av", "ay", "az",
        "ba", "be", "bg", "bh", "bi", "bm", "bn", "bo", "br", "bs",
        "ca", "ce", "ch", "co", "cr", "cs", "cu", "cv", "cy",
        "da", "de", "dv", "dz",
        "ee", "el", "en", "eo", "es", "et", "eu",
        "fa", "ff", "fi", "fj", "fo", "fr", "fy",
        "ga", "gd", "gl", "gn", "gu", "gv",
        "ha", "he", "hi", "ho", "hr", "ht", "hu", "hy", "hz",
        "ia", "id", "ie", "ig", "ii", "ik", "io", "is", "it", "iu",
        "ja", "jv",
        "ka", "kg", "ki", "kj", "kk", "kl", "km", "kn", "ko", "kr", "ks", "ku", "kv", "kw", "ky",
        "la", "lb", "lg", "li", "ln", "lo", "lt", "lu", "lv",
        "mg", "mh", "mi", "mk", "ml", "mn", "mr", "ms", "mt", "my",
        "na", "nb", "nd", "ne", "ng", "nl", "nn", "no", "nr", "nv", "ny",
        "oc", "oj", "om", "or", "os",
        "pa", "pi", "pl", "ps", "pt",
        "qu",
        "rm", "rn", "ro", "ru", "rw",
        "sa", "sc", "sd", "se", "sg", "si", "sk", "sl", "sm", "sn", "so", "sq", "sr", "ss", "st", "su", "sv", "sw",
        "ta", "te", "tg", "th", "ti", "tk", "tl", "tn", "to", "tr", "ts", "tt", "tw", "ty",
        "ug", "uk", "ur", "uz",
        "ve", "vi", "vo",
        "wa", "wo",
        "xh",
        "yi", "yo",
        "za", "zh", "zu"
    ]
    return iso639_1


def is_mal_id_valid(mal_id: str) -> bool:
    if not mal_id:
        return False
    import requests
    try:
        response = requests.get("https://api.myanimelist.net/v2/forum/boards", headers={"X-MAL-CLIENT-ID": mal_id})
        if response.status_code == 200:
            return True
    except Exception:
        pass
    return False


def get_settings(app):
    conn = sqlite3.connect("data/mml.sqlite3")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM settings")
    settings = {r[0]: r[1] for r in cursor.fetchall()}
    params = []

    main_rating = settings["main_rating"]
    if main_rating in ["mu", "dex", "mal"]:
        app.config["MAIN_RATING"] = main_rating
    else:
        app.config["MAIN_RATING"] = "mu"
        app.logger.warning(f"""{main_rating} is not a valid main_rating, "mu" will be used.""")
        params.append(("mu", "main_rating"))

    langs = settings["title_languages"]
    iso639_1 = iso_langs()
    langs = [l for l in langs.split(",") if l in iso639_1]
    if "en" not in langs:
        langs.append("en")
        params.append((",".join(langs), "title_languages"))
        app.logger.info("Don't remove English from title languages or you may break something.")
    app.config["TITLE_LANGUAGES"] = langs

    # INTEGRATION BASE
    for i in ["mu", "dex", "mal"]:
        j = f"{i}_integration"
        if (k:=settings[j]) not in ["0", "1"]:
            app.config[j.upper()] = 0
            params.append((0, j))
        else:
            k = int(k)
            app.config[j.upper()] = k

    # MU INTEGRATION
    if app.config["MU_INTEGRATION"]:
        l = ("plan_to_read", "reading", "completed", "one-shot", "dropped", "on_hold", "ongoing")
        l = tuple(f"mu_list_{i}" for i in l)
        s = ("mu_username", "mu_password")
        if all(settings.get(i) for i in s) and all(is_int(settings.get(i)) for i in l):
            app.config["MU_INTEGRATION"] = "yes"
            for i in s:
                app.config[i.upper()] = settings[i]
            for i in l:
                app.config[i.upper()] = int(settings[i])
        else:
            app.config["MU_INTEGRATION"] = 0
            params.append((0, "mu_integration"))
            app.logger.warning("You must provide both mu_username and mu_password to use mu_integration")

    # DEX INTEGRATION
    if app.config["DEX_INTEGRATION"]:
        s = ["dex_username", "dex_password", "dex_client_id", "dex_secret", "dex_integration_forced"]
        if all(settings.get(i) for i in s):
            app.config["DEX_INTEGRATION"] = 1
            for i in s:
                app.config[i.upper()] = settings[i]
        else:
            app.config["DEX_INTEGRATION"] = 0
            params.append((0, "dex_integration"))
            app.logger.warning(
                "You must provide dex_username, dex_password, dex_client_id, dex_secret and dex_integration_forced to use dex_integration")

    # MAL INTEGRATION
    # Why "publicly available information" require authentication?
    # https://web.archive.org/web/20250514000339/https://myanimelist.net/forum/?topicid=1973141#:~:text=publicly%20available%20information
    f_mal = settings.get("mal_client_id")
    s = is_mal_id_valid(f_mal) if f_mal else False
    if s:
        app.config["MAL_CLIENT_ID"] = f_mal
    else:
        app.logger.warning("You must provide a MAL Client ID to get any data from MyAnimeList.")
        app.config["MAL_CLIENT_ID"] = None
        if app.config["MAL_INTEGRATION"]:
            app.config["MAL_INTEGRATION"] = 0
            params.append((0, "mal_integration"))
    if app.config["MAL_INTEGRATION"]:
        app.config["MAL_INTEGRATION"] = 0  # TODO: Add mal integration

    # AUTOMATION
    for i in ["mu", "dex", "mal"]:
        j = f"{i}_automation"
        if (k:=settings[j]) not in ["0", "1"]:
            app.config[j.upper()] = 0
            params.append((0, j))
        elif not app.config[f"{i.upper()}_INTEGRATION"]:
            app.config[j.upper()] = 0
        else:
            k = int(k)
            app.config[j.upper()] = k


    if params:
        cursor.executemany("UPDATE settings SET value = ? WHERE key = ? ", params)
        conn.commit()
    conn.close()


def update_settings(data, app):
    conn = sqlite3.connect("data/mml.sqlite3")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM settings")
    in_db = {r[0]: r[1] for r in cursor.fetchall()}
    params = []
    bools = ("mu_integration", "dex_integration", "mal_integration")
    accepted = bools + ("main_rating", "title_languages")
    for k, v in data.items():
        if not k in accepted:
            continue
        if k in bools:
            v = 1 if v == True else 0
        if v == in_db[k]:
            continue
        if k == "main_rating":
            if v not in ["mu", "dex", "mal"]:
                continue
        if k == "title_languages":
            if not isinstance(v, str):
                continue
            langs = [l for l in v.split(",")]
            iso639_1 = iso_langs()
            v_ = [i for i in langs if i in iso639_1]
            v = ",".join(v_)
            if "en" not in v:
                v = "en" + v
                app.logger.info("Don't remove English from title languages or you may break something.")
        params.append((v, k))
        app.config[k] = v

    if params:
        cursor.executemany("UPDATE settings SET value = ? WHERE key = ? ", params)
        conn.commit()
    conn.close()
