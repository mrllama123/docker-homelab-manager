from fastapi import APIRouter, Depends, Request
from sqlmodel import Session
from fastapi.responses import HTMLResponse, RedirectResponse
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


@router.get("/volumes", description="volumes page", response_class=HTMLResponse)
async def volumes(request: Request):
    volumes = await api_volumes()
    return templates.TemplateResponse(request, "volume_rows.html", {"volumes": volumes})


@router.get(
    "/backup-volume-tab", description="backup volumes tab", response_class=HTMLResponse
)
def backup_volume_tab(request: Request):
    return templates.TemplateResponse(request, "backup_volume_tab.html")


@router.post(
    "/volumes/backup/{volume_name}",
    description="create backup",
    response_class=RedirectResponse,
)
def backup_volume(request: Request, volume_name: str):
    backup = api_backup_volume(volume_name)
    return RedirectResponse(url="/backup-volume-tab", status_code=303)
