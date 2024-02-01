import os

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src.docker import backup_volume, restore_volume
from src.models import BackupSchedule, ScheduleCrontab
from apscheduler.job import Job


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


def map_job_to_backup_schedule(job: Job):
    if isinstance(job.trigger, CronTrigger):
        return BackupSchedule(
            job_id=job.id,
            volume_name=job.args[0],
            crontab=ScheduleCrontab(
                minute=job.trigger.minute,
                hour=job.trigger.hour,
                day=job.trigger.day,
                month=job.trigger.month,
                day_of_week=job.trigger.day_of_week,
            ),
        )

    if isinstance(job.trigger, IntervalTrigger):

        period_info = {
            "period": job.trigger.interval,
            "every": job.trigger.interval_length,
        }

        return BackupSchedule(
            job_id=job.id,
            volume_name=job.args[0],
            periodic=SchedulePeriodic(**period_info),
        )

    return BackupSchedule(
        job_id=job.id,
        volume_name=job.args[0],
    )
