import uuid
from enum import Enum
from typing import Optional, Self

from pydantic import BaseModel, model_validator
from sqlmodel import Field, SQLModel
from pydantic.types import Path

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


class SshKeyTypes(str, Enum):
    RSA = "rsa"
    ED25519 = "ed25519"
    ECDSA = "ecdsa"
    DSA = "dsa"


class SftpBackupSourceBase(SQLModel):
    name: str = Field(index=True, unique=True)
    hostname: str = Field(index=True, unique=True)
    port: int = Field(gt=0, lt=65536)
    username: str = Field()
    password: str | None = None
    ssh_key_type: SshKeyTypes | None = None
    ssh_key: str | None = None
    remote_path: str

    @model_validator(mode="after")
    def check_ssh_config_set(self) -> Self:
        if not self.password and not self.ssh_key:
            raise ValueError("either password or ssh key must be set")

        # ensure that ssh_key is set when ssh_key_type is set
        check_ssh_key_type_null = not self.ssh_key_type and self.ssh_key
        check_ssh_key_null = self.ssh_key_type and not self.ssh_key

        if check_ssh_key_null or check_ssh_key_type_null:
            raise ValueError(
                "if setting ssh key both ssh key and ssh key type need to be selected"
            )
        return self


class SftpBackupSourceCreate(SftpBackupSourceBase):
    pass


class SftpBackupSourcePublic(SftpBackupSourceBase):
    """
    model of what is displayed to the api
    """

    id: uuid.UUID


class SftpBackupSource(SftpBackupSourceBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
