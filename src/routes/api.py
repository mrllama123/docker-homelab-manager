import logging
import uuid

from apscheduler.jobstores.base import ConflictingIdError, JobLookupError
from fastapi import APIRouter, Depends, HTTPException
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
    BackUpStatus,
    CreateBackupResponse,
    CreateBackupSchedule,
    RestoredBackups,
    RestoreVolume,
    RestoreVolumeResponse,
    SftpBackupSourceCreate,
    SftpBackupSourcePublic,
    VolumeItem,
)
from src.routes.impl.volumes.backups import db_get_backup, db_list_backups
from src.routes.impl.volumes.db import (
    db_create_sftp_backup_source,
    db_delete_sftp_backup_source,
    db_get_sftp_backup_source,
    db_list_sftp_backup_sources,
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
    response_model=list[Backups],
)
def list_backups(
    session: Session = Depends(get_session),
    backup_ids: list[str] | None = None,
    status: BackUpStatus | None = None,
) -> list[Backups]:
    return db_list_backups(session, backup_ids, status)


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

    job = add_backup_job(f"backup-{volume_name}-{uuid.uuid4()!s}", volume_name)
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
        f"restore-{restore_volume.volume_name}-{uuid.uuid4()!s}",
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
        restore_id=task.id,
        volume_name=restore_volume.volume_name,
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
    "/volumes/schedule/backup/{schedule_id}",
    description="Get a backup schedule",
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
    "/volumes/schedule/backup/{schedule_id}",
    description="Remove a backup schedule",
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


@router.post("/volumes/backups/source", description="Create a backup source")
def create_sftp_backup_source(
    backup_source: SftpBackupSourceCreate,
    session: Session = Depends(get_session),
) -> SftpBackupSourcePublic:
    return db_create_sftp_backup_source(session, backup_source)


@router.get("/volumes/backups/sources", description="List backup sources")
def list_backup_sources(
    session: Session = Depends(get_session),
) -> list[SftpBackupSourcePublic]:
    return db_list_sftp_backup_sources(session)


@router.get("/volumes/backups/source/{source_id}", description="Get a backup source")
def get_backup_source(
    source_id: str,
    session: Session = Depends(get_session),
) -> SftpBackupSourcePublic:
    result = db_get_sftp_backup_source(session, source_id)
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Backup source {source_id} does not exist",
        )
    return result


@router.delete(
    "/volumes/backups/source/{source_id}",
    description="Delete a backup source",
)
def delete_backup_source(
    source_id: str,
    session: Session = Depends(get_session),
) -> str:
    if not db_get_sftp_backup_source(session, source_id):
        raise HTTPException(
            status_code=404,
            detail=f"Backup source {source_id} does not exist",
        )
    db_delete_sftp_backup_source(session, source_id)
    return f"Backup source {source_id} deleted"
