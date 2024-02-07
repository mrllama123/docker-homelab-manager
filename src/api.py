import logging
import uuid
from contextlib import asynccontextmanager

from apscheduler.jobstores.base import ConflictingIdError, JobLookupError
from fastapi import Depends, FastAPI, HTTPException
from sqlmodel import Session, select

from src.apschedule.schedule import (
    add_backup_job,
    add_restore_job,
    delete_backup_schedule,
    get_backup_schedule,
    list_backup_schedules,
    setup_scheduler,
)
from src.db import get_session
from src.docker import get_volume, get_volumes, is_volume_attached
from src.models import (
    Backups,
    BackupSchedule,
    RestoreVolume,
    CreateBackupResponse,
    CreateBackupSchedule,
    RestoreVolume,
    RestoreVolumeResponse,
    VolumeItem,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    scheduler = setup_scheduler()
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(lifespan=lifespan)


@app.get("/volumes", description="Get a list of all Docker volumes")
async def api_volumes() -> list[VolumeItem]:
    volumes = get_volumes()
    return [
        {
            "name": volume.name,
            "labels": volume.labels or {},
            "mountpoint": str(volume.mountpoint),
            "options": volume.options or {},
            "status": volume.status or {},
            "createdAt": volume.created_at.isoformat(),
        }
        for volume in volumes
    ]


@app.get(
    "/volumes/backup",
    description="Get a list of all backups",
    response_model=list[Backups],
)
async def api_backups(session: Session = Depends(get_session)) -> list[Backups]:
    return session.exec(select(Backups)).all()


@app.get(
    "/volumes/backup/{backup_id}",
    description="Get a backup by name",
    response_model=Backups,
)
async def api_backup(
    backup_id: str, session: Session = Depends(get_session)
) -> Backups:
    backup = session.exec(select(Backups).where(Backups.backup_id == backup_id)).first()
    if not backup:
        raise HTTPException(
            status_code=404,
            detail=f"Backup {backup_id} does not exist",
        )
    return backup


@app.post("/volumes/backup/{volume_name}", description="Backup a Docker volume")
def api_backup_volume(volume_name: str) -> CreateBackupResponse:
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


@app.post(
    "/volumes/restore",
    description="Restore a Docker volume",
)
def api_restore_volume(
    restore_volume: RestoreVolume,
) -> RestoreVolumeResponse:
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


@app.get("/volumes/schedule/backup/{schedule_id}", description="Get a backup schedule")
def api_get_backup_schedule(schedule_id: str) -> BackupSchedule:
    logger.info("Getting schedule %s", schedule_id)
    schedule = get_backup_schedule(schedule_id)
    if not schedule:
        raise HTTPException(
            status_code=404,
            detail=f"Schedule job {schedule_id} does not exist",
        )
    return schedule


@app.get("/volumes/schedule/backup", description="Get a list of backup schedules")
def api_list_backup_schedules() -> list[BackupSchedule]:
    # TODO: add filters e.g volume_name, cron schedule
    return list_backup_schedules()


@app.delete(
    "/volumes/schedule/backup/{schedule_id}", description="Remove a backup schedule"
)
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


@app.post("/volumes/schedule/backup", description="Create a backup schedule")
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
