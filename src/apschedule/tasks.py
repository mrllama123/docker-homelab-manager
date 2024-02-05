from datetime import datetime

from sqlmodel import Session
from src.docker import backup_volume, restore_volume
from src.db import engine
from src.models import Backups, RestoredBackups, ScheduleBackups
import pytz
import os

TZ = os.environ.get("TZ", "UTC")
BACKUP_DIR = os.getenv("BACKUP_DIR")


def task_create_backup(volume_name: str, job_id: str, is_schedule=False) -> None:
    with Session(engine) as session:
        dt_now = datetime.now(tz=pytz.timezone(TZ))
        backup_file = f"{volume_name}-{dt_now.isoformat()}.tar.gz"
        backup_volume(volume_name, BACKUP_DIR)

        backup = Backups(
            backup_id=job_id,
            backup_file_name=backup_file,
            backup_created=dt_now.isoformat(),
            backup_path=os.path.join(BACKUP_DIR, backup_file),
            volume_name=volume_name,
            success=True,
        )

        session.add(backup)
        session.commit()


def task_restore_backup(volume_name: str, backup_file: str, job_id: str) -> None:
    with Session(engine) as session:
        dt_now = datetime.now(tz=pytz.timezone(TZ))
        restore_volume(volume_name, BACKUP_DIR, backup_file)

        backup = RestoredBackups(
            restore_id=job_id,
            backup_file_name=backup_file,
            restore_created=dt_now.isoformat(),
            restore_path=os.path.join(BACKUP_DIR, backup_file),
            volume_name=volume_name,
            success=True,
        )
        session.add(backup)
        session.commit()
