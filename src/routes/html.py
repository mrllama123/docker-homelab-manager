import logging
import uuid
from typing import Annotated

from apscheduler.jobstores.base import JobLookupError
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from src.apschedule.schedule import add_backup_job
from src.db import get_session
from src.docker import get_volume, is_volume_attached
from src.models import CreateBackupSchedule
from src.routes.impl.funcs import (
    api_create_backup_schedule,
    api_list_backup_schedules,
    api_remove_backup_schedules,
)
from src.routes.impl.volumes.backups import db_list_backups
from src.routes.impl.volumes.volumes import list_volumes

router = APIRouter(tags=["html"])

templates = Jinja2Templates(directory="src/templates")

logger = logging.getLogger(__name__)


@router.get("/", description="home page", response_class=HTMLResponse)
def root(request: Request):
    return templates.TemplateResponse(request, "index.html")


@router.get("/volumes", description="volumes page", response_class=HTMLResponse)
def volumes(request: Request):
    volumes = list_volumes()
    return templates.TemplateResponse(
        request, "tabs/backup_volumes/components/volume_rows.html", {"volumes": volumes}
    )


@router.get(
    "/tabs/backup-volume", description="backup volumes tab", response_class=HTMLResponse
)
def backup_volume_tab(request: Request):
    return templates.TemplateResponse(
        request, "tabs/backup_volumes/backup_volume_tab.html"
    )


@router.post(
    "/volumes/backup/{volume_name}",
    description="create backup",
    response_class=HTMLResponse,
)
def backup_volume(request: Request, volume_name: str):

    logger.info("backing up volume: %s", volume_name)
    if not get_volume(volume_name):
        return templates.TemplateResponse(
            request,
            "notification.html",
            {
                "message": f"Volume {volume_name} does not exist",
                "swap_out_of_band": False,
            },
        )
    if not is_volume_attached(volume_name):
        return templates.TemplateResponse(
            request,
            "notification.html",
            {
                "message": f"Volume {volume_name} is attached to a container",
                "swap_out_of_band": False,
            },
        )

    job = add_backup_job(f"backup-{volume_name}-{str(uuid.uuid4())}", volume_name)
    logger.info(
        "backup %s started task id: %s",
        volume_name,
        job.id,
        extra={"task_id": job.id},
    )
    return templates.TemplateResponse(
        request,
        "notification.html",
        {
            "message": f"Backup created: {job.id}",
            "swap_out_of_band": False,
        },
    )


@router.get("/volumes/backups", description="backup row", response_class=HTMLResponse)
def backups(request: Request, session: Session = Depends(get_session)):
    backups = db_list_backups(session)
    return templates.TemplateResponse(
        request, "tabs/backup_volumes/components/backup_rows.html", {"backups": backups}
    )


@router.get(
    "/volumes/backup/schedules",
    description="backup schedules rows",
    response_class=HTMLResponse,
)
def backup_schedules(request: Request):
    schedules = api_list_backup_schedules()
    return templates.TemplateResponse(
        request,
        "tabs/backup_volumes/components/backup_schedule_rows.html",
        {"schedules": schedules},
    )


@router.get(
    "/volumes/backup/schedule/{volume_name}",
    description="create backup schedule",
    response_class=HTMLResponse,
)
def create_backup_schedule_form(request: Request, volume_name: str):
    if request.headers.get("HX-Target") == "create-schedule-window":
        return ""
    return templates.TemplateResponse(
        request,
        "tabs/backup_volumes/components/create_backup_schedule.html",
        {"volume_name": volume_name},
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
    second: Annotated[str, Form()],
    minute: Annotated[str, Form()],
    hour: Annotated[str, Form()],
    day: Annotated[str, Form()],
    month: Annotated[str, Form()],
    day_of_week: Annotated[str, Form()],
):

    schedule = CreateBackupSchedule(
        schedule_name=schedule_name,
        volume_name=volume_name,
        crontab={
            "second": second,
            "minute": minute,
            "hour": hour,
            "day": day,
            "month": month,
            "day_of_week": day_of_week,
        },
    )

    logger.info(f"create_backup_schedule: {schedule}")
    try:
        await api_create_backup_schedule(schedule)

        return HTMLResponse("", headers={"HX-Trigger": "reload-backup-schedule-rows"})

    except HTTPException as e:
        return templates.TemplateResponse(
            request,
            "notification.html",
            {"message": e.detail},
        )
    except Exception:
        raise


@router.delete(
    "/volumes/backup/schedules",
    description="delete backup schedule",
    response_class=HTMLResponse,
)
def delete_backup_schedule(request: Request, schedules: Annotated[list[str], Form()]):
    try:
        api_remove_backup_schedules(schedules)
        schedules = api_list_backup_schedules()
        return templates.TemplateResponse(
            request,
            "tabs/backup_volumes/components/backup_schedule_rows.html",
            {"schedules": schedules},
        )
    except JobLookupError as e:
        return templates.TemplateResponse(
            request, "notification.html", {"message": str(e)}
        )
    except Exception:
        raise
