import os

import src.docker as docker
from celery import Celery
from sqlalchemy_celery_beat.schedulers import DatabaseScheduler


celery = Celery(__name__)
celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379")
celery.conf.result_backend = os.environ.get(
    "CELERY_RESULT_BACKEND",
    "db+sqlite://",
)
celery.conf.beat_dburi = os.environ.get(
    "CELERY_BEAT_DBURI",
    "db+sqlite://",
)

celery.conf.beat_scheduler = DatabaseScheduler
celery.conf.beat_schema = None

beat = celery.Beat(loglevel="debug")


@celery.task(name="create_volume_backup")
def create_volume_backup(volume_name: str):
    docker.backup_volume(volume_name)


@celery.task(name="restore_volume_task")
def restore_volume_task(volume_name: str, filename: str):
    docker.restore_volume(volume_name, filename)


