from flask_apscheduler import APScheduler
from utils.mangaupdates_integration import mu_update_ongoing, mu_get_data_for_all, mu_sync_lists, mu_update_series, \
    mu_update_ratings
from utils.mangadex_integration import dex_start, dex_sync_lists, dex_sync_lists_forced, dex_refresh_token, \
    dex_update_ratings, dex_fetch_ids

scheduler = APScheduler()


def init_scheduler(app):
    scheduler.init_app(app)
    scheduler.start()

    @scheduler.task("cron", id="db_backup", day="*", hour=1, minute=0)
    def scheduled_db_backup():
        from datetime import datetime
        import sqlite3
        import os

        os.makedirs("data/backups", exist_ok=True)
        backup_path = f"data/backups/mml_{datetime.today().strftime("%Y-%m-%d")}sqlite3"
        try:
            src = sqlite3.connect("data/mml.sqlite3")
            dst = sqlite3.connect(backup_path)
            src.backup(dst)
            dst.close()
            src.close()
        except Exception as e:
            with app.context():
                app.logger.error(e)

    if app.config.get("MU_AUTOMATION"):
        @scheduler.task("cron", id="mu_automation", day="*", hour=1, minute=30)
        def scheduled_check_updates():
            with app.context():
                mu_update_ongoing()
                data, headers = mu_get_data_for_all()
                if not data or not headers:
                    return
                mu_sync_lists(data, headers)
                mu_update_series(data)
                mu_update_ratings(data)

    if app.config.get("DEX_FETCH_IDS"):
        @scheduler.task("cron", id="dex_fetch_ids", day="*", hour=2, minute=0)
        def scheduled_dex_fetch_ids():
            with app.context():
                dex_fetch_ids()

    if app.config.get("DEX_AUTOMATION"):
        @scheduler.task("cron", id="dex_automation", day="*", hour=2, minute=30)
        def scheduled_dex_updates():
            with app.context():
                tokens, headers, lists = dex_start()
                if not tokens or not headers or not lists:
                    return
                to_update = dex_sync_lists(lists)
                if app.config["DEX_INTEGRATION_FORCED"] == "1":
                    tokens, headers = dex_sync_lists_forced(tokens, headers, to_update)
                _, headers = dex_refresh_token(tokens)
                if not headers:
                    return
                dex_update_ratings(lists, headers)