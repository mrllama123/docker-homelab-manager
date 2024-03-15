import logging
import uuid

from apscheduler.jobstores.base import ConflictingIdError, JobLookupError
from fastapi import HTTPException
from sqlmodel import Session, select

from src.apschedule.schedule import (
    add_backup_job,
    add_restore_job,
    delete_backup_schedule,
    get_backup_schedule,
)
from src.docker import get_volume, get_volumes, is_volume_attached
from src.models import (
    Backups,
    BackupSchedule,
    CreateBackupResponse,
    CreateBackupSchedule,
    RestoreVolume,
    RestoreVolumeResponse,
    VolumeItem,
)

logger = logging.getLogger(__name__)





def api_remove_backup_schedule(schedule_id: str) -> str:
    logger.info("Removing schedule %s", schedule_id)
    try:
        delete_backup_schedule(schedule_id)
    except JobLookupError as e:
        raise HTTPException(
            status_code=404,
            detail=f"Schedule job {schedule_id} does not exist",
        ) from e
    except Exception:
        raise
    return f"Schedule {schedule_id} removed"


def api_remove_backup_schedules(schedule_ids: str) -> str:

    for id in schedule_ids:
        logger.info("Removing schedule %s", id)
        delete_backup_schedule(id)

    return f"Schedules {schedule_ids} removed"


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
