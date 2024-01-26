from sqlmodel import Session, select
from sqlalchemy_celery_beat.models import (
    IntervalSchedule,
    CrontabSchedule,
    PeriodicTask,
)
from src.models import BackupScheduleInput
import json


def get_schedule(
    schedule_info: BackupScheduleInput, session: Session
) -> IntervalSchedule | CrontabSchedule:
    if schedule_info.crontab:
        schedule = session.exec(
            select(CrontabSchedule).where(
                CrontabSchedule.day_of_month == schedule_info.crontab.day
                and CrontabSchedule.day_of_week == schedule_info.crontab.day_of_week
                and CrontabSchedule.hour == schedule_info.crontab.hour
                and CrontabSchedule.minute == schedule_info.crontab.minute
                and CrontabSchedule.month_of_year == schedule_info.crontab.month
                and CrontabSchedule.timezone == schedule_info.timezone
            )
        ).first()
        if not schedule:
            schedule = CrontabSchedule(
                day_of_month=schedule_info.crontab.day,
                day_of_week=schedule_info.crontab.day_of_week,
                hour=schedule_info.crontab.hour,
                minute=schedule_info.crontab.minute,
                month_of_year=schedule_info.crontab.month,
                timezone=schedule_info.timezone,
            )
            session.add(schedule)
            session.commit()
    else:
        schedule = session.exec(
            select(IntervalSchedule).where(
                IntervalSchedule.every == schedule_info.periodic.every
                and IntervalSchedule.period == schedule_info.periodic.period
            )
        ).first()
        if not schedule:
            schedule = IntervalSchedule(
                every=schedule_info.periodic.every,
                period=schedule_info.periodic.period,
            )
            session.add(schedule)
            session.commit()
    return schedule


def get_periodic_task(
    schedule_info: BackupScheduleInput, session: Session
) -> PeriodicTask | None:
    task = session.exec(
        select(PeriodicTask).where(PeriodicTask.name == schedule_info.schedule_name)
    ).first()

    return task


def create_periodic_task(schedule_info, session, schedule):
    periodic_task = PeriodicTask(
        name=schedule_info.schedule_name,
        task="src.celery.create_volume_backup",
        interval=schedule,
        args=json.dumps([schedule_info.volume_name]),
    )
    session.add(periodic_task)
    session.commit()
