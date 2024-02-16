from fastapi import APIRouter, Depends, Request
from sqlmodel import Session
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
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
    api_backup_volume,
    api_backups,
    api_create_backup_schedule,
    api_get_backup,
    api_get_backup_schedule,
    api_list_backup_schedules,
    api_remove_backup_schedule,
    api_restore_volume,
    api_volumes,
)

router = APIRouter(tags=["html"])

templates = Jinja2Templates(directory="src/templates")


@router.get("/", description="home page", response_class=HTMLResponse)
def root(request: Request):
    return templates.TemplateResponse(request, "index.html")
