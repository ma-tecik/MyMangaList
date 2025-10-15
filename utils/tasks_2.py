def db_backup():
    from datetime import datetime
    import sqlite3
    import os

    os.makedirs("data/backups", exist_ok=True)
    dst_name = f"data/backups/mml_{datetime.today().strftime('%Y-%m-%d')}.sqlite3"
    with sqlite3.connect(f"data/mml.sqlite3") as src, sqlite3.connect(dst_name) as dst:
        src.backup(dst)

    backups = sorted(os.listdir("data/backups"))
    for backup in backups[:-10]:
        os.remove(os.path.join("data/backups", backup))


def mu_all():
    from utils.mangaupdates_integration import mu_update_ongoing, mu_get_data_for_all, mu_sync_lists, mu_update_series, \
        mu_update_ratings
    mu_update_ongoing()
    data, headers = mu_get_data_for_all()
    if not data or not headers:
        return
    mu_sync_lists(data, headers)
    mu_update_series(data)
    mu_update_ratings(data)

def dex_all():
    from utils.mangadex_integration import dex_start, dex_sync_lists, dex_sync_lists_forced, dex_refresh_token, \
        dex_update_ratings
    from flask import current_app
    tokens, headers, lists = dex_start()
    if not tokens or not headers or not lists:
        return
    to_update = dex_sync_lists(lists)
    if current_app.config["DEX_INTEGRATION_FORCED"] == "1":
        tokens, headers = dex_sync_lists_forced(tokens, headers, to_update)
    _, headers = dex_refresh_token(tokens)
    if not headers:
        return
    dex_update_ratings(lists, headers)