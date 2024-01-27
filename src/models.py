from enum import Enum
from typing import Any

from pydantic import BaseModel, ValidationError, model_validator


class VolumeItem(BaseModel):
    name: str
    labels: dict[str, str]
    mountpoint: str
    options: dict[str, str]
    status: dict[str, str]
    createdAt: str


class BackupVolumeResponse(BaseModel):
    message: str
    task_id: str


class BackupStatusResponse(BaseModel):
    status: str
    task_id: str
    result: Any


class BackupVolumeRestore(BaseModel):
    volume_name: str
    backup_filename: str


class ScheduleCrontab(BaseModel):
    minute: str
    hour: str
    day: str
    month: str
    day_of_week: str
    month_of_year: str


class SchedulePeriod(str, Enum):
    DAYS = "days"
    HOURS = "hours"
    MINUTES = "minutes"
    SECONDS = "seconds"
    MICROSECONDS = "microseconds"


class SchedulePeriodic(BaseModel):
    every: int
    period: SchedulePeriod


class BackupScheduleInput(BaseModel):
    volume_name: str
    schedule_name: str
    crontab: ScheduleCrontab | None = None
    periodic: SchedulePeriodic | None = None
    timezone: str = "UTC"

    @model_validator(mode="after")
    def check_fields(self):
        if not self.crontab and not self.periodic:
            raise ValidationError('crontab" or "periodic" must be provided')
        if self.crontab and self.periodic:
            raise ValidationError(
                'Only one of "crontab" or "periodic" must be provided'
            )
        return self


class BackupScheduleResponse(BaseModel):
    pass
