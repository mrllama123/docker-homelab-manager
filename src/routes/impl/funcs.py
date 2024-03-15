import logging

from apscheduler.jobstores.base import ConflictingIdError
from fastapi import HTTPException

from src.apschedule.schedule import add_backup_job
from src.docker import get_volume
from src.models import BackupSchedule, CreateBackupSchedule

logger = logging.getLogger(__name__)


async def api_create_backup_schedule(
    schedule_body: CreateBackupSchedule,
) -> BackupSchedule:
    if not get_volume(schedule_body.volume_name):
        raise HTTPException(
            status_code=404,
            detail=f"Volume {schedule_body.volume_name} does not exist",
        )

    try:
        job = add_backup_job(
            schedule_body.schedule_name,
            schedule_body.volume_name,
            schedule_body.crontab,
            is_schedule=True,
        )

    except ConflictingIdError as e:
        raise HTTPException(
            status_code=409,
            detail=f"Schedule job {schedule_body.schedule_name} already exists",
        ) from e
    except Exception:
        raise

    return BackupSchedule(
        schedule_id=job.id,
        schedule_name=schedule_body.schedule_name,
        volume_name=schedule_body.volume_name,
        crontab=schedule_body.crontab,
    )
