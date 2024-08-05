from sqlmodel import select
from src.models import SftpBackupSourceCreate, SftpBackupSource, SshKeyTypes


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

def test_create_sftp_backup_source_ssh_key(client, session):
    response = client.post(
        "/api/volumes/backups/source",
        json=SftpBackupSourceCreate(
            name="test-sftp",
            hostname="127.0.0.1",
            port=22,
            username="root",
            ssh_key_type=SshKeyTypes.RSA,
            ssh_key="-----BEGIN RSA PRIVATE KEY-----\nMIIEogIBAAKCAQEA6NF8iallvQVp22WDkTkyrtvPruB2uZjYGT1+XWFYe9z\nRUtxr0Yl/e/H+B33IqU4ZinVTnQx2Kb+M3AX4+sO7m484zTbo7AAACTk+EGeCIb5O\nunaf6h8mJPIy/u8=\n-----END RSA PRIVATE KEY-----\n",
        ).model_dump(),
    )
    assert response.status_code == 200
    response_data = response.json()
    assert response_data.get("name") == "test-sftp"
    assert response_data.get("hostname") == "127.0.0.1"
    assert response_data.get("port") == 22
    assert response_data.get("username") == "root"
    assert response_data.get("ssh_key_type") == SshKeyTypes.RSA
    assert response_data.get("ssh_key") == "-----BEGIN RSA PRIVATE KEY-----\nMIIEogIBAAKCAQEA6NF8iallvQVp22WDkTkyrtvPruB2uZjYGT1+XWFYe9z\nRUtxr0Yl/e/H+B33IqU4ZinVTnQx2Kb+M3AX4+sO7m484zTbo7AAACTk+EGeCIb5O\nunaf6h8mJPIy/u8=\n-----END RSA PRIVATE KEY-----\n"
    assert response_data.get("id")
    assert len(list(session.exec(select(SftpBackupSource)).all())) == 1

