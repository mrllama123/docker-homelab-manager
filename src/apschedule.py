from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
import os
from src.docker import backup_volume, restore_volume

from src.models import SchedulePeriod, ScheduleCrontab, SchedulePeriodic

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
    interval: SchedulePeriodic = None,
):
    if crontab:
        return schedule.add_job(
            func=backup_volume,
            trigger=CronTrigger(**crontab),
            id=job_name,
            name=job_name,
            args=[volume_name],
            replace_existing=False,
        )

    if interval:
        return schedule.add_job(
            func=backup_volume,
            trigger=IntervalTrigger(**{interval.period: interval.every}),
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
    interval: SchedulePeriodic = None,
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

    if interval:
        return schedule.add_job(
            func=restore_volume,
            trigger=IntervalTrigger(**{interval.period: interval.every}),
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

