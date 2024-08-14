import uuid

from sqlmodel import select

from src.models import SftpBackupSource, SshKeyTypes


def test_delete_sftp_backup_source(session, client):
    sftp_source = SftpBackupSource(
        name="Test SFTP Source",
        hostname="sftp.example.com",
        port=22,
        username="testuser",
        remote_path="/usr/nas/share",
        ssh_key="testprivatekey",
        ssh_key_type=SshKeyTypes.RSA,
    )

    session.add(sftp_source)
    session.commit()

    id = str(sftp_source.id)
    response = client.delete(f"/api/volumes/backups/source/{id}")
    assert response.status_code == 200
    assert response.text == f'"Backup source {id} deleted"'

    statement = select(SftpBackupSource).where(SftpBackupSource.id == sftp_source.id)
    result = session.exec(statement)
    assert result.first() is None


def test_delete_sftp_backup_source_not_found(client):
    id = str(uuid.uuid4())
    response = client.delete(f"/api/volumes/backups/source/{id}")
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == f"Backup source {id} does not exist"
