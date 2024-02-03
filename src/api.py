import logging
import uuid
from contextlib import asynccontextmanager

from apscheduler.jobstores.base import ConflictingIdError, JobLookupError
from fastapi import Depends, FastAPI, HTTPException
from sqlmodel import Session, select

from src.apschedule import (
    add_backup_job,
    add_restore_job,
    delete_backup_schedule,
    get_backup_schedule,
    list_backup_schedules,
    setup_scheduler,
)
from src.db import Backups, engine
from src.docker import get_volume, get_volumes, is_volume_attached
from src.models import BackupSchedule, BackupVolume, BackupVolumeResponse, VolumeItem

logger = logging.getLogger(__name__)


SCHEDULER = None


@asynccontextmanager
async def lifespan(_: FastAPI):
    global SCHEDULER
    SCHEDULER = setup_scheduler()

    yield
    SCHEDULER.shutdown(wait=False)


def get_session():
    with Session(engine) as session:
        yield session


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
    "/backups", description="Get a list of all backups", response_model=list[Backups]
)
async def api_backups(session: Session = Depends(get_session)) -> list[Backups]:
    return session.exec(select(Backups)).all()


@app.get(
    "/backups/{backup_name}", description="Get a backup by name", response_model=Backups
)
async def api_backup(
    backup_name: str, session: Session = Depends(get_session)
) -> Backups:
    backup = session.exec(
        select(Backups).where(Backups.backup_name == backup_name)
    ).first()
    if not backup:
        raise HTTPException(
            status_code=404,
            detail=f"Backup {backup_name} does not exist",
        )
    return backup


@app.post("/backup/{volume_name}", description="Backup a Docker volume")
def api_backup_volume(volume_name: str) -> BackupVolumeResponse:
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

    task = add_backup_job(
        SCHEDULER, f"backup-{volume_name}-{str(uuid.uuid4())}", volume_name
    )
    logger.info(
        "backup %s started task id: %s",
        volume_name,
        task.id,
        extra={"task_id": task.id},
    )

    return {"message": f"Backup of {volume_name} started", "task_id": task.id}


@app.post(
    "/restore",
    description="Restore a Docker volume",
)
def api_restore_volume(
    backup_volume: BackupVolume,
) -> BackupVolumeResponse:
    logger.info(
        "restoring volume: %s from backup: %s",
        backup_volume.volume_name,
        backup_volume.backup_filename,
    )
    task = add_restore_job(
        SCHEDULER,
        f"restore-{backup_volume.volume_name}-{str(uuid.uuid4())}",
        backup_volume.volume_name,
        backup_volume.backup_filename,
    )
    logger.info(
        "restore of %s started task id: %s",
        backup_volume.volume_name,
        task.id,
        extra={"task_id": task.id},
    )
    return {
        "message": f"restore of {backup_volume.volume_name} started",
        "task_id": task.id,
    }


@app.get(
    "/volumes/backup/schedule/{schedule_name}", description="Get a backup schedule"
)
def api_get_backup_schedule(schedule_name: str) -> BackupSchedule:
    logger.info("Getting schedule %s", schedule_name)
    schedule = get_backup_schedule(SCHEDULER, schedule_name)
    if not schedule:
        raise HTTPException(
            status_code=404,
            detail=f"Schedule job {schedule_name} does not exist",
        )
    return schedule


@app.get("/volumes/backup/schedule", description="Get a list of backup schedules")
def api_list_backup_schedules() -> list[BackupSchedule]:
    # TODO: add filters e.g volume_name, cron schedule
    return list_backup_schedules(SCHEDULER)


@app.delete(
    "/volumes/backup/schedule/{schedule_name}", description="Remove a backup schedule"
)
def api_remove_backup_schedule(schedule_name: str) -> str:
    logger.info("Removing schedule %s", schedule_name)
    try:
        delete_backup_schedule(SCHEDULER, schedule_name)
    except JobLookupError as e:
        raise HTTPException(
            status_code=404,
            detail=f"Schedule job {schedule_name} does not exist",
        ) from e
    except Exception:
        raise
    return f"Schedule {schedule_name} removed"


@app.post("/volumes/backup/schedule", description="Create a backup schedule")
async def api_create_backup_schedule(
    schedule_body: BackupSchedule,
) -> BackupSchedule:
    if not get_volume(schedule_body.volume_name):
        raise HTTPException(
            status_code=404,
            detail=f"Volume {schedule_body.volume_name} does not exist",
        )

    try:
        job = add_backup_job(
            SCHEDULER,
            schedule_body.schedule_name,
            schedule_body.volume_name,
            schedule_body.crontab,
        )

    except ConflictingIdError as e:
        raise HTTPException(
            status_code=409,
            detail=f"Schedule job {schedule_body.schedule_name} already exists",
        ) from e
    except Exception:
        raise

    return BackupSchedule(
        schedule_name=job.id,
        volume_name=schedule_body.volume_name,
        crontab=schedule_body.crontab,
    )
