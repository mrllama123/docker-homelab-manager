from fastapi import APIRouter, Depends
from sqlmodel import Session


from src.db import get_session
from src.models import (
    Backups,
    BackupSchedule,
    CreateBackupResponse,
    CreateBackupSchedule,
    RestoreVolume,
    RestoreVolumeResponse,
    VolumeItem,
)
from src.routes.impl.volumes import (
    api_backups,
    api_create_backup_schedule,
    api_get_backup,
    api_backup_volume,
    api_get_backup_schedule,
    api_list_backup_schedules,
    api_remove_backup_schedule,
    api_restore_volume,
    api_volumes,
)

router = APIRouter(prefix="/api", tags=["api"])


@router.get("/volumes", description="Get a list of all Docker volumes")
async def get_volumes() -> list[VolumeItem]:
    return await api_volumes()


@router.get(
    "/volumes/backup",
    description="Get a list of all backups",
    response_model=list[Backups],
)
async def list_backups(session: Session = Depends(get_session)) -> list[Backups]:
    return await api_backups(session)


@router.get(
    "/volumes/backup/{backup_id}",
    description="Get a backup by name",
    response_model=Backups,
)
async def get_backup(
    backup_id: str, session: Session = Depends(get_session)
) -> Backups:
    return await api_get_backup(backup_id, session)


@router.post(
    "/volumes/backup/{backup_id}",
    description="Backup a volume",
)
def backup_volume(
    backup_id: str
) -> CreateBackupResponse:
    return api_backup_volume(backup_id)


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
