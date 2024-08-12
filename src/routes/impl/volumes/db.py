from sqlmodel import Session, select

from src.models import SftpBackupSource, SftpBackupSourceCreate


def db_create_sftp_backup_source(
    session: Session, backup_source: SftpBackupSourceCreate
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
