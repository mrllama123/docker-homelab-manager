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


class ScheduleContab(BaseModel):
    minute: str
    hour: str
    day: str
    month: str
    day_of_week: str
    month_of_year: str


class BackScheduleInput(BaseModel):
    volume_name: str
    schedule_name: str
    crontab: ScheduleContab
    periodic: str

    @model_validator(mode="after")
    def check_fields(self):
        if self.crontab and self.periodic:
            raise ValidationError('Only one of "crontab" or "periodic" must be provided')
        return self
