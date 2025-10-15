from celery import shared_task
from flask import current_app
from time import sleep
from utils.mangaupdates_integration import mu_get_data_for_all, mu_update_ratings, mu_update_ongoing, mu_sync_lists, \
    mu_update_series
from utils.mangadex_integration import dex_start, dex_update_ratings, dex_sync_lists, dex_sync_lists_forced, \
    dex_fetch_ids
from utils.tasks_2 import db_backup, mu_all, dex_all


@shared_task(name="reload_settings", ignore_result=True)
def reload_settings():
    from utils.settings import get_settings
    app = current_app
    get_settings(app)


@shared_task(name="backup_database", ignore_result=True)
def db_backup_task():
    db_backup()


@shared_task(name="mu_update_ratings")
def mu_update_ratings_task():
    data, _ = mu_get_data_for_all()
    if not data:
        raise Exception("No data returned")
    s = mu_update_ratings(data)
    if not s:
        raise Exception("Failed to update ratings")


@shared_task(name="mu_all")
def mu_all_task():
    mu_all()


@shared_task(name="mu_update_ongoing")
def mu_update_ongoing_task():
    s = mu_update_ongoing()
    if not s:
        raise Exception("Failed to update ongoing series")
    if s == 2:
        sleep(10)
        mu_sync_lists_task()


@shared_task(name="mu_sync_lists")
def mu_sync_lists_task():
    data, headers = mu_get_data_for_all()
    if not data:
        raise Exception("No data returned")
    s = mu_sync_lists(data, headers)
    if not s:
        raise Exception("Failed to sync lists")


@shared_task(name="mu_update_series")
def mu_update_series_task():
    data, _ = mu_get_data_for_all()
    if not data:
        raise Exception("No data returned")
    s = mu_update_series(data)
    if not s:
        raise Exception("Failed to update series")


@shared_task(name="dex_all")
def dex_all_task():
    dex_all()


@shared_task(name="dex_update_ratings")
def dex_update_ratings_task():
    tokens, headers, lists = dex_start()
    if not headers:
        raise Exception("Failed to authenticate with Mangadex")
    s = dex_update_ratings(lists, headers)
    if not s:
        raise Exception("Failed to update ratings")


@shared_task(name="dex_sync_lists")
def dex_sync_lists_task():
    tokens, headers, lists = dex_start()
    if not headers:
        raise Exception("Failed to authenticate with Mangadex")
    to_update = dex_sync_lists(lists)
    if to_update and current_app.config["DEX_INTEGRATION_FORCED"]:
        dex_sync_lists_forced(tokens, headers, to_update)


@shared_task(name="dex_fetch_ids")
def dex_fetch_ids_task():
    if not dex_fetch_ids():
        raise Exception("Failed to fetch IDs")

