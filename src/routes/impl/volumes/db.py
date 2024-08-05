from sqlmodel import Session

from src.models import SftpBackupSource, SftpBackupSourceCreate


def db_create_sftp_backup_source(
    session: Session, backup_source: SftpBackupSourceCreate
) -> SftpBackupSource:

    db_sftp_backup_source = SftpBackupSource.model_validate(backup_source)
    session.add(db_sftp_backup_source)
    session.commit()
    session.refresh(db_sftp_backup_source)
    return db_sftp_backup_source
