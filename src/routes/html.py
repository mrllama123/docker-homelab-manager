from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session
from typing import Annotated

from src.db import get_session
from src.models import CreateBackupSchedule
from src.routes.impl.volumes import (
    api_backup_volume,
    api_backups,
    api_volumes,
    api_list_backup_schedules,
    api_create_backup_schedule,
)
import logging

router = APIRouter(tags=["html"])

templates = Jinja2Templates(directory="src/templates")

logger = logging.getLogger(__name__)


@router.get("/", description="home page", response_class=HTMLResponse)
def root(request: Request):
    return templates.TemplateResponse(request, "index.html")


@router.get("/volumes", description="volumes page", response_class=HTMLResponse)
async def volumes(request: Request):
    volumes = await api_volumes()
    return templates.TemplateResponse(request, "volume_rows.html", {"volumes": volumes})


@router.get(
    "/tabs/backup-volume", description="backup volumes tab", response_class=HTMLResponse
)
def backup_volume_tab(request: Request):
    return templates.TemplateResponse(request, "backup_volume_tab.html")


@router.post(
    "/volumes/backup/{volume_name}",
    description="create backup",
    response_class=HTMLResponse,
)
def backup_volume(request: Request, volume_name: str):
    try:
        result = api_backup_volume(volume_name)
        return templates.TemplateResponse(
            request,
            "notification.html",
            {"message": f"Backup created: {result.backup_id}", "swap_out_of_band": False},
        )
    except HTTPException as e:
        return templates.TemplateResponse(
            request, "notification.html", {"message": e.detail, "swap_out_of_band": False}
        )
    except Exception:
        raise


@router.get("/volumes/backups", description="backup row", response_class=HTMLResponse)
async def backups(request: Request, session: Session = Depends(get_session)):
    backups = await api_backups(session)
    return templates.TemplateResponse(request, "backup_rows.html", {"backups": backups})


@router.get(
    "/volumes/backup/schedules",
    description="backup schedules rows",
    response_class=HTMLResponse,
)
def backup_schedules(request: Request):
    schedules = api_list_backup_schedules()
    return templates.TemplateResponse(
        request, "backup_schedule_rows.html", {"schedules": schedules}
    )


@router.get(
    "/volumes/backup/schedule/{volume_name}",
    description="create backup schedule",
    response_class=HTMLResponse,
)
def create_backup_schedule_form(request: Request, volume_name: str):
    return templates.TemplateResponse(
        request, "create_backup_schedule.html", {"volume_name": volume_name}
    )


@router.post(
    "/volumes/backup/schedule/{volume_name}",
    description="create backup schedule",
    response_class=HTMLResponse,
)
async def create_backup_schedule(
    request: Request,
    volume_name: str,
    schedule_name: Annotated[str, Form()],
    seconds: Annotated[str, Form()],
    minutes: Annotated[str, Form()],
    hours: Annotated[str, Form()],
    days: Annotated[str, Form()],
    months: Annotated[str, Form()],
    days_of_week: Annotated[str, Form()],
):

    schedule = CreateBackupSchedule(
        schedule_name=schedule_name,
        volume_name=volume_name,
        crontab={
            "seconds": seconds,
            "minutes": minutes,
            "hours": hours,
            "days": days,
            "months": months,
            "days_of_week": days_of_week,
        },
    )

    await api_create_backup_schedule(schedule)
    return templates.TemplateResponse(
        request, "notification.html", {"message": "Backup schedule created", "swap_out_of_band": True}
    )
