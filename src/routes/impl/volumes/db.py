from sqlmodel import Session

from src.routes.impl.crypto import hash_string
from src.models import SftpBackupSource, SftpBackupSourceCreate


def db_create_sftp_backup_source(
    session: Session, backup_source: SftpBackupSourceCreate
) -> SftpBackupSource:
    
    # dont think hashed ssh key or password will work as you need to know the password/key to decrypt it
    # ssh_auth_hashed = (
    #     {"password": hash_string(backup_source.password)}
    #     if backup_source.password
    #     else {"ssh_key": hash_string(backup_source.ssh_key)}
    # )

    # db_sftp_backup_source = SftpBackupSource.model_validate(backup_source, update=ssh_auth_hashed)
    db_sftp_backup_source = SftpBackupSource.model_validate(backup_source)
    session.add(db_sftp_backup_source)
    session.commit()
    session.refresh(db_sftp_backup_source)
    return db_sftp_backup_source
