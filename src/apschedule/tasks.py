from datetime import datetime, timezone

from sqlmodel import Session
from src.docker import backup_volume
from src.db import engine
from src.models import Backups
import pytz
import os

TZ = os.environ.get("TZ", "UTC")
BACKUP_DIR = os.getenv("BACKUP_DIR")


def task_create_backup(volume_name: str, job_id: str) -> None:
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
