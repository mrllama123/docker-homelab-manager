import logging
import os
import uuid
from datetime import datetime

import pytz
from sqlmodel import Session

from src.db import engine
from src.docker import backup_volume, restore_volume
from src.models import (
    BackupFilenames,
    Backups,
    BackupVolumes,
    RestoreBackupVolumes,
    RestoredBackups,
    ScheduledBackups,
    ErrorBackups,
    ErrorRestoredBackups,
)

TZ = os.environ.get("TZ", "UTC")
BACKUP_DIR = os.getenv("BACKUP_DIR")

logger = logging.getLogger(__name__)


def task_create_backup(
    volume_name: str,
    job_id: str,
    job_name: str | None = None,
    is_schedule: bool = False,
) -> None:

    with Session(engine) as session:
        # TODO: hack to get this to work as the current apschedule events have no useful info sent to it
        backup_id = str(uuid.uuid4()) if is_schedule else job_id
        try:
            dt_now = datetime.now(tz=pytz.timezone(TZ))
            backup_file = f"{volume_name}-{dt_now.isoformat()}.tar.gz"
            backup_volume(volume_name, BACKUP_DIR)

            backup = Backups(
                backup_id=backup_id,
                backup_filename=backup_file,
                backup_created=dt_now.isoformat(),
                backup_path=os.path.join(BACKUP_DIR, backup_file),
                volume_name=volume_name,
                success=True,
            )

            if is_schedule:
                schedule = ScheduledBackups(
                    schedule_id=job_id,
                    backup_id=backup_id,
                    schedule_name=job_name,
                )
                backup.schedule_id = job_id
                session.add(schedule)

            session.add(BackupVolumes(volume_name=volume_name, backup_id=backup_id))
            session.add(
                BackupFilenames(backup_filename=backup_file, backup_id=backup_id)
            )
            session.add(backup)
            session.commit()
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            session.rollback()
            session.add(
                ErrorBackups(
                    backup_id=backup_id,
                    error_message=str(e),
                )
            )
            session.commit()


def task_restore_backup(volume_name: str, backup_file: str, job_id: str) -> None:
    # TODO: hack to get this to work as the current apschedule events have no useful info sent to it
    with Session(engine) as session:
        try:
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
            session.add(
                RestoreBackupVolumes(volume_name=volume_name, restore_id=job_id)
            )
            session.add(backup)
            session.commit()
        except Exception as e:
            logger.error(f"Error restoring backup: {e}")
            session.rollback()
            session.add(
                ErrorRestoredBackups(
                    restore_id=job_id,
                    error_message=str(e),
                )
            )
            session.commit()
