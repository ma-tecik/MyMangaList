from celery import Celery, Task
import os

def celery_init_app(app) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    redis_url = os.environ["REDIS_URL"]
    celery_app = Celery(app.name, task_cls=FlaskTask, include=["utils.tasks"],
                        broker_url=redis_url, result_backend=redis_url)
    celery_app.set_default()
    return celery_app