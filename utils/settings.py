import sqlite3
from pyexpat.errors import messages


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
    langs = ",".join(langs)
    if "en" not in langs:
        langs = "en" + langs
        params.append((langs, "title_languages"))
        app.logger.info("Don't remove English from title languages or you may break something.")
    app.config["TITLE_LANGUAGES"] = langs

    for i in ["mu", "dex", "mal"]:
        if settings[f"{i}_integration"] not in [0, 1]:
            settings[f"{i}_integration"] = 0
            params.append((0, f"{i}_integration"))

    mu_integration = settings["mu_integration"]
    if mu_integration:
        if settings["mu_username"] and settings["mu_password"]:
            app.config["MU_INTEGRATION"] = "yes"
            app.config["MU_USERNAME"] = settings["mu_username"]
            app.config["MU_PASSWORD"] = settings["mu_password"]
            app.config["MU_LAST_TIMESTAMP"] = settings["mu_last_timestamp"]
            for i in ("plan_to_read", "reading", "completed", "one-shots", "dropped", "on_hold", "ongoing"):
                app.config[f"MU_LIST_{i.upper()}"] = settings[f"mu_list_{i}"]
        else:
            app.config["MU_INTEGRATION"] = 0
            params.append((0, "mu_integration"))
            app.logger.warning("You must provide both mu_username and mu_password to use mu_integration")
    else:
        app.config["MU_INTEGRATION"] = 0

    dex_integration = settings["dex_integration"]
    if dex_integration:
        if settings["dex_token"]:
            app.config["DEX_INTEGRATION"] = 1
            app.config["DEX_TOKEN"] = settings.get("dex_token")
        else:
            app.config["DEX_INTEGRATION"] = 0
            params.append((0, "dex_integration"))
            app.logger.warning("You must provide dex_token to use dex_integration")
    else:
        app.config["DEX_INTEGRATION"] = 0

    mal_integration = settings["mal_integration"]
    if mal_integration:
        app.config["MAL_INTEGRATION"] = 0  # TODO: Add mal integration
    else:
        app.config["MAL_INTEGRATION"] = 0

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