from utils.mangadex_integration import dex_fetch_ids
from utils.tasks_2 import db_backup, mu_all, dex_all
from flask_apscheduler import APScheduler

scheduler = APScheduler()


def init_scheduler(app, r=False):
    scheduler.init_app(app)
    scheduler.start()

    def run_task(task_func, task_name, c=True):
        if r:
            task_func() if not c else app.app_context()(task_func)()
        else:
            app.extensions["celery"].send_task(task_name, priority=1 if c else 0)

    @scheduler.task("cron", id="db_backup", day="*", hour=1, minute=0)
    def scheduled_db_backup():
        run_task(db_backup, "backup_database", c=False)

    if app.config.get("MU_AUTOMATION"):
        @scheduler.task("cron", id="mu_automation", day="*", hour=1, minute=30)
        def scheduled_mu_all():
            run_task(mu_all, "mu_all")

    if app.config.get("DEX_FETCH_IDS"):
        @scheduler.task("cron", id="dex_fetch_ids", day="*", hour=2, minute=0)
        def scheduled_dex_fetch_ids():
            run_task(dex_fetch_ids, "dex_fetch_ids")

    if app.config.get("DEX_AUTOMATION"):
        @scheduler.task("cron", id="dex_automation", day="*", hour=2, minute=30)
        def scheduled_dex_all():
            run_task(dex_all, "dex_all")