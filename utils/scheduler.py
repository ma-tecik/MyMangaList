from flask_apscheduler import APScheduler
from utils.mangaupdates_integration import mu_update_ongoing, mu_get_data_for_all, mu_sync_lists, mu_update_series, \
    mu_update_ratings
from utils.mangadex_integration import dex_start, dex_sync_lists, dex_sync_lists_forced, dex_refresh_token, \
    dex_update_ratings, dex_fetch_ids
scheduler = APScheduler()


def init_scheduler(app):
    scheduler.init_app(app)
    scheduler.start()

    if app.config.get("MU_AUTOMATION"):
        @scheduler.task("cron", id="mu_automation", day="*", hour=1, minute=30)
        def scheduled_check_updates():
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
            app.logger.info("Starting scheduled MangaDex ID fetch...")
            dex_fetch_ids()

    if app.config.get("DEX_AUTOMATION"):
        @scheduler.task("cron", id="dex_automation", day="*", hour=2, minute=30)
        def scheduled_dex_updates():
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
