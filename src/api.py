from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from sqlmodel import Session, select

from src.celery import create_volume_backup, restore_volume_task
from src.db import Backups, create_db_and_tables, engine
from src.docker import get_volume, get_volumes, is_volume_attached
from src.apschedule import (
    setup_scheduler,
    add_backup_interval_job,
    add_backup_crontab_job,
    add_backup_job,
)
from src.models import (
    BackupStatusResponse,
    BackupVolume,
    BackupVolumeResponse,
    VolumeItem,
    CreateBackupSchedule,
    BackupScheduleJob,
)
import logging
from apscheduler.jobstores.base import ConflictingIdError
import uuid

logging.basicConfig()
logger = logging.getLogger(__name__)


schedule = None


@asynccontextmanager
async def lifespan(_: FastAPI):
    global schedule
    create_db_and_tables()
    schedule = setup_scheduler()
    yield
    schedule.shutdown(wait=False)


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
        schedule, f"backup-{volume_name}-{str(uuid.uuid4())}", volume_name
    )  

    return {"message": f"Backup of {volume_name} started", "task_id": task.id}


@app.post(
    "/restore",
    description="Restore a Docker volume",
)
def api_restore_volume(
    backup_volume: BackupVolume,
) -> BackupVolumeResponse:
    # TODO: change to use apschedule
    task = restore_volume_task.delay(
        backup_volume.volume_name, backup_volume.backup_filename
    )
    return {
        "message": f"restore of {backup_volume.volume_name} started",
        "task_id": task.id,
    }


@app.get("/backup/status/{task_id}", description="Get the status of a backup task")
def api_backup_status(task_id: str) -> BackupStatusResponse:
    task = create_volume_backup.AsyncResult(task_id)
    return {"status": task.status, "result": task.result, "task_id": task.id}


@app.post("/volumes/backup/schedule", description="Create a backup schedule")
async def api_create_backup_schedule(
    schedule_body: CreateBackupSchedule,
) -> BackupScheduleJob:
    if not get_volume(schedule_body.volume_name):
        raise HTTPException(
            status_code=404,
            detail=f"Volume {schedule_body.volume_name} does not exist",
        )

    try:
        job = add_backup_job(
            schedule,
            schedule_body.schedule_name,
            schedule_body.volume_name,
            schedule_body.crontab,
            schedule_body.periodic,
        )

    except ConflictingIdError as e:
        raise HTTPException(
            status_code=409,
            detail=f"Schedule job {schedule_body.schedule_name} already exists",
        ) from e
    except Exception:
        raise

    return BackupScheduleJob(
        job_id=job.id,
        volume_name=schedule_body.volume_name,
        crontab=schedule_body.crontab,
        periodic=schedule_body.periodic,
    )
