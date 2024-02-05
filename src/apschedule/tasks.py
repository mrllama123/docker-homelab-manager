from datetime import datetime

from sqlmodel import Session
from src.docker import backup_volume, restore_volume
from src.db import engine
from src.models import (
    Backups,
    RestoredBackups,
    ScheduledBackups,
    BackupVolumes,
    BackupFilenames,
    RestoreBackupVolumes,
)
import pytz
import os
import uuid
import logging

TZ = os.environ.get("TZ", "UTC")
BACKUP_DIR = os.getenv("BACKUP_DIR")

logger = logging.getLogger(__name__)


def task_create_backup(
    volume_name: str, job_id: str, is_schedule: bool = False
) -> None:
    with Session(engine) as session:
        dt_now = datetime.now(tz=pytz.timezone(TZ))
        backup_file = f"{volume_name}-{dt_now.isoformat()}.tar.gz"
        backup_volume(volume_name, BACKUP_DIR)

        backup_id = str(uuid.uuid4()) if is_schedule else job_id

        backup = Backups(
            backup_id=backup_id,
            backup_filename=backup_file,
            backup_created=dt_now.isoformat(),
            backup_path=os.path.join(BACKUP_DIR, backup_file),
            volume_name=volume_name,
            success=True,
        )
        session.add(BackupVolumes(volume_name=volume_name, backup_id=backup_id))
        session.add(BackupFilenames(backup_filename=backup_file, backup_id=backup_id))

        session.add(backup)
        if is_schedule:
            schedule = ScheduledBackups(
                schedule_id=job_id,
                backup_id=backup_id,
            )
            session.add(schedule)
        session.commit()


def task_restore_backup(volume_name: str, backup_file: str, job_id: str) -> None:
    with Session(engine) as session:
        dt_now = datetime.now(tz=pytz.timezone(TZ))
        restore_volume(volume_name, BACKUP_DIR, backup_file)

        backup = RestoredBackups(
            restore_id=job_id,
            backup_filename=backup_file,
            restored_date=dt_now.isoformat(),
            restore_path=os.path.join(BACKUP_DIR, backup_file),
            volume_name=volume_name,
            success=True,
        )
        session.add(RestoreBackupVolumes(volume_name=volume_name, restore_id=job_id))
        session.add(backup)
        session.commit()
