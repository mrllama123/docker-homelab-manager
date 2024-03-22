from typing import Optional

from pydantic import BaseModel
from sqlmodel import Field, SQLModel


class VolumeItem(BaseModel):
    name: str
    labels: dict[str, str]
    mountpoint: str
    options: dict[str, str]
    status: dict[str, str]
    createdAt: str


class CreateBackupResponse(BaseModel):
    backup_id: str
    volume_name: str


class RestoreVolumeResponse(BaseModel):
    restore_id: str
    volume_name: str


class RestoreVolume(BaseModel):
    volume_name: str
    backup_filename: str


class RestoreVolumeHtmlRequest(BaseModel):
    backup_id: str
    volume_name: str


class ScheduleCrontab(BaseModel):
    seconds: str = "*"
    minute: str = "*"
    hour: str = "*"
    day: str = "*"
    month: str = "*"
    day_of_week: str = "*"


class CreateBackupSchedule(BaseModel):
    schedule_name: str
    volume_name: str
    crontab: ScheduleCrontab


class BackupSchedule(BaseModel):
    schedule_id: str
    volume_name: str
    schedule_name: str | None = None
    crontab: ScheduleCrontab = None


# db models


class Backups(SQLModel, table=True):
    backup_id: Optional[str] = Field(default=None, primary_key=True)
    schedule_id: Optional[str] = Field(default=None)
    backup_name: Optional[str] = Field(default=None)
    volume_name: Optional[str] = Field(default=None)
    backup_filename: Optional[str] = Field(default=None)
    backup_path: Optional[str] = Field(default=None)
    successful: bool = True
    error_message: Optional[str] = Field(default=None)
    created_at: Optional[str] = Field(default=None)


class BackupFilenames(SQLModel, table=True):
    backup_filename: Optional[str] = Field(default=None, primary_key=True)
    backup_id: Optional[str] = Field(
        default=None,
        foreign_key="backups.backup_id",
    )


class RestoredBackups(SQLModel, table=True):
    restore_id: Optional[str] = Field(default=None, primary_key=True)
    restore_name: Optional[str] = Field(default=None)
    volume_name: Optional[str] = Field(default=None)
    backup_filename: Optional[str] = Field(default=None)
    created_at: Optional[str] = Field(default=None)
    successful: bool = True
    error_message: Optional[str] = Field(default=None)


class UnknownLoadingJobBase(SQLModel):
    progress: int = Field(default=0)


class UnknownLoadingJob(UnknownLoadingJobBase, table=True):
    id: int | None = Field(default=None, primary_key=True)



