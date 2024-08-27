import logging
import os
import uuid

from apscheduler.job import Job
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src.apschedule.tasks import task_create_backup, task_restore_backup
from src.models import BackupSchedule, ScheduleCrontab

logger = logging.getLogger(__name__)

APSCHEDULE_JOBSTORE_URL = os.environ.get(
    "APSCHEDULE_JOBSTORE_URL",
    "sqlite:///example.sqlite",
)
TZ = os.environ.get("TZ", "UTC")

SCHEDULER: AsyncIOScheduler | None = None


def setup_scheduler() -> AsyncIOScheduler:
    global SCHEDULER  # noqa: PLW0603
    jobstores = {"default": SQLAlchemyJobStore(url=APSCHEDULE_JOBSTORE_URL)}
    SCHEDULER = AsyncIOScheduler(jobstores=jobstores, timezone=TZ)
    SCHEDULER.start()
    return SCHEDULER


def add_backup_job(
    job_name: str,
    volume_name: str,
    crontab: ScheduleCrontab = None,
    is_schedule: bool = False,
):
    job_id = str(uuid.uuid4())

    kwargs = {"is_schedule": True, "job_name": job_name} if is_schedule else {"job_name": job_name}

    if crontab:
        return SCHEDULER.add_job(
            func=task_create_backup,
            trigger=CronTrigger(
                minute=crontab.minute,
                hour=crontab.hour,
                day=crontab.day,
                month=crontab.month,
                day_of_week=crontab.day_of_week,
            ),
            id=job_id,
            name=job_name,
            args=[volume_name, job_id],
            kwargs=kwargs,
            replace_existing=False,
        )

    return SCHEDULER.add_job(
        func=task_create_backup,
        id=job_id,
        name=job_name,
        args=[volume_name, job_id],
        kwargs=kwargs,
        replace_existing=False,
        coalesce=True,
    )


def add_restore_job(
    job_name: str,
    volume_name: str,
    backup_filename: str,
    crontab: ScheduleCrontab = None,
):
    job_id = str(uuid.uuid4())
    if crontab:
        return SCHEDULER.add_job(
            func=task_restore_backup,
            trigger=CronTrigger(**crontab),
            id=job_id,
            name=job_name,
            args=[volume_name, backup_filename, job_id, job_name],
            replace_existing=False,
        )

    return SCHEDULER.add_job(
        func=task_restore_backup,
        id=job_id,
        name=job_name,
        args=[volume_name, backup_filename, job_id, job_name],
        replace_existing=False,
        coalesce=True,
    )


def get_backup_schedule(schedule_name: str) -> BackupSchedule | None:
    job = SCHEDULER.get_job(schedule_name)
    if job:
        return map_job_to_backup_schedule(job)

    return job


def list_backup_schedules() -> list[BackupSchedule]:
    return [map_job_to_backup_schedule(job) for job in SCHEDULER.get_jobs()]


def delete_backup_schedule(schedule_id: str):
    return SCHEDULER.remove_job(schedule_id)


def map_job_to_backup_schedule(job: Job):
    if isinstance(job.trigger, CronTrigger):
        logger.debug("felids: %s", job.trigger.fields)
        cron_fields = {field.name: str(field) for field in job.trigger.fields}
        logger.info("cron_fields: %s", cron_fields)
        return BackupSchedule(
            schedule_id=job.id,
            volume_name=job.args[0],
            schedule_name=job.name,
            crontab=ScheduleCrontab(
                minute=cron_fields["minute"],
                hour=cron_fields["hour"],
                day=cron_fields["day"],
                month=cron_fields["month"],
                day_of_week=cron_fields["day_of_week"],
            ),
        )

    return BackupSchedule(
        schedule_id=job.id,
        schedule_name=job.name,
        volume_name=job.args[0],
    )
