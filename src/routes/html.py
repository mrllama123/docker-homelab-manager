import json
import logging
import uuid
from typing import Annotated

from apscheduler.jobstores.base import ConflictingIdError, JobLookupError
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from src.apschedule import schedule
from src.db import get_session
from src.docker import get_volume, is_volume_attached
from src.models import CreateBackupSchedule, RestoreVolumeHtmlRequest
from src.routes.impl.volumes.backups import db_list_backups
from src.routes.impl.volumes.resored_backups import db_list_restored_backups
from src.routes.impl.volumes.volumes import list_volumes

router = APIRouter(tags=["html"])

templates = Jinja2Templates(directory="src/templates")

logger = logging.getLogger(__name__)


@router.get("/", description="home page", response_class=HTMLResponse)
def root(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "index.html",
    )


@router.get("/volumes", description="volumes page", response_class=HTMLResponse)
def volumes(request: Request) -> HTMLResponse:
    volumes = list_volumes()
    return templates.TemplateResponse(
        request,
        "tabs/backup_volumes/components/volume_rows.html",
        {"volumes": volumes},
    )


@router.get("/tabs/restore-volumes", description="restore volumes tab")
def restore_volumes_tab(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "tabs/restore_volumes/restore_volume_tab.html",
    )


@router.get("/tabs/backup-volumes", description="backup volumes tab")
def backup_volumes_tab(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "tabs/backup_volumes/backup_volume_tab.html",
    )


@router.post(
    "/volumes/backup/{volume_name}",
    description="create backup",
    response_class=HTMLResponse,
)
def backup_volume(request: Request, volume_name: str) -> HTMLResponse:

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

    job = schedule.add_backup_job(
        f"backup-{volume_name}-{uuid.uuid4()!s}",
        volume_name,
    )
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
def backups(request: Request, session: Session = Depends(get_session)) -> HTMLResponse:
    backups = (
        db_list_backups(session, successful=True)
        if request.headers.get("HX-Target") == "success-backup-rows"
        else db_list_backups(session)
    )
    path = (
        "tabs/restore_volumes/components/backup_rows.html"
        if request.headers.get("HX-Target") == "success-backup-rows"
        else "tabs/backup_volumes/components/backup_rows.html"
    )
    return templates.TemplateResponse(request, path, {"backups": backups})


@router.get(
    "/volumes/backup/schedules",
    description="backup schedules rows",
    response_class=HTMLResponse,
)
def backup_schedules(request: Request) -> HTMLResponse:
    schedules = schedule.list_backup_schedules()
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
def create_backup_schedule_form(request: Request, volume_name: str) -> HTMLResponse:
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
) -> HTMLResponse:

    new_schedule = CreateBackupSchedule(
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

    logger.info("create_backup_schedule: %s", new_schedule)

    if not get_volume(new_schedule.volume_name):
        return templates.TemplateResponse(
            request,
            "notification.html",
            {"message": "Volume {schedule.volume_name} does not exist"},
        )

    try:
        job = schedule.add_backup_job(
            new_schedule.schedule_name,
            new_schedule.volume_name,
            new_schedule.crontab,
            is_schedule=True,
        )
        logger.info("create_backup_schedule: job_id: %s", job.id)

        return HTMLResponse("", headers={"HX-Trigger": "reload-backup-schedule-rows"})

    except ConflictingIdError:
        return templates.TemplateResponse(
            request,
            "notification.html",
            {"message": f"Schedule job {new_schedule.schedule_name} already exists"},
        )
    except Exception:
        raise


@router.delete(
    "/volumes/backup/schedules",
    description="delete backup schedule",
    response_class=HTMLResponse,
)
def delete_backup_schedule(
    request: Request,
    schedules: Annotated[list[str], Form()],
) -> HTMLResponse:
    try:
        for id in schedules:
            logger.info("Removing schedule %s", id)
            schedule.delete_backup_schedule(id)
        schedules = schedule.list_backup_schedules()
        return templates.TemplateResponse(
            request,
            "tabs/backup_volumes/components/backup_schedule_rows.html",
            {"schedules": schedules},
        )
    except JobLookupError as e:
        return templates.TemplateResponse(
            request,
            "notification.html",
            {"message": str(e)},
        )
    except Exception:
        raise


@router.post(
    "/volumes/restore",
    description="restore volumes",
    response_class=HTMLResponse,
)
def restore_volumes(
    request: Request,
    volumes: Annotated[list[str], Form()],
    session: Session = Depends(get_session),
) -> HTMLResponse:
    logger.info("restoring volumes: %s", volumes)
    volumes = [json.loads(v) for v in volumes]
    volumes: list[RestoreVolumeHtmlRequest] = [
        RestoreVolumeHtmlRequest.model_validate(v) for v in volumes
    ]

    backups = db_list_backups(session, backup_ids=[v.backup_id for v in volumes])

    if not backups:
        return templates.TemplateResponse(
            request,
            "notification.html",
            {"message": "No backups found"},
        )

    # TODO handle multiple data sources of backups in future

    restore_volume_by_backup_id = {v.backup_id: v.volume_name for v in volumes}

    group_backup_by_volume_name = {
        restore_volume_by_backup_id[backup.backup_id]: backup for backup in backups
    }

    for volume_name, backup in group_backup_by_volume_name.items():
        logger.info("restoring volume: %s", volume_name)
        job = schedule.add_restore_job(
            f"backup-{volume_name}-{uuid.uuid4()!s}",
            volume_name,
            backup.backup_filename,
        )

        logger.info(
            "restore %s started task id: %s",
            volume_name,
            job.id,
            extra={"task_id": job.id},
        )
    return HTMLResponse("")


@router.get(
    "/volumes/restores",
    description="list restore backups",
    response_class=HTMLResponse,
)
def restores(request: Request, session: Session = Depends(get_session)) -> HTMLResponse:
    restores = db_list_restored_backups(session)
    return templates.TemplateResponse(
        request,
        "tabs/restore_volumes/components/restore_rows.html",
        {"restored_backups": restores},
    )
