import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from src.apschedule.schedule import add_backup_job
from src.db import get_session
from src.docker import get_volume, is_volume_attached
from src.models import (
    Backups,
    BackupSchedule,
    CreateBackupResponse,
    CreateBackupSchedule,
    RestoreVolume,
    RestoreVolumeResponse,
    VolumeItem,
)
from src.routes.impl.funcs import (
    api_create_backup_schedule,
    api_get_backup_schedule,
    api_list_backup_schedules,
    api_remove_backup_schedule,
    api_restore_volume,
    api_volumes,
)
from src.routes.impl.volumes.backups import db_get_backup, db_list_backups

router = APIRouter(prefix="/api", tags=["api"])


logger = logging.getLogger(__name__)


@router.get("/volumes", description="Get a list of all Docker volumes")
async def get_volumes() -> list[VolumeItem]:
    return await api_volumes()


@router.get(
    "/volumes/backup",
    description="Get a list of all backups",
    response_model=list[Backups],
)
def list_backups(
    session: Session = Depends(get_session),
    backup_ids: list[str] | None = None,
    successful: bool | None = None,
) -> list[Backups]:
    return db_list_backups(session, backup_ids, successful)


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
    return api_restore_volume(restore_volume)


@router.get(
    "/volumes/schedule/backup/{schedule_id}", description="Get a backup schedule"
)
async def get_backup_schedule(schedule_id: str) -> BackupSchedule:
    return api_get_backup_schedule(schedule_id)


@router.get("/volumes/schedule/backup", description="Get a list of backup schedules")
async def list_backup_schedules() -> list[BackupSchedule]:
    return api_list_backup_schedules()


@router.delete(
    "/volumes/schedule/backup/{schedule_id}", description="Remove a backup schedule"
)
def remove_backup_schedule(schedule_id: str) -> str:
    return api_remove_backup_schedule(schedule_id)


@router.post("/volumes/schedule/backup", description="Create a backup schedule")
async def create_backup_schedule(schedule: CreateBackupSchedule) -> BackupSchedule:
    return await api_create_backup_schedule(schedule)
