import os

if not os.getenv("REDIS_URL"):
    import sys
    sys.exit("Redis URL not set")

from flask import Flask
from utils.init_celery import celery_init_app
from flask.logging import default_handler
from utils.settings import get_settings
import logging

app = Flask(__name__)
app.config["WORKER"] = True
app.logger.setLevel(logging.INFO)
default_handler.setLevel(logging.INFO)
default_handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s in %(module)s.%(funcName)s: %(message)s",
                                               datefmt="%Y-%m-%d %H:%M:%S"))
log_dir = "data/logs"
os.makedirs(log_dir, exist_ok=True)
file_handler = logging.FileHandler(os.path.join(log_dir, "worker.log"))
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s in %(module)s.%(funcName)s: %(message)s",
                                            datefmt="%Y-%m-%d %H:%M:%S"))
app.logger.addHandler(file_handler)

get_settings(app)

celery_app = celery_init_app(app)
