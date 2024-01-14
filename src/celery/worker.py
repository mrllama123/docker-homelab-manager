import os

import src.docker as docker
from celery import Celery

celery = Celery(__name__)
celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379")
celery.conf.result_backend = os.environ.get(
    "CELERY_RESULT_BACKEND",
    "redis://localhost:6379",
)


@celery.task(name="create_volume_backup")
def create_volume_backup(volume_name: str):
    docker.backup_volume(volume_name)


@celery.task(name="restore_volume_task")
def restore_volume_task(volume_name: str, filename: str):
    docker.restore_volume(volume_name, filename)
