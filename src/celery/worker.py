import os

from celery import Celery

from src.docker import backup_volume

celery = Celery(__name__)
celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379")
celery.conf.result_backend = os.environ.get(
    "CELERY_RESULT_BACKEND",
    "redis://localhost:6379",
)


@celery.task(name="create_volume_backup")
def create_volume_backup(volume_name: str, backup_folder: str):
    backup_volume(volume_name, backup_folder)
