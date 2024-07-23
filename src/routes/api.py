import logging
import uuid

from apscheduler.jobstores.base import ConflictingIdError, JobLookupError
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlmodel import Session

from src.apschedule.schedule import (
    add_backup_job,
    add_restore_job,
    delete_backup_schedule,
    get_backup_schedule,
    list_backup_schedules,
)
from src.db import get_session
from src.docker import get_volume, is_volume_attached
from src.models import (
    Backups,
    BackupSchedule,
    CreateBackupResponse,
    CreateBackupSchedule,
    ListBackupsResponse,
    RestoredBackups,
    RestoreVolume,
    RestoreVolumeResponse,
    VolumeItem,
)
from src.routes.impl.volumes.backups import (
    db_get_backup,
    db_list_backups,
    db_get_backup_table_count,
)
from src.routes.impl.volumes.resored_backups import db_list_restored_backups
from src.routes.impl.volumes.volumes import list_volumes

router = APIRouter(prefix="/api", tags=["api"])


logger = logging.getLogger(__name__)


@router.get("/volumes", description="Get a list of all Docker volumes")
def get_volumes() -> list[VolumeItem]:
    return list_volumes()


@router.get(
    "/volumes/backup",
    description="Get a list of all backups",
)
def list_backups(
    request: Request,
    response: Response,
    successful: bool | None = None,
    session: Session = Depends(get_session),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=100, le=100),
) -> ListBackupsResponse:
    offset = (page - 1) * size
    total_items = db_get_backup_table_count(session)
    total_pages = round((total_items + (size - 1)) / size)
    items = db_list_backups(session, offset, size, successful=successful)
    next_page = page + 1 if page < total_pages else None
    if next_page:
        next_page_header = f'<{request.url}?page={next_page}&size={size}>; rel="next"'
        last_page_header = f'<{request.url}?page={total_pages}&size={size}>; rel="last"'
        prev_page_header = (
            f'<{request.url}?page={page - 1}&size={size}>; rel="prev"'
            if page > 1
            else None
        )
        # TODO: make this better as feels gross to do it this way but need to go to bed :(
        if prev_page_header:
            response.headers["link"] = (
                f"{next_page_header}, {prev_page_header}, {last_page_header}"
            )
        else:
            response.headers["link"] = f"{next_page_header}, {last_page_header}"

    else:
        response.headers["link"] = (
            f'<{request.url}?page=1&size={size}>; rel="first", <{request.url}?page={total_pages}&size={size}>; rel="last"'
        )

    return ListBackupsResponse(
        backups=items,
        total_items=total_items,
        total_pages=total_pages,
        page=page,
        size=size,
    )


@router.get(
    "/volumes/backup/{backup_id}",
    description="Get a backup by name",
    response_model=Backups,
)
def get_backup(backup_id: str, session: Session = Depends(get_session)) -> Backups:
    backup = db_get_backup(session, backup_id)
    if not backup:
        raise HTTPException(
            status_code=404,
            detail=f"Backup {backup_id} does not exist",
        )
    return backup


@router.post(
    "/volumes/backup/{volume_name}",
    description="Backup a volume",
)
def backup_volume(volume_name: str) -> CreateBackupResponse:
    logger.info("backing up volume: %s", volume_name)
    if not get_volume(volume_name):
        raise HTTPException(
            status_code=404,
            detail=f"Volume {volume_name} does not exist",
        )
    if not is_volume_attached(volume_name):
        raise HTTPException(
            status_code=409,
            detail=f"Volume {volume_name} is attached to a container",
        )

    job = add_backup_job(f"backup-{volume_name}-{str(uuid.uuid4())}", volume_name)
    logger.info(
        "backup %s started task id: %s",
        volume_name,
        job.id,
        extra={"task_id": job.id},
    )

    return CreateBackupResponse(
        backup_id=job.id,
        volume_name=volume_name,
    )


@router.post(
    "/volumes/restore",
    description="Restore a Docker volume",
)
def restore_volume(restore_volume: RestoreVolume) -> RestoreVolumeResponse:
    logger.info(
        "restoring volume: %s from backup: %s",
        restore_volume.volume_name,
        restore_volume.backup_filename,
    )
    task = add_restore_job(
        f"restore-{restore_volume.volume_name}-{str(uuid.uuid4())}",
        restore_volume.volume_name,
        restore_volume.backup_filename,
    )
    logger.info(
        "restore of %s started task id: %s",
        restore_volume.volume_name,
        task.id,
        extra={"task_id": task.id},
    )
    return RestoreVolumeResponse(
        restore_id=task.id, volume_name=restore_volume.volume_name
    )


@router.get(
    "/volumes/restores",
    description="Get a list of all volumes that have been restored from a backup",
)
def api_list_restores(
    created_at: str | None = None,
    restore_successful: bool | None = None,
    backup_filename: str | None = None,
    session: Session = Depends(get_session),
) -> list[RestoredBackups]:
    params = {}
    if created_at:
        params["created_at"] = created_at
    if restore_successful is not None:
        params["successful"] = restore_successful
    if backup_filename:
        params["backup_filename"] = backup_filename
    return db_list_restored_backups(session, **params)


@router.get(
    "/volumes/schedule/backup/{schedule_id}", description="Get a backup schedule"
)
async def get_schedule(schedule_id: str) -> BackupSchedule:
    logger.info("Getting schedule %s", schedule_id)
    schedule = get_backup_schedule(schedule_id)
    if not schedule:
        raise HTTPException(
            status_code=404,
            detail=f"Schedule job {schedule_id} does not exist",
        )
    return schedule


@router.get("/volumes/schedule/backup", description="Get a list of backup schedules")
def api_list_backup_schedules() -> list[BackupSchedule]:
    return list_backup_schedules()


@router.delete(
    "/volumes/schedule/backup/{schedule_id}", description="Remove a backup schedule"
)
def remove_backup_schedule(schedule_id: str) -> str:
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


@router.post("/volumes/schedule/backup", description="Create a backup schedule")
async def create_backup_schedule(schedule: CreateBackupSchedule) -> BackupSchedule:
    if not get_volume(schedule.volume_name):
        raise HTTPException(
            status_code=404,
            detail=f"Volume {schedule.volume_name} does not exist",
        )

    try:
        job = add_backup_job(
            schedule.schedule_name,
            schedule.volume_name,
            schedule.crontab,
            is_schedule=True,
        )

    except ConflictingIdError as e:
        raise HTTPException(
            status_code=409,
            detail=f"Schedule job {schedule.schedule_name} already exists",
        ) from e
    except Exception:
        raise

    return BackupSchedule(
        schedule_id=job.id,
        schedule_name=schedule.schedule_name,
        volume_name=schedule.volume_name,
        crontab=schedule.crontab,
    )
