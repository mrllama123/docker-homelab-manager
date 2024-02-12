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
    CreateBackupResponse,
    CreateBackupSchedule,
    RestoreVolume,
    RestoreVolumeResponse,
    VolumeItem,
)

from src.routes import api
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    scheduler = setup_scheduler()
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(lifespan=lifespan)
app.include_router(api.router)