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
    backup_id: str


class RestoreVolumeResponse(BaseModel):
    message: str
    restore_id: str


class BackupStatusResponse(BaseModel):
    status: str
    backup_id: str
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
    success: Optional[bool] = Field(default=None)
    errorMessage: Optional[str] = Field(default=None)


class BackupFilenames(SQLModel, table=True):
    backup_filename: Optional[str] = Field(default=None, primary_key=True)
    backup_id: Optional[str] = Field(
        default=None,
        foreign_key="backups.backup_id",
    )


class RestoredBackups(SQLModel, table=True):
    restore_id: Optional[str] = Field(default=None, primary_key=True)
    volume_name: Optional[str] = Field(
        default=None, foreign_key="restorebackupvolumes.volume_name"
    )
    backup_filename: Optional[str] = Field(
        default=None, foreign_key="backupfilenames.backup_filename"
    )
    restored_date: Optional[str] = Field(default=None)
    success: Optional[bool] = Field(default=None)
    errorMessage: Optional[str] = Field(default=None)


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


class RestoreBackupVolumes(SQLModel, table=True):
    restore_id: Optional[str] = Field(
        default=None, primary_key=True, foreign_key="restoredbackups.restore_id"
    )
    volume_name: str


# class Backups(SQLModel, table=True):
#     backup_id: Optional[str] = Field(default=None, primary_key=True)
#     backup_file_name: Optional[str] = Field(default=None, index=True)
#     backup_path: Optional[str] = Field(default=None)
#     backup_created: str
#     backup_path: str
#     volume_name: str
#     success: Optional[bool] = Field(default=None)
#     errorMessage: Optional[str] = Field(default=None)


# class RestoredBackups(SQLModel, table=True):
#     restore_id: Optional[str] = Field(default=None, primary_key=True)
#     backup_file_name: Optional[str] = Field(
#         default=None, index=True, foreign_key="backups.backup_file_name"
#     )
#     backup_file_name_schedule: Optional[str] = Field(
#         default=None, index=True, foreign_key="schedulebackups.backup_file_name"
#     )
#     volume_name: str
#     restored_date: Optional[str] = Field(default=None)
#     success: Optional[bool] = Field(default=None)
#     errorMessage: Optional[str] = Field(default=None)


# class ScheduleBackups(SQLModel, table=True):
#     schedule_id: Optional[str] = Field(default=None, primary_key=True)
#     backup_file_name: Optional[str] = Field(default=None, primary_key=True)
#     backup_created: str
#     volume_name: str
#     success: Optional[bool] = Field(default=None)
#     errorMessage: Optional[str] = Field(default=None)
