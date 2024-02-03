from typing import Any, Optional

from pydantic import BaseModel
from sqlmodel import Field, SQLModel


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


class BackupVolume(BaseModel):
    volume_name: str
    backup_filename: str


class ScheduleCrontab(BaseModel):
    minute: str = "*"
    hour: str = "*"
    day: str = "*"
    month: str = "*"
    day_of_week: str = "*"


class BackupSchedule(BaseModel):
    schedule_name: str
    volume_name: str
    crontab: ScheduleCrontab = None


class Backups(SQLModel, table=True):
    backup_name: Optional[str] = Field(default=None, primary_key=True)
    backup_path: Optional[str] = Field(default=None)
    backup_created: str
    backup_path: str
    volume_name: str
    restored: Optional[bool] = Field(default=False)
    restored_date: Optional[str] = Field(default=None)
