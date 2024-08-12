import uuid
from sqlmodel import select
from src.models import SftpBackupSource, SshKeyTypes


def test_get_sftp_backup_source(session, client):
    # Create a test SFTP backup source
    sftp_source = SftpBackupSource(
        name="Test SFTP Source",
        hostname="sftp.example.com",
        port=22,
        username="testuser",
        ssh_key="testprivatekey",
        ssh_key_type=SshKeyTypes.RSA,
    )
    session.add(sftp_source)
    session.commit()
    # Test getting the SFTP backup source
    response = client.get(f"/api/volumes/backups/source/{str(sftp_source.id)}")
    assert response.status_code == 200
    data = response.json()
    assert sftp_source.model_dump(mode="json") == data


def test_get_sftp_backup_source_not_found(client):
    # Test getting a non-existent SFTP backup source
    id = str(uuid.uuid4())
    response = client.get(f"/api/volumes/backups/source/{id}")
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == f"Backup source {id} does not exist"
