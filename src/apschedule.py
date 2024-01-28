from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
import os
from src.docker import backup_volume

from src.models import SchedulePeriod, ScheduleCrontab

APSCHEDULE_JOBSTORE_URL = os.environ.get(
    "APSCHEDULE_JOBSTORE_URL", "sqlite:///example.sqlite"
)
TZ = os.environ.get("TZ", "UTC")


def setup_scheduler() -> AsyncIOScheduler:
    jobstores = {"default": SQLAlchemyJobStore(url=APSCHEDULE_JOBSTORE_URL)}
    scheduler = AsyncIOScheduler(jobstores=jobstores, timezone=TZ)
    scheduler.start()
    return scheduler


def add_backup_interval_job(
    schedule: AsyncIOScheduler,
    job_name: str,
    volume_name: str,
    interval: int,
    period: SchedulePeriod,
):
    trigger = IntervalTrigger(**{period: interval})
    return schedule.add_job(
        func=backup_volume,
        trigger=trigger,
        id=job_name,
        name=job_name,
        args=[volume_name],
        replace_existing=False,
    )


def add_backup_crontab_job(
    schedule: AsyncIOScheduler,
    job_name: str,
    volume_name: str,
    crontab: ScheduleCrontab,
):
    trigger = CronTrigger(**crontab)
    return schedule.add_job(
        func=backup_volume,
        trigger=trigger,
        id=job_name,
        name=job_name,
        args=[volume_name],
        replace_existing=False,
    )
