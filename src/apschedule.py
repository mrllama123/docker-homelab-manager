import logging
import os

from apscheduler.job import Job
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src.docker import backup_volume, restore_volume
from src.models import BackupSchedule, ScheduleCrontab

logger = logging.getLogger(__name__)


APSCHEDULE_JOBSTORE_URL = os.environ.get(
    "APSCHEDULE_JOBSTORE_URL", "sqlite:///example.sqlite"
)
TZ = os.environ.get("TZ", "UTC")


def setup_scheduler() -> AsyncIOScheduler:
    jobstores = {"default": SQLAlchemyJobStore(url=APSCHEDULE_JOBSTORE_URL)}
    scheduler = AsyncIOScheduler(jobstores=jobstores, timezone=TZ)
    scheduler.start()
    return scheduler


def add_backup_job(
    schedule: AsyncIOScheduler,
    job_name: str,
    volume_name: str,
    crontab: ScheduleCrontab = None,
):
    if crontab:
        return schedule.add_job(
            func=backup_volume,
            trigger=CronTrigger(
                minute=crontab.minute,
                hour=crontab.hour,
                day=crontab.day,
                month=crontab.month,
                day_of_week=crontab.day_of_week,
            ),
            id=job_name,
            name=job_name,
            args=[volume_name],
            replace_existing=False,
        )

    return schedule.add_job(
        func=backup_volume,
        id=job_name,
        name=job_name,
        args=[volume_name],
        replace_existing=False,
        coalesce=True,
    )


def add_restore_job(
    schedule: AsyncIOScheduler,
    job_name: str,
    volume_name: str,
    backup_filename: str,
    crontab: ScheduleCrontab = None,
):
    if crontab:
        return schedule.add_job(
            func=restore_volume,
            trigger=CronTrigger(**crontab),
            id=job_name,
            name=job_name,
            args=[volume_name, backup_filename],
            replace_existing=False,
        )

    return schedule.add_job(
        func=restore_volume,
        id=job_name,
        name=job_name,
        args=[volume_name, backup_filename],
        replace_existing=False,
        coalesce=True,
    )


def get_backup_schedule(
    scheduler: AsyncIOScheduler, schedule_name: str
) -> BackupSchedule | None:
    job = scheduler.get_job(schedule_name)
    if job:
        return map_job_to_backup_schedule(job)

    return job


def list_backup_schedules(scheduler: AsyncIOScheduler) -> list[BackupSchedule]:
    return [map_job_to_backup_schedule(job) for job in scheduler.get_jobs()]


def delete_backup_schedule(scheduler: AsyncIOScheduler, schedule_name: str):
    return scheduler.remove_job(schedule_name)


def map_job_to_backup_schedule(job: Job):
    if isinstance(job.trigger, CronTrigger):
        logger.debug("felids: %s", job.trigger.fields)
        cron_fields = {field.name: str(field) for field in job.trigger.fields}
        logger.info("cron_fields: %s", cron_fields)
        return BackupSchedule(
            schedule_name=job.id,
            volume_name=job.args[0],
            crontab=ScheduleCrontab(
                minute=cron_fields["minute"],
                hour=cron_fields["hour"],
                day=cron_fields["day"],
                month=cron_fields["month"],
                day_of_week=cron_fields["day_of_week"],
            ),
        )

    return BackupSchedule(
        schedule_name=job.id,
        volume_name=job.args[0],
    )
