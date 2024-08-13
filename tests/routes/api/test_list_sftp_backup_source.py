from src.models import SftpBackupSource, SshKeyTypes


def test_list_sftp_backup_sources(client, session):
    sftp_sources = [
        SftpBackupSource(
            name="test_sftp_source_1",
            hostname="host1.example.com",
            port=22,
            username="test_username_1",
            ssh_key="test_private_key_1",
            ssh_key_type=SshKeyTypes.RSA,
        ),
        SftpBackupSource(
            name="test_sftp_source_2",
            hostname="host2.example.com",
            port=22,
            username="test_username_2",
            ssh_key="test_private_key_2",
            ssh_key_type=SshKeyTypes.ED25519,
        ),
        SftpBackupSource(
            name="test_sftp_source_3",
            hostname="host3.example.com",
            port=22,
            username="test_username_3",
            ssh_key="test_private_key_3",
            ssh_key_type=SshKeyTypes.RSA,
        ),
    ]
    session.add_all(sftp_sources)
    session.commit()

    # Act
    response = client.get("/api/volumes/backups/sources")
    assert response.status_code == 200
    data = response.json()

    for data in data:
        assert data["name"] in [
            "test_sftp_source_1",
            "test_sftp_source_2",
            "test_sftp_source_3",
        ]
        assert data["hostname"] in [
            "host1.example.com",
            "host2.example.com",
            "host3.example.com",
        ]
        assert data["port"] == 22
        assert data["username"] in [
            "test_username_1",
            "test_username_2",
            "test_username_3",
        ]
        assert data["ssh_key_type"] in [SshKeyTypes.RSA, SshKeyTypes.ED25519]


def test_list_sftp_backup_source_empty(client, session):
    response = client.get("/api/volumes/backups/sources")
    assert response.status_code == 200
    data = response.json()
    assert data == []
