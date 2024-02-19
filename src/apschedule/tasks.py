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
    RestoredBackups,
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
        dt_now = datetime.now(tz=pytz.timezone(TZ))
        try:
            backup_file = f"{volume_name}-{dt_now.isoformat()}.tar.gz"
            backup_volume(volume_name, BACKUP_DIR, backup_file)

            backup = Backups(
                backup_id=backup_id,
                backup_filename=backup_file,
                backup_name=job_name,
                backup_created=dt_now.isoformat(),
                successful=True,
                backup_path=os.path.join(BACKUP_DIR, backup_file),
                volume_name=volume_name,
            )

            if is_schedule:
                backup.schedule_id = job_id
            session.add(
                BackupFilenames(backup_filename=backup_file, backup_id=backup_id)
            )
            session.add(backup)
            session.commit()
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            session.rollback()
            session.add(
                Backups(
                    backup_id=backup_id,
                    backup_name=job_name,
                    backup_created=dt_now.isoformat(),
                    successful=False,
                    error_message=str(e),
                )
            )
            session.commit()
            raise


def task_restore_backup(
    volume_name: str, backup_file: str, job_id: str, job_name: str | None = None
) -> None:
    # TODO: hack to get this to work as the current apschedule events have no useful info sent to it
    with Session(engine) as session:
        dt_now = datetime.now(tz=pytz.timezone(TZ))
        try:
            logger.info("backup dir: %s", BACKUP_DIR)
            restore_volume(volume_name, BACKUP_DIR, backup_file)

            backup = RestoredBackups(
                restore_id=job_id,
                backup_filename=backup_file,
                restore_name=job_name,
                restored_date=dt_now.isoformat(),
                successful=True,
                restore_path=os.path.join(BACKUP_DIR, backup_file),
                volume_name=volume_name,
            )
            session.add(backup)
            session.commit()
        except Exception as e:
            logger.error(f"Error restoring backup: {e}")
            session.rollback()
            session.add(
                RestoredBackups(
                    restore_id=job_id,
                    restore_name=job_name,
                    successful=False,
                    restored_date=dt_now.isoformat(),
                    error_message=str(e),
                )
            )
            session.commit()
            raise
