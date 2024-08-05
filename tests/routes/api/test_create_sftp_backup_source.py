from sqlmodel import select
from src.models import SftpBackupSourceCreate, SftpBackupSource


def test_create_sftp_backup_source_password(client, session):

    response = client.post(
        "/api/volumes/backups/source",
        json=SftpBackupSourceCreate(
            name="test-sftp",
            hostname="127.0.0.1",
            port=22,
            username="root",
            password="verysecretpassword",
        ).model_dump(),
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data.get("name") == "test-sftp"
    assert response_data.get("hostname") == "127.0.0.1"
    assert response_data.get("port") == 22
    assert response_data.get("username") == "root"
    assert response_data.get("id")
    assert response_data.get("password") == "verysecretpassword"
    assert len(list(session.exec(select(SftpBackupSource)).all())) == 1
