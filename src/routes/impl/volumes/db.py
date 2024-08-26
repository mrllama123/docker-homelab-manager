import os
from datetime import datetime

import pytz
from sqlmodel import Session, select

from src.models import Backups, BackUpStatus, SftpBackupSource, SftpBackupSourceCreate

TZ = os.environ.get("TZ", "UTC")


def db_create_sftp_backup_source(
    session: Session,
    backup_source: SftpBackupSourceCreate,
) -> SftpBackupSource:
    db_sftp_backup_source = SftpBackupSource.model_validate(backup_source)
    session.add(db_sftp_backup_source)
    session.commit()
    session.refresh(db_sftp_backup_source)
    return db_sftp_backup_source


def db_delete_sftp_backup_source(session: Session, id: str) -> None:
    backup_source = session.get(SftpBackupSource, id)
    session.delete(backup_source)
    session.commit()


def db_get_sftp_backup_source(session: Session, id: str) -> SftpBackupSource | None:
    return session.get(SftpBackupSource, id)


def db_list_sftp_backup_sources(session: Session) -> list[SftpBackupSource]:
    query = select(SftpBackupSource)
    return session.exec(query).all()


def db_create_backup(
    session: Session,
    volume_name: str,
    backup_name: str,
    schedule_id: str | None = None,
    status: BackUpStatus = BackUpStatus.Created,
    error_message: str | None = None,
) -> Backups:
    dt_now = datetime.now(tz=pytz.timezone(TZ))
    db_backup = Backups(
        volume_name=volume_name,
        backup_name=backup_name,
        schedule_id=schedule_id,
        created_at=dt_now.isoformat(),
        status=status,
        error_message=error_message,
    )
    session.add(db_backup)
    session.commit()
    session.refresh(db_backup)
    return db_backup
