import logging
import os
import uuid
from datetime import datetime
from pathlib import Path

import pytz
from sqlmodel import Session

from src.db import engine
from src.docker import backup_volume, restore_volume
from src.models import BackupFilenames, BackUpStatus, RestoredBackups
from src.routes.impl.volumes.db import db_create_backup

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
            backup = db_create_backup(session, volume_name, job_name)
            backup_file = f"{volume_name}-{backup.created_at}.tar.gz"
            backup_volume(volume_name, BACKUP_DIR, backup_file)

            session.add(
                BackupFilenames(backup_filename=backup_file, backup_id=backup_id),
            )
            session.add(backup)
            session.commit()
        except Exception as e:
            session.rollback()
            db_create_backup(
                backup_id,
                job_name,
                status=BackUpStatus.Errored,
                error_message=str(e),
            )
            raise


def task_restore_backup(
    volume_name: str,
    backup_file: str,
    job_id: str,
    job_name: str | None = None,
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
                created_at=dt_now.isoformat(),
                successful=True,
                backup_path=str(Path(BACKUP_DIR) / backup_file),
                volume_name=volume_name,
            )
            session.add(backup)
            session.commit()
        except Exception as e:
            session.rollback()
            session.add(
                RestoredBackups(
                    restore_id=job_id,
                    restore_name=job_name,
                    successful=False,
                    created_at=dt_now.isoformat(),
                    error_message=str(e),
                ),
            )
            session.commit()
            raise
