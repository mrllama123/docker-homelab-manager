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
    schedule_id: Optional[str] = Field(
        default=None, foreign_key="scheduledbackups.schedule_id"
    )
    volume_name: Optional[str] = Field(
        default=None, foreign_key="backupvolumes.volume_name"
    )
    backup_filename: Optional[str] = Field(default=None)
    backup_path: Optional[str] = Field(default=None)
    backup_created: str


class BackupFilenames(SQLModel, table=True):
    backup_filename: Optional[str] = Field(default=None, primary_key=True)
    backup_id: Optional[str] = Field(
        default=None,
        foreign_key="backups.backup_id",
    )


class ScheduledBackups(SQLModel, table=True):
    backup_id: Optional[str] = Field(
        default=None, foreign_key="backups.backup_id", primary_key=True
    )
    schedule_id: Optional[str] = Field(default=None)
    schedule_name: str


class BackupVolumes(SQLModel, table=True):
    backup_id: Optional[str] = Field(
        default=None, primary_key=True, foreign_key="backups.backup_id"
    )
    volume_name: str


class ErrorBackups(SQLModel, table=True):
    backup_id: Optional[str] = Field(default=None, primary_key=True)
    error_message: Optional[str] = Field(default=None)


class RestoredBackups(SQLModel, table=True):
    restore_id: Optional[str] = Field(default=None, primary_key=True)
    volume_name: Optional[str] = Field(
        default=None, foreign_key="restorebackupvolumes.volume_name"
    )
    backup_filename: Optional[str] = Field(
        default=None, foreign_key="backupfilenames.backup_filename"
    )
    restored_date: Optional[str] = Field(default=None)


class ErrorRestoredBackups(SQLModel, table=True):
    restore_id: Optional[str] = Field(default=None, primary_key=True)
    error_message: Optional[str] = Field(default=None)


class RestoreBackupVolumes(SQLModel, table=True):
    restore_id: Optional[str] = Field(
        default=None, primary_key=True, foreign_key="restoredbackups.restore_id"
    )
    volume_name: str
