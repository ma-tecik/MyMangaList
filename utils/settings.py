import sqlite3

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
    params_to_add = []
    params_to_update = []

    if main_rating := settings.get("main_rating"):
        if main_rating in ["mu", "dex", "mal"]:
            app.config["MAIN_RATING"] = main_rating
        else:
            app.config["MAIN_RATING"] = "mu"
            app.logger.warning(f"""{main_rating} is not a valid main_rating, "mu" will be used.""")
    else:
        app.config["MAIN_RATING"] = "mu"
        params_to_add.append(("main_rating", "mu"))

    if _langs := settings["title_languages"]:
        langs = [l for l in _langs.split(",")]
        iso639_1 = iso_langs()
        if all(i in iso639_1 for i in langs):
            if "en" not in langs:
                langs.append("en")
                params_to_update.append(("en," + _langs, "title_languages"))
                app.logger.info("Don't remove English from title languages or you may break something.")
            app.config["TITLE_LANGUAGES"] = langs
        else:
            app.config["TITLE_LANGUAGES"] = ["en"]
            app.logger.warning(f"""{langs} is not a valid language, "en" will be used.""")
    else:
        app.config["TITLE_LANGUAGES"] = ["en"]
        params_to_add.append(("title_languages", "en"))


    if mu_integration := settings.get("mu_integration"):
        if not mu_integration in ["yes", "no"]:
            app.config["MU_INTEGRATION"] = "no"
            params_to_update.append(("no", "mu_integration"))
            app.logger.warning("""mu_integration is not valid, "no" will be used.""")
        if mu_integration == "yes":
            if settings.get("mu_username") and settings.get("mu_password"):
                app.config["MU_INTEGRATION"] = "yes"
                app.config["MU_USERNAME"] = settings.get("mu_username")
                app.config["MU_PASSWORD"] = settings.get("mu_password")
            else:
                app.config["MU_INTEGRATION"] = "no"
                params_to_update.append(("no", "mu_integration"))
                app.logger.warning("You must provide both mu_username and mu_password to use mu_integration")
    else:
        app.config["MU_INTEGRATION"] = "no"
        params_to_add.append(("mu_integration", "no"))

    if dex_integration := settings.get("dex_integration"):
        if not dex_integration in ["yes", "no"]:
            app.config["DEX_INTEGRATION"] = "no"
            params_to_update.append(("no", "dex_integration"))
            app.logger.warning("""dex_integration is not valid, "no" will be used.""")
        if dex_integration == "yes":
            if settings.get("dex_token"):
                app.config["DEX_INTEGRATION"] = "yes"
                app.config["DEX_TOKEN"] = settings.get("dex_token")
            else:
                app.config["DEX_INTEGRATION"] = "no"
                params_to_update.append(("no", "dex_integration"))
                app.logger.warning("You must provide dex_token to use dex_integration")
    else:
        app.config["DEX_INTEGRATION"] = "no"
        params_to_add.append(("dex_integration", "no"))

    if mal_integration := settings.get("mal_integration"):
        if not mal_integration in ["yes", "no"]:
            app.logger.warning("""mal_integration is not valid, "no" will be used.""")
        if mal_integration == "yes":
            app.config["MAL_INTEGRATION"] = "no"  # TODO: Add mal integration
    else:
        app.config["MAL_INTEGRATION"] = "no"
        params_to_add.append(("mal_integration", "no"))

    if params_to_add:
        cursor.executemany("INSERT INTO settings VALUES (?, ?)", params_to_add)
        conn.commit()
    if params_to_update:
        cursor.executemany("UPDATE settings SET value = ? WHERE key = ? ", params_to_update)
        conn.commit()
    conn.close()